import time
from itertools import chain
from typing import Any, Callable, Generator, Iterable

import yaml
from core.models import DataSource
from dcim.models import Device
from django.db.models import Prefetch, QuerySet
from django.utils.translation import gettext as __
from extras.choices import ObjectChangeActionChoices
from extras.models import Tag
from extras.scripts import BooleanVar, MultiObjectVar, ObjectVar

import validity
from validity.choices import ExplanationVerbosityChoices
from validity.compliance.exceptions import EvalError, SerializationError
from validity.models import (
    ComplianceReport,
    ComplianceSelector,
    ComplianceTest,
    ComplianceTestResult,
    NameSet,
    VDataSource,
    VDevice,
)
from validity.netbox_changes import enqueue_object, events_queue
from validity.utils.misc import datasource_sync, null_request
from .script_data import RunTestsScriptData, ScriptDataMixin
from .variables import VerbosityVar


class RunTestsScript(ScriptDataMixin[RunTestsScriptData]):
    _sleep_between_tests = validity.settings.sleep_between_tests
    _result_batch_size = validity.settings.result_batch_size

    sync_datasources = BooleanVar(
        required=False,
        default=False,
        label=__("Sync Data Sources"),
        description=__("Sync all referenced Data Sources"),
    )
    make_report = BooleanVar(default=True, label=__("Make Compliance Report"))
    selectors = MultiObjectVar(
        model=ComplianceSelector,
        required=False,
        label=__("Specific Selectors"),
        description=__("Run the tests only for specific selectors"),
    )
    devices = MultiObjectVar(
        model=Device,
        required=False,
        label=__("Specific Devices"),
        description=__("Run the tests only for specific devices"),
    )
    test_tags = MultiObjectVar(
        model=Tag,
        required=False,
        label=__("Specific Test Tags"),
        description=__("Run the tests which contain specific tags only"),
    )
    explanation_verbosity = VerbosityVar(
        choices=ExplanationVerbosityChoices.choices,
        default=ExplanationVerbosityChoices.maximum,
        label=__("Explanation Verbosity Level"),
        required=False,
    )
    override_datasource = ObjectVar(
        model=DataSource,
        required=False,
        label=__("Override DataSource"),
        description=__("Find all devices state/config data in this Data Source instead of bound ones"),
    )

    class Meta:
        name = __("Run Compliance Tests")
        description = __("Execute compliance tests and save the results")

    def __init__(self, datasource_sync_fn: Callable = datasource_sync):
        super().__init__()
        self.datasource_sync_fn = datasource_sync_fn
        self._nameset_functions = {}
        self.global_namesets = NameSet.objects.filter(_global=True)
        self.results_count = 0
        self.results_passed = 0

    def nameset_functions(self, namesets: Iterable[NameSet]) -> dict[str, Callable]:
        result = {}
        for nameset in chain(namesets, self.global_namesets):
            if nameset.name not in self._nameset_functions:
                try:
                    new_functions = nameset.extract()
                except Exception as e:
                    self.log_warning(f"Cannot extract code from nameset {nameset}, {type(e).__name__}: {e}")
                    new_functions = {}
                self._nameset_functions[nameset.name] = new_functions
            result |= self._nameset_functions[nameset.name]
        return result

    def run_test(self, device: VDevice, test: ComplianceTest) -> tuple[bool, list[tuple[Any, Any]]]:
        functions = self.nameset_functions(test.namesets.all())
        return test.run(device, functions, verbosity=self.script_data.explanation_verbosity)

    def run_tests_for_device(
        self,
        tests_qs: QuerySet[ComplianceTest],
        device: VDevice,
        report: ComplianceReport | None,
    ) -> Generator[ComplianceTestResult, None, None]:
        for test in tests_qs:
            explanation = []
            try:
                device.state  # noqa: B018
                passed, explanation = self.run_test(device, test)
            except EvalError as exc:
                self.log_failure(f"Failed to execute test **{test}** for device **{device}**, `{exc}`")
                passed = False
                explanation.append((str(exc), None))
            self.results_count += 1
            self.results_passed += int(passed)
            yield ComplianceTestResult(
                test=test,
                device=device,
                passed=passed,
                explanation=explanation,
                report=report,
                dynamic_pair=device.dynamic_pair,
            )
            time.sleep(self._sleep_between_tests)

    def get_device_qs(self, selector: ComplianceSelector) -> QuerySet[VDevice]:
        device_qs = selector.devices.select_related().prefetch_serializer().prefetch_poller()
        if self.script_data.override_datasource:
            device_qs = device_qs.set_datasource(self.script_data.override_datasource.obj)
        else:
            device_qs = device_qs.prefetch_datasource()
        if self.script_data.devices:
            device_qs = device_qs.filter(pk__in=self.script_data.devices)
        return device_qs

    def run_tests_for_selector(
        self, selector: ComplianceSelector, report: ComplianceReport | None
    ) -> Generator[ComplianceTestResult, None, None]:
        for device in self.get_device_qs(selector):
            try:
                yield from self.run_tests_for_device(selector.tests.all(), device, report)
            except SerializationError as e:
                self.log_failure(f"`{e}`, ignoring all tests for *{device}*")
                continue

    def fire_report_webhook(self, report_id: int) -> None:
        report = ComplianceReport.objects.filter(pk=report_id).annotate_result_stats().count_devices_and_tests().first()
        queue = events_queue.get()
        enqueue_object(queue, report, self.request.user, self.request.id, ObjectChangeActionChoices.ACTION_CREATE)

    def save_to_db(self, results: Iterable[ComplianceTestResult], report: ComplianceReport | None) -> None:
        ComplianceTestResult.objects.bulk_create(results, batch_size=self._result_batch_size)
        ComplianceTestResult.objects.delete_old()
        if report:
            ComplianceReport.objects.delete_old()

    def get_selectors(self) -> QuerySet[ComplianceSelector]:
        selectors = self.script_data.selectors.queryset
        test_qs = ComplianceTest.objects.all()
        if self.script_data.test_tags:
            test_qs = test_qs.filter(tags__pk__in=self.script_data.test_tags).distinct()
            selectors = selectors.filter(tests__tags__pk__in=self.script_data.test_tags).distinct()
        return selectors.prefetch_related(Prefetch("tests", test_qs.prefetch_related("namesets")))

    def datasources_to_sync(self) -> Iterable[VDataSource]:
        if self.script_data.override_datasource:
            return [self.script_data.override_datasource.obj]
        datasource_ids = (
            VDevice.objects.filter(self.script_data.device_filter)
            .annotate_datasource_id()
            .values_list("data_source_id", flat=True)
            .distinct()
        )
        return VDataSource.objects.filter(pk__in=datasource_ids)

    def run(self, data, commit):
        self.script_data = self.script_data_cls(data)
        selectors = self.get_selectors()
        if self.script_data.sync_datasources:
            self.datasource_sync_fn(self.datasources_to_sync(), device_filter=self.script_data.device_filter)
        with null_request():
            report = ComplianceReport.objects.create() if self.script_data.make_report else None
        results = chain.from_iterable(self.run_tests_for_selector(selector, report) for selector in selectors)
        self.save_to_db(results, report)
        output = {"results": {"all": self.results_count, "passed": self.results_passed}}
        if report:
            self.log_info(f"See [Compliance Report]({report.get_absolute_url()}) for detailed statistics")
            self.fire_report_webhook(report.pk)
        return yaml.dump(output, sort_keys=False)

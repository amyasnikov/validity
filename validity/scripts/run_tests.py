import time
from itertools import chain
from typing import Any, Callable, Generator, Iterable

import yaml
from dcim.models import Device
from django.db.models import Prefetch, QuerySet
from django.utils.translation import gettext as __
from extras.choices import ObjectChangeActionChoices
from extras.models import Tag
from extras.scripts import BooleanVar, ChoiceVar, MultiObjectVar
from extras.webhooks import enqueue_object
from netbox.context import webhooks_queue

import validity
from validity.choices import ExplanationVerbosityChoices
from validity.compliance.eval import ExplanationalEval
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
from validity.utils.misc import datasource_sync, null_request


class RequiredChoiceVar(ChoiceVar):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(choices, *args, **kwargs)
        self.field_attrs["choices"] = choices


class RunTestsScript:
    _sleep_between_tests = validity.settings.sleep_between_tests
    _result_batch_size = validity.settings.result_batch_size

    sync_datasources = BooleanVar(
        required=False,
        default=False,
        label=__("Sync Data Sources"),
        description=__('Sync all Data Source instances which have "device_config_path" defined'),
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
    explanation_verbosity = RequiredChoiceVar(
        choices=ExplanationVerbosityChoices.choices,
        default=ExplanationVerbosityChoices.maximum,
        label=__("Explanation Verbosity Level"),
        required=False,
    )

    class Meta:
        name = __("Run Compliance Tests")
        description = __("Execute compliance tests and save the results")

    def __init__(self):
        super().__init__()
        self._nameset_functions = {}
        self.global_namesets = NameSet.objects.filter(_global=True)
        self.verbosity = 2
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
        evaluator = ExplanationalEval(
            functions=functions, names={"device": device}, load_defaults=True, verbosity=self.verbosity
        )
        passed = bool(evaluator.eval(test.effective_expression))
        return passed, evaluator.explanation

    def run_tests_for_device(
        self,
        tests_qs: QuerySet[ComplianceTest],
        device: VDevice,
        report: ComplianceReport | None,
    ) -> Generator[ComplianceTestResult, None, None]:
        for test in tests_qs:
            explanation = []
            try:
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

    def run_tests_for_selector(
        self,
        selector: ComplianceSelector,
        report: ComplianceReport | None,
        device_ids: list[int],
    ) -> Generator[ComplianceTestResult, None, None]:
        qs = selector.devices.select_related().prefetch_datasource().prefetch_serializer().prefetch_poller()
        if device_ids:
            qs = qs.filter(pk__in=device_ids)
        for device in qs:
            try:
                yield from self.run_tests_for_device(selector.tests.all(), device, report)
            except SerializationError as e:
                self.log_failure(f"`{e}`, ignoring all tests for *{device}*")
                continue

    def fire_report_webhook(self, report_id: int) -> None:
        report = ComplianceReport.objects.filter(pk=report_id).annotate_result_stats().count_devices_and_tests().first()
        queue = webhooks_queue.get()
        enqueue_object(queue, report, self.request.user, self.request.id, ObjectChangeActionChoices.ACTION_CREATE)

    def save_to_db(self, results: Iterable[ComplianceTestResult], report: ComplianceReport | None) -> None:
        ComplianceTestResult.objects.bulk_create(results, batch_size=self._result_batch_size)
        ComplianceTestResult.objects.delete_old()
        if report:
            ComplianceReport.objects.delete_old()

    def get_selectors(self, data: dict) -> QuerySet[ComplianceSelector]:
        selectors = ComplianceSelector.objects.all()
        if specific_selectors := data.get("selectors"):
            selectors = selectors.filter(pk__in=specific_selectors)
        test_qs = ComplianceTest.objects.all()
        if test_tags := data.get("test_tags"):
            test_qs = test_qs.filter(tags__pk__in=test_tags).distinct()
            selectors = selectors.filter(tests__tags__pk__in=test_tags).distinct()
        return selectors.prefetch_related(Prefetch("tests", test_qs.prefetch_related("namesets")))

    def run(self, data, commit):
        self.verbosity = int(data.get("explanation_verbosity", self.verbosity))
        if data.get("sync_datasources"):
            datasource_sync(VDataSource.objects.exclude(custom_field_data__device_config_path=None))
        with null_request():
            report = ComplianceReport.objects.create() if data.get("make_report") else None
        selectors = self.get_selectors(data)
        device_ids = data.get("devices", [])
        results = chain.from_iterable(
            self.run_tests_for_selector(selector, report, device_ids) for selector in selectors
        )
        self.save_to_db(results, report)
        output = {"results": {"all": self.results_count, "passed": self.results_passed}}
        if report:
            self.log_info(f"See [Compliance Report]({report.get_absolute_url()}) for detailed statistics")
            self.fire_report_webhook(report.pk)
        return yaml.dump(output, sort_keys=False)

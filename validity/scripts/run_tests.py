import builtins
import time
from inspect import getmembers
from itertools import chain
from typing import Any, Callable, Generator, Iterable

import yaml
from dcim.models import Device
from django.db.models import QuerySet
from django.utils.translation import gettext as __
from extras.choices import ObjectChangeActionChoices
from extras.scripts import BooleanVar, MultiObjectVar, Script
from extras.webhooks import enqueue_object
from netbox.context import webhooks_queue
from simpleeval import InvalidExpression

import validity
import validity.config_compliance.eval.default_nameset as default_nameset
from validity.config_compliance.eval import ExplanationalEval
from validity.config_compliance.exceptions import DeviceConfigError, EvalError
from validity.models import (
    ComplianceReport,
    ComplianceSelector,
    ComplianceTest,
    ComplianceTestResult,
    GitRepo,
    NameSet,
    VDevice,
)
from validity.utils.git import SyncReposMixin
from validity.utils.misc import null_request


class RunTestsScript(SyncReposMixin, Script):

    _sleep_between_tests = validity.settings.sleep_between_tests

    sync_repos = BooleanVar(
        required=False,
        default=False,
        label=__("Sync Repositories"),
        description=__("Pull updates from all available git repositories before running the tests"),
    )
    make_report = BooleanVar(default=True, label=__("Make Compliance Report"))
    selectors = MultiObjectVar(
        model=ComplianceSelector,
        required=False,
        label=__("Specific selectors"),
        description=__("Run the tests only for specific selectors"),
    )
    devices = MultiObjectVar(
        model=Device,
        required=False,
        label=__("Specific devices"),
        description=__("Run the tests only for specific devices"),
    )

    class Meta:
        name = __("Run Compliance Tests")
        description = __("Execute compliance tests and save the results")

    def __init__(self):
        super().__init__()
        self._nameset_functions = {}
        self.global_namesets = NameSet.objects.filter(_global=True)
        self.results_count = 0
        self.results_passed = 0

    def nameset_functions(self, namesets: Iterable[NameSet]) -> dict[str, Callable]:
        def extract_nameset(nameset, globals_):
            locs = {}
            exec(nameset.effective_definitions, globals_, locs)
            __all__ = set(locs.get("__all__", []))
            return {k: v for k, v in locs.items() if k in __all__ and callable(v)}

        result = {}
        globals_ = dict(getmembers(builtins)) | {
            name: getattr(default_nameset, name) for name in default_nameset.__all__
        }
        for nameset in chain(namesets, self.global_namesets):
            if nameset.name not in self._nameset_functions:
                try:
                    new_functions = extract_nameset(nameset, globals_)
                except Exception as e:
                    self.log_warning(f"Cannot extract code from nameset {nameset}, {type(e).__name__}: {e}")
                    new_functions = {}
                self._nameset_functions[nameset.name] = new_functions
            result |= self._nameset_functions[nameset.name]
        return result

    def run_test(self, device: VDevice, test: ComplianceTest) -> tuple[bool, list[tuple[Any, Any]]]:
        functions = self.nameset_functions(test.namesets.all())
        evaluator = ExplanationalEval(functions=functions, names={"device": device}, load_defaults=True)
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
                device.config
                passed, explanation = self.run_test(device, test)
            except (InvalidExpression, EvalError) as e:
                self.log_failure(f"Failed to execute test *{test}* for device *{device}*, `{type(e).__name__}: {e}`")
                passed = False
                explanation.append((f"{type(e).__name__}: {e}", None))
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
        qs = selector.devices.select_related().annotate_json_serializer().annotate_json_repo()
        if device_ids:
            qs = qs.filter(pk__in=device_ids)
        for device in qs:
            try:
                device.selector = selector
                yield from self.run_tests_for_device(selector.tests.all(), device, report)
            except DeviceConfigError as e:
                self.log_failure(f"`{e}`, ignoring all tests for *{device}*")
                continue

    def fire_report_webhook(self, report_id: int) -> None:
        report = ComplianceReport.objects.filter(pk=report_id).annotate_result_stats().count_devices_and_tests().first()
        queue = webhooks_queue.get()
        enqueue_object(queue, report, self.request.user, self.request.id, ObjectChangeActionChoices.ACTION_CREATE)

    def save_to_db(self, results: list[ComplianceTestResult], report: ComplianceReport | None) -> None:
        ComplianceTestResult.objects.bulk_create(results)
        ComplianceTestResult.objects.delete_old()
        if report:
            ComplianceReport.objects.delete_old()

    def run(self, data, commit):
        if data.get("sync_repos"):
            self.update_git_repos(GitRepo.objects.all())
        with null_request():
            report = ComplianceReport.objects.create() if data.get("make_report") else None
        selectors = ComplianceSelector.objects.prefetch_related("tests", "tests__namesets")
        device_ids = data.get("devices", [])
        if specific_selectors := data.get("selectors"):
            selectors = selectors.filter(pk__in=specific_selectors)
        results = [
            *chain.from_iterable(self.run_tests_for_selector(selector, report, device_ids) for selector in selectors)
        ]
        self.save_to_db(results, report)
        output = {"results": {"all": self.results_count, "passed": self.results_passed}}
        if report:
            self.log_info(f"See [Compliance Report]({report.get_absolute_url()}) for detailed statistics")
            self.fire_report_webhook(report.pk)
        return yaml.dump(output, sort_keys=False)


name = "Validity Compliance Tests"

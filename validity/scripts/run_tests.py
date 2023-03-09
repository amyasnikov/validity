from itertools import chain
from typing import Any, Callable, Iterable

from dcim.models import Device
from django.db.models import Q
from django.utils.translation import gettext as __
from extras.scripts import BooleanVar, Script
from simpleeval import InvalidExpression

import validity.config_compliance.solver.default_nameset as default_nameset
from validity import settings
from validity.config_compliance.device_config import DeviceConfig
from validity.config_compliance.exceptions import DeviceConfigError, EvalError
from validity.config_compliance.solver.eval import ExplanationalEval
from validity.config_compliance.solver.eval_defaults import DEFAULT_NAMES, DEFAULT_OPERATORS
from validity.models import ComplianceSelector, ComplianceTest, ComplianceTestResult, GitRepo, NameSet
from validity.queries import DeviceQS
from validity.utils.git import SyncReposMixin


class RunTestsScript(SyncReposMixin, Script):
    sync_repos = BooleanVar(
        required=False,
        default=False,
        label=__("Sync Repositories"),
        description=__("Pull updates from all available git repositories before running the tests"),
    )

    class Meta:
        name = __("Run Compliance Tests")
        description = __("Execute compliance tests and save the results")

    def __init__(self):
        super().__init__()
        self._nameset_functions = {}
        self.global_namesets = NameSet.objects.filter(_global=True)

    def nameset_functions(self, namesets: Iterable[NameSet]) -> dict[str, Callable]:
        def extract_nameset(nameset, globals_):
            locs = {}
            exec(nameset.effective_definitions, globals_, locs)
            __all__ = set(locs["__all__"])
            return {k: v for k, v in locs.items() if k in __all__ and isinstance(v, Callable)}

        result = {name: getattr(default_nameset, name) for name in default_nameset.__all__}
        globals_ = result.copy()
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

    @staticmethod
    def make_device(device_config: DeviceConfig, pair_config: DeviceConfig | None) -> Device:
        def device_from_cfg(device_cfg_obj):
            if device_cfg_obj is not None:
                d = device_cfg_obj.device
                d.config = device_cfg_obj.serialized
                return d

        device = device_from_cfg(device_config)
        device.dynamic_pair = device_from_cfg(pair_config)
        return device

    def run_test(
        self, device_config: DeviceConfig, pair_config: DeviceConfig | None, test: ComplianceTest
    ) -> tuple[bool, list[tuple[Any, Any]]]:
        functions = self.nameset_functions(test.namesets.all())
        device = self.make_device(device_config, pair_config)
        names = DEFAULT_NAMES | {"device": device}
        evaluator = ExplanationalEval(DEFAULT_OPERATORS, functions, names)
        passed = bool(evaluator.eval(test.effective_expression))
        return passed, [("str(device.dynamic_pair)", str(device.dynamic_pair))] + evaluator.explanation

    @staticmethod
    def device_iterator(filter_: Q | None):
        if not filter_:
            return
        devices = DeviceQS().filter(filter_).annotate_json_serializer().annotate_json_repo()
        yield from devices.json_iterator("serializer", "repo")

    def run(self, data, commit):
        if data.get("sync_repos"):
            self.update_git_repos(GitRepo.objects.all())
        selectors = ComplianceSelector.objects.prefetch_related("tests", "tests__namesets")
        results = []
        for selector in selectors:
            for device in self.device_iterator(selector.filter):
                try:
                    config = DeviceConfig.from_device(device)
                    dynamic_pair = next(self.device_iterator(selector.dynamic_pair_filter(device)), None)
                    pair_config = DeviceConfig.from_device(dynamic_pair) if dynamic_pair else None
                except DeviceConfigError as e:
                    self.log_failure(str(e) + f", ignoring all tests for {device}")
                    continue
                for test in selector.tests.all():
                    explanation = []
                    try:
                        passed, explanation = self.run_test(config, pair_config, test)
                    except (InvalidExpression, EvalError) as e:
                        self.log_failure(
                            f"Failed to execute test {test} for device {config.device}, {type(e).__name__}: {e}"
                        )
                        passed = False
                        explanation.append((f"{type(e).__name__}: {e}", None))
                    results.append(
                        ComplianceTestResult(test=test, device=config.device, passed=passed, explanation=explanation)
                    )
        ComplianceTestResult.objects.bulk_create(results)
        ComplianceTestResult.objects.last_more_than(settings.store_last_results).delete()


name = "Validity Compliance Tests"

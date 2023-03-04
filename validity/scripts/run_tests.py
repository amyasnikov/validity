from typing import Any, Callable, Iterable

from dcim.models import Device
from django.db.models import Q
from django.utils.translation import gettext as __
from extras.scripts import Script
from simpleeval import InvalidExpression

import validity.config_compliance.solver.default_nameset as default_nameset
from validity import settings
from validity.config_compliance.device_config import DeviceConfig, serialize_configs
from validity.config_compliance.solver.eval import ExplanationalEval
from validity.config_compliance.solver.eval_defaults import DEFAULT_NAMES, DEFAULT_OPERATORS
from validity.models import ComplianceSelector, ComplianceTest, ComplianceTestResult, NameSet
from validity.queries import DeviceQS


class RunTestsScript(Script):
    class Meta:
        name = __("Run Compliance Tests")
        description = __("Execute compliance tests and save the results")

    def __init__(self):
        super().__init__()
        self._nameset_functions = {}

    def nameset_functions(self, namesets: Iterable[NameSet]) -> dict[str, Callable]:
        def extract_nameset(nameset):
            __all__ = []
            exec(nameset.effective_definitions)
            __all__ = set(__all__)
            return {k: v for k, v in locals().items() if k in __all__ and isinstance(v, Callable)}

        result = {name: getattr(default_nameset, name) for name in default_nameset.__all__}
        for nameset in namesets:
            if nameset.name not in self._nameset_functions:
                try:
                    new_functions = extract_nameset(nameset)
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
        functions = self.nameset_functions(device_config.device.namesets)
        device = self.make_device(device_config, pair_config)
        names = DEFAULT_NAMES | {"device": device}
        evaluator = ExplanationalEval(DEFAULT_OPERATORS, functions, names)
        passed = bool(evaluator.eval(test.effective_expression))
        return passed, evaluator.explanation

    @staticmethod
    def device_iterator(filter_: Q | None, namesets: bool = False):
        if not filter_:
            yield None
            return
        fields = {"serializer", "repo"}
        devices = DeviceQS().filter(filter_).annotate_json_serializer().annotate_json_repo()
        if namesets:
            fields.add("namesets")
            devices = devices.annotate_json_namesets()
        yield from devices.json_iterator(*fields)

    def run(self, data, commit):
        selectors = ComplianceSelector.objects.prefetch_related("tests")
        results = []
        for selector in selectors:
            for device in self.device_iterator(selector.filter, namesets=True):
                config = DeviceConfig.from_device(device)
                dynamic_pair = next(self.device_iterator(selector.dynamic_pair_filter(device)))
                pair_config = DeviceConfig.from_device(dynamic_pair) if dynamic_pair else None
                serialize_configs([config, pair_config])
                for test in selector.tests.all():
                    try:
                        passed, explanation = self.run_test(config, pair_config, test)
                    except InvalidExpression as e:
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

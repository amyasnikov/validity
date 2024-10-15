from dataclasses import dataclass, field
from unittest.mock import Mock

import pytest
from factories import CompTestDBFactory, CompTestResultFactory, DeviceFactory, NameSetDBFactory, SelectorFactory

from validity.compliance.eval.eval_defaults import DEFAULT_NAMESET
from validity.compliance.exceptions import EvalError
from validity.models import ComplianceTest
from validity.scripts.data_models import ExecutionResult
from validity.scripts.data_models import TestResultRatio as ResultRatio
from validity.scripts.runtests.apply import ApplyWorker, DeviceTestIterator
from validity.scripts.runtests.apply import TestExecutor as TExecutor


NS_1 = """
__all__ = ["func1", "var", "func2"]

def func1(var): pass

var = 1234

def func2(var): pass
"""

NS_2 = """
from collections import Counter
import itertools

__all__ = ["func3", "non_existing_func", "Counter", "itertools"]

def func3(): pass
"""

NS_3 = "some wrong syntax"


@pytest.mark.parametrize(
    "nameset_texts, extracted_fn_names, warning_calls",
    [
        pytest.param(["", ""], set(), 0, id="empty"),
        pytest.param([NS_1], {"func1", "func2"}, 0, id="NS_1"),
        pytest.param([NS_2], {"func3", "Counter"}, 0, id="NS_2"),
        pytest.param([NS_1, NS_2], {"func1", "func2", "func3", "Counter"}, 0, id="NS_1, NS_2"),
        pytest.param([NS_3], set(), 1, id="NS_3"),
        pytest.param([NS_3, NS_1, NS_3], {"func1", "func2"}, 2, id="NS3, NS_1, NS_3"),
    ],
)
@pytest.mark.django_db
def test_nameset_functions(nameset_texts, extracted_fn_names, warning_calls):
    script = TExecutor(1, 2, 10)
    namesets = [NameSetDBFactory(definitions=d) for d in nameset_texts]
    functions = script.nameset_functions(namesets)
    assert extracted_fn_names == functions.keys()
    assert len(script.log.messages) == warning_calls
    for fn_name, fn in functions.items():
        assert fn_name == fn.__name__
        assert callable(fn)


FUNC = """
__all__ = ['func']
{}
"""


@pytest.mark.parametrize(
    "definitions",
    [
        pytest.param(FUNC.format("def func(): return max(1, 10)"), id="max"),
        pytest.param(FUNC.format('def func(): return jq.first(".data", {"data": [1,2,3]})'), id="jq"),
    ],
)
@pytest.mark.django_db
def test_builtins_are_available_in_nameset(definitions):
    script = TExecutor(10, 20, 30, extra_globals=DEFAULT_NAMESET)
    namesets = [NameSetDBFactory(definitions=definitions)]
    functions = script.nameset_functions(namesets)
    functions["func"]()


@pytest.mark.django_db
def test_run_tests_for_device():
    device = DeviceFactory()
    device.__dict__["state"] = {"a": "b"}
    device.__dict__["dynamic_pair"] = DeviceFactory(name="dynpair")
    namesets = Mock(**{"all.return_value": []})
    tests = [Mock(namesets=namesets, spec=ComplianceTest, _state=Mock(db="default")) for _ in range(3)]
    tests[0].run.return_value = True, []
    tests[1].run.return_value = False, [("some", "explanation")]
    tests[2].run.side_effect = EvalError("some test error")
    executor = TExecutor(10, explanation_verbosity=2, report_id=30)
    results = [
        {
            "passed": r.passed,
            "explanation": r.explanation,
            "report_id": r.report_id,
            "dynamic_pair": r.dynamic_pair.name,
        }
        for r in executor.run_tests_for_device(tests, device)
    ]
    assert results == [
        {"passed": True, "explanation": [], "report_id": 30, "dynamic_pair": "dynpair"},
        {"passed": False, "explanation": [("some", "explanation")], "report_id": 30, "dynamic_pair": "dynpair"},
        {"passed": False, "explanation": [("some test error", None)], "report_id": 30, "dynamic_pair": "dynpair"},
    ]
    for test in tests:
        test.run.assert_called_once_with(device, {}, verbosity=2)
    assert executor.results_passed == 1
    assert executor.results_count == 3


@pytest.mark.django_db
def test_devicetest_iterator():
    devices = [DeviceFactory() for _ in range(3)]
    selectors = [SelectorFactory(), SelectorFactory()]
    tests = [CompTestDBFactory() for _ in range(5)]
    selectors[0].tests.set(tests[:2])
    selectors[1].tests.set(tests[2:])
    selector_devices = {selectors[0].pk: [devices[0].pk, devices[1].pk], selectors[1].pk: [d.pk for d in devices[2:]]}
    iterator = DeviceTestIterator(selector_devices, [], None)
    iter_values = [(list(d.order_by("pk")), list(t.order_by("pk"))) for d, t in iterator]
    assert iter_values[::-1] == [(devices[:2], tests[:2]), (devices[2:], tests[2:])]


@pytest.fixture
def apply_worker():
    test_results = CompTestResultFactory.build_batch(size=3)
    executor = Mock(results_passed=5, results_count=10, return_value=test_results)
    executor.log.messages = ["log1", "log2"]
    device_test_gen = Mock(return_value=[(["device1"], ["test1"]), (["device2"], ["test2"])])
    job_extractor_factory = Mock()
    job_extractor_factory.return_value.parent.job.result.slices = [None, {1: [1, 2, 3]}]
    return ApplyWorker(
        testresult_queryset=Mock(),
        test_executor_cls=Mock(return_value=executor),
        result_batch_size=100,
        job_extractor_factory=job_extractor_factory,
        device_test_gen=device_test_gen,
    )


@pytest.mark.django_db
def test_applyworker_success(full_runtests_params, apply_worker):
    full_runtests_params.overriding_datasource = 10
    full_runtests_params.test_tags = [555]
    device_test_gen = apply_worker.device_test_gen
    executor = apply_worker.test_executor_cls.return_value
    test_results = executor.return_value
    result = apply_worker(params=full_runtests_params, worker_id=1)
    assert result == ExecutionResult(test_stat=ResultRatio(passed=5, total=10), log=["log1", "log2"])
    device_test_gen.assert_called_once_with(
        {1: [1, 2, 3]}, full_runtests_params.test_tags, full_runtests_params.overriding_datasource
    )
    apply_worker.testresult_queryset.bulk_create.assert_called_once()
    assert list(apply_worker.testresult_queryset.bulk_create.call_args.args[0]) == test_results * len(
        device_test_gen.return_value
    )
    assert executor.call_count == len(device_test_gen.return_value)


@dataclass
class MockLogger:
    script_id: str
    messages: list = field(default_factory=list, init=False)

    def log_exception(self, m):
        self.messages.append(str(m))


@pytest.mark.django_db
def test_applyworker_exception(full_runtests_params, apply_worker):
    apply_worker.test_executor_cls = Mock(side_effect=ValueError("some error"))
    apply_worker.logger_factory = MockLogger
    result = apply_worker(params=full_runtests_params, worker_id=1)
    assert result == ExecutionResult(test_stat=ResultRatio(passed=0, total=0), log=["some error"], errored=True)

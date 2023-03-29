from collections import namedtuple
from unittest.mock import Mock

import pytest
from factories import NameSetDBFactory
from simpleeval import InvalidExpression

import validity.config_compliance.eval.default_nameset as default_nameset
from validity.config_compliance.eval.eval_defaults import DEFAULT_NAMES, DEFAULT_OPERATORS
from validity.config_compliance.exceptions import EvalError
from validity.scripts import run_tests
from validity.scripts.run_tests import RunTestsScript


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
def test_nameset_functions(nameset_texts, extracted_fn_names, warning_calls, mock_script_logging):
    script = RunTestsScript()
    namesets = [NameSetDBFactory(definitions=d) for d in nameset_texts]
    functions = script.nameset_functions(namesets)
    default_ns_names = set(default_nameset.__all__)
    assert default_ns_names | extracted_fn_names == functions.keys()
    assert script.log_warning.call_count == warning_calls
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
        pytest.param(FUNC.format('def func(): return jq(".data", {"data": [1,2,3]})'), id="jq"),
    ],
)
@pytest.mark.django_db
def test_builtins_are_available_in_nameset(definitions):
    script = RunTestsScript()
    namesets = [NameSetDBFactory(definitions=definitions)]
    functions = script.nameset_functions(namesets)
    functions["func"]()


@pytest.mark.parametrize("device_cfg, pair_cfg", [(Mock(), Mock()), (Mock(), None)])
def test_make_device(device_cfg, pair_cfg):
    script = RunTestsScript()
    device = script.make_device(device_cfg, pair_cfg)
    assert device == device_cfg.device
    assert device.config == device_cfg.serialized
    if pair_cfg is None:
        assert device.dynamic_pair is None
    else:
        assert device.dynamic_pair == pair_cfg.device
        assert device.dynamic_pair.config == pair_cfg.serialized


def test_run_test(monkeypatch):
    script = RunTestsScript()
    nm_functions = Mock()
    make_device = Mock()
    evaluator_cls = Mock(return_value=Mock(explanation=[("var1", "val1")]))
    monkeypatch.setattr(script, "nameset_functions", nm_functions)
    monkeypatch.setattr(script, "make_device", make_device)
    monkeypatch.setattr(run_tests, "ExplanationalEval", evaluator_cls)
    device_cfg = Mock()
    pair_cfg = Mock()
    test = Mock()
    passed, explanation = script.run_test(device_cfg, pair_cfg, test)
    assert passed  # bool(Mock()) is True
    assert len(explanation) == 2
    assert explanation[0][0] == "str(device.dynamic_pair)"
    assert explanation[1] == ("var1", "val1")
    nm_functions.assert_called_once_with(test.namesets.all())
    make_device.assert_called_once_with(device_cfg, pair_cfg)
    evaluator_cls.assert_called_once_with(
        DEFAULT_OPERATORS, nm_functions.return_value, DEFAULT_NAMES | {"device": make_device.return_value}
    )
    evaluator_cls.return_value.eval.assert_called_once_with(test.effective_expression)


@pytest.mark.parametrize(
    "run_test_mock",
    [
        Mock(return_value=(True, [("expla", "nation")])),
        Mock(return_value=(False, [("1", "2"), ("3", "4")])),
        Mock(side_effect=InvalidExpression()),
        Mock(side_effect=EvalError(InvalidExpression())),
    ],
)
def test_run_tests_for_device(mock_script_logging, run_test_mock, monkeypatch):
    result_cls = namedtuple("MockResult", "passed explanation device test report")
    monkeypatch.setattr(run_tests, "ComplianceTestResult", result_cls)
    script = RunTestsScript()
    script._sleep_between_tests = 0
    monkeypatch.setattr(script, "run_test", run_test_mock)
    tests = ["test1", "test2", "test3"]
    device_config = Mock()
    pair_config = Mock()
    report = Mock()
    results = list(script.run_tests_for_device(tests, device_config, pair_config, report))
    assert len(results) == len(tests)
    is_error = isinstance(run_test_mock.side_effect, Exception)
    for test, result in zip(tests, results):
        assert result.test == test
        if is_error:
            assert script.log_failure.call_count == len(tests)
            assert result.passed is False
            assert len(result.explanation) == 1 and result.explanation[0][1] is None
        else:
            assert result.passed == run_test_mock.return_value[0]
            assert result.explanation == run_test_mock.return_value[1]
        assert result.report == report
    assert run_test_mock.call_count == len(tests)


def test_run_tests_for_selector(mock_script_logging, monkeypatch):
    script = RunTestsScript()
    monkeypatch.setattr(script, "prepare_device_configs", Mock(return_value=("config", "pair_config")))
    devices = ["device1", "device2"]
    monkeypatch.setattr(script, "device_iterator", Mock(return_value=devices))
    monkeypatch.setattr(script, "run_tests_for_device", Mock(return_value=range(3)))
    selector = Mock()
    report = Mock()
    list(script.run_tests_for_selector(selector, report))
    script.device_iterator.assert_called_once_with(selector.filter)
    assert script.prepare_device_configs.call_count == len(devices)
    assert script.run_tests_for_device.call_count == len(devices)
    script.run_tests_for_device.assert_called_with(selector.tests.all(), "config", "pair_config", report)

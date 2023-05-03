from collections import namedtuple
from unittest.mock import Mock
from uuid import uuid4

import pytest
from factories import CompTestDBFactory, DeviceFactory, NameSetDBFactory, ReportFactory, SelectorFactory
from simpleeval import InvalidExpression

from validity.config_compliance.exceptions import EvalError
from validity.models import ComplianceReport, ComplianceTestResult, VDevice
from validity.scripts import run_tests
from validity.scripts.run_tests import RunTestsScript
from validity.utils.misc import null_request


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
    assert extracted_fn_names == functions.keys()
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
        pytest.param(FUNC.format('def func(): return jq.first(".data", {"data": [1,2,3]})'), id="jq"),
    ],
)
@pytest.mark.django_db
def test_builtins_are_available_in_nameset(definitions):
    script = RunTestsScript()
    namesets = [NameSetDBFactory(definitions=definitions)]
    functions = script.nameset_functions(namesets)
    functions["func"]()


def test_run_test(monkeypatch):
    script = RunTestsScript()
    nm_functions = Mock()
    evaluator_cls = Mock(return_value=Mock(explanation=[("var1", "val1")]))
    monkeypatch.setattr(script, "nameset_functions", nm_functions)
    monkeypatch.setattr(run_tests, "ExplanationalEval", evaluator_cls)
    device = Mock()
    test = Mock()
    passed, explanation = script.run_test(device, test)
    assert passed  # bool(Mock()) is True
    assert explanation
    nm_functions.assert_called_once_with(test.namesets.all())
    evaluator_cls.assert_called_once_with(
        functions=nm_functions.return_value, names={"device": device}, load_defaults=True
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
    result_cls = namedtuple("MockResult", "passed explanation device test report dynamic_pair")
    monkeypatch.setattr(run_tests, "ComplianceTestResult", result_cls)
    script = RunTestsScript()
    script._sleep_between_tests = 0
    monkeypatch.setattr(script, "run_test", run_test_mock)
    tests = ["test1", "test2", "test3"]
    device = Mock()
    report = Mock()
    results = list(script.run_tests_for_device(tests, device, report))
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
    devices = [Mock(name="device1"), Mock(name="device2")]
    monkeypatch.setattr(script, "run_tests_for_device", Mock(return_value=range(3)))
    selector = Mock(
        name="selector",
        **{
            "devices.select_related.return_value"
            ".annotate_json_serializer.return_value.annotate_json_repo.return_value": devices
        }
    )
    report = Mock()
    list(script.run_tests_for_selector(selector, report, []))
    assert script.run_tests_for_device.call_count == len(devices)
    script.run_tests_for_device.assert_any_call(selector.tests.all(), devices[0], report)
    script.run_tests_for_device.assert_any_call(selector.tests.all(), devices[1], report)
    assert devices[0].selector == selector


@pytest.mark.django_db
def test_webhook_without_ctx_is_not_fired(monkeypatch):
    enq_obj = Mock()
    monkeypatch.setattr(run_tests, "enqueue_object", enq_obj)
    with null_request():
        ComplianceReport.objects.create()
    enq_obj.assert_not_called()


@pytest.mark.django_db
def test_fire_report_webhook(monkeypatch):
    enq_obj = Mock()
    monkeypatch.setattr(run_tests, "enqueue_object", enq_obj)
    script = RunTestsScript()
    script.request = Mock(id=uuid4(), user=Mock(username="admin"))
    report = ReportFactory()
    script.fire_report_webhook(report.pk)
    enq_obj.assert_called_once()


@pytest.mark.django_db
def test_full_run(monkeypatch):
    DeviceFactory(name="device1")
    DeviceFactory(name="device2")
    selector = SelectorFactory(name_filter="device([0-9])", dynamic_pairs="NAME")
    monkeypatch.setattr(
        VDevice,
        "config",
        property(lambda self: {"key2": "somevalue"} if self.name == "device2" else {"key1": "somevalue"}),
    )
    test = CompTestDBFactory(
        expression='jq.first(".key1", device.config) == jq.first(".key2", device.dynamic_pair.config) != None'
    )
    test.selectors.set([selector])
    script = RunTestsScript()
    script.run(data={"make_report": False}, commit=True)
    results = [*ComplianceTestResult.objects.order_by("device__name")]
    assert len(results) == 2
    assert results[0].passed and not results[1].passed

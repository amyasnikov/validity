from unittest.mock import MagicMock

import pytest
from factories import CompTestDBFactory, DataSourceFactory, DeviceFactory, PollerFactory


@pytest.mark.django_db
def test_run_test(monkeypatch):
    test = CompTestDBFactory(expression="1==1")
    device = DeviceFactory()
    device.data_source = DataSourceFactory()
    device.poller = PollerFactory()
    evaluator_cls = MagicMock()
    monkeypatch.setattr(test, "evaluator_cls", evaluator_cls)
    functions = {"f1": lambda x: x * 10}
    names = {"name1": 10}
    verbosity = object()
    passed, explanation = test.run(device, functions, names, verbosity)
    assert passed == evaluator_cls.return_value.eval.return_value.__bool__.return_value
    evaluator_cls.return_value.eval.assert_called_once_with("1==1")
    assert explanation == evaluator_cls.return_value.explanation
    evaluator_cls.assert_called_once()
    assert evaluator_cls.call_args.kwargs["functions"] == functions
    assert evaluator_cls.call_args.kwargs["names"] == names | {
        "device": device,
        "_poller": device.poller,
        "_data_source": device.data_source,
    }
    assert evaluator_cls.call_args.kwargs["verbosity"] == verbosity

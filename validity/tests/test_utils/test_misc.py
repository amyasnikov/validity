import operator
from contextlib import nullcontext

import pytest

from validity.utils.misc import NetboxVersion, reraise


class Error1(Exception):
    pass


class Error2(Exception):
    pass


@pytest.mark.parametrize(
    "internal_exc, external_exc, msg",
    [
        (None, None, None),
        (Error1("some_error1"), Error2(), None),
        (Error1("some_error1"), Error2(), "some_message"),
    ],
)
def test_reraise(internal_exc, external_exc, msg):
    ctx = (
        pytest.raises(type(external_exc), match=str(internal_exc) if not msg else msg)
        if external_exc is not None
        else nullcontext()
    )
    with ctx:
        with reraise(type(internal_exc), type(external_exc), msg):
            if internal_exc is not None:
                raise internal_exc


@pytest.mark.parametrize(
    "obj1, obj2, compare_results",
    [
        (NetboxVersion("3.5"), 3.5, [False, True, True, True, False]),
        (NetboxVersion("3.5.0"), NetboxVersion(3.5), [False, True, True, True, False]),
        (NetboxVersion(3), "1.5.2", [False, False, False, True, True]),
        (NetboxVersion("3.6-beta2"), "3.6.1", [True, True, False, False, False]),
    ],
)
def test_netbox_version(obj1, obj2, compare_results):
    operators = [operator.lt, operator.le, operator.eq, operator.ge, operator.gt]
    for op, expected_result in zip(operators, compare_results):
        assert op(obj1, obj2) is expected_result

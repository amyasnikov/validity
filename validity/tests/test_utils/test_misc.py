import operator
from contextlib import nullcontext

import pytest

from validity.utils.misc import reraise
from validity.utils.version import NetboxVersion


class Error1(Exception):
    pass


class Error2(Exception):
    pass


class Error3(Exception):
    def __init__(self, *args: object, orig_error) -> None:
        self.orig_error = orig_error
        super().__init__(*args)


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
        args = () if msg is None else (msg,)
        with reraise(type(internal_exc), type(external_exc), *args):
            if internal_exc is not None:
                raise internal_exc


def test_reraise_orig_error():
    try:
        with reraise(TypeError, Error3):
            raise TypeError("message")
    except Error3 as e:
        assert isinstance(e.orig_error, TypeError)
        assert e.orig_error.args == ("message",)


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

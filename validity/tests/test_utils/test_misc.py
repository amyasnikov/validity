from contextlib import nullcontext

import pytest

from validity.utils.misc import reraise


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

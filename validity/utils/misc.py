import inspect
from contextlib import contextmanager, suppress
from itertools import chain, islice
from logging import Logger
from typing import Callable, Collection, Iterable

from django.db.models import Model
from django.utils.functional import Promise
from netbox.context import current_request


@contextmanager
def null_request():
    """
    Prevents EventRule instances from triggering by setting current request to None
    """
    ctx = current_request.get()
    current_request.set(None)
    try:
        yield
    finally:
        current_request.set(ctx)


@contextmanager
def reraise(
    catch: type[Exception] | tuple[type[Exception], ...],
    raise_: type[Exception],
    *args,
    orig_error_param: str | None = "orig_error",
    **kwargs,
):
    """
    Catch one exception and raise another exception of different type,
    args and kwargs will be passed to the newly generated exception
    """
    try:
        yield
    except raise_:
        raise
    except catch as catched_err:
        if not args:
            args += (str(catched_err),)
        with suppress(Exception):
            if orig_error_param in inspect.signature(raise_).parameters:
                kwargs[orig_error_param] = catched_err
        raise raise_(*args, **kwargs) from catched_err


def batched(iterable: Iterable, n: int, container: type = list):
    """
    Batch data into containers of length n. Equal to python3.12 itertools.batched
    """
    it = iter(iterable)
    while True:
        batch = container(islice(it, n))
        if not batch:
            return
        yield batch


def partialcls(cls, *args, **kwargs):
    """
    Returns partial class with args and kwargs applied to __init__.
    All original class attributes are preserved. When called, returns original class instance
    """

    def __new__(_, *new_args, **new_kwargs):
        new_args = args + new_args
        new_kwargs = kwargs | new_kwargs
        return cls(*new_args, **new_kwargs)

    return type(cls.__name__, (cls,), {"__new__": __new__})


@contextmanager
def log_exceptions(logger: Logger, level: str, log_traceback=True):
    """
    Log exceptions of a function/method/codeblock
    """
    try:
        yield
    except Exception as exc:
        log_method = getattr(logger, level)
        log_method(msg=str(exc), exc_info=log_traceback)
        raise


class LazyIterator(Promise):
    def __init__(self, *parts: Callable[[], Collection] | Collection):
        self._parts = parts

    def __iter__(self):
        yield from chain.from_iterable(part() if callable(part) else part for part in self._parts)


def md_link(model: Model) -> str:
    """
    Turns django model instance into markdown link
    """
    url = model.get_absolute_url()
    return f"[{model}]({url})"

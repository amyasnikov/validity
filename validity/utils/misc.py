import inspect
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, Any, Callable, Iterable

from core.exceptions import SyncError
from django.utils.html import format_html
from netbox.context import current_request


if TYPE_CHECKING:
    from core.models import DataSource


def colorful_percentage(percent: float) -> str:
    levels = {75: "warning", 50: "orange", 25: "danger"}
    badge_color = "success"
    for level, color in levels.items():
        if level <= percent:
            break
        badge_color = color
    percent = round(percent, 1)
    return format_html('<span class="badge rounded-pill bg-{}">{}%</span>', badge_color, percent)


@contextmanager
def null_request():
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
    orig_error_param="orig_error",
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
        with suppress():
            if orig_error_param in inspect.signature(raise_).parameters:
                kwargs[orig_error_param] = catched_err
        raise raise_(*args, **kwargs) from catched_err


def datasource_sync(
    datasources: Iterable["DataSource"],
    threads: int = 10,
    fail_handler: Callable[["DataSource", Exception], Any] | None = None,
):
    """
    Parrallel sync of multiple Data Sources
    """

    def sync_func(datasource):
        try:
            datasource.sync()
        except SyncError as e:
            if fail_handler:
                fail_handler(datasource, e)

    with ThreadPoolExecutor(max_workers=threads) as tp:
        any(tp.map(sync_func, datasources))

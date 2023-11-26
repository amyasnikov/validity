from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
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
def reraise(catch: type[Exception] | tuple[type[Exception], ...], raise_: type[Exception], msg: Any = None):
    try:
        yield
    except raise_:
        raise
    except catch as e:
        if msg and isinstance(msg, str):
            msg = msg.format(str(e))
        if not msg:
            msg = str(e)
        raise raise_(msg) from e


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

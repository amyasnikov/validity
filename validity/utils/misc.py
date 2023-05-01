from contextlib import contextmanager

from django.utils.html import format_html
from netbox.context import current_request


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
def reraise(catch: type[Exception] | tuple[type[Exception], ...], raise_: type[Exception], msg: str | None = None):
    try:
        yield
    except raise_:
        raise
    except catch as e:
        if msg:
            msg = msg.format(str(e))
        else:
            msg = str(e)
        raise raise_(msg) from e

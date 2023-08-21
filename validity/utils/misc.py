import operator
from contextlib import contextmanager
from functools import total_ordering
from typing import Any

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


@total_ordering
class NetboxVersion:
    def __init__(self, version: str | float | int) -> None:
        version = str(version)
        version, *suffix = version.split("-", maxsplit=1)
        splitted_version = [int(i) for i in version.split(".")]
        while len(splitted_version) < 3:
            splitted_version.append(0)
        if suffix:
            splitted_version.append(suffix[0])
        self.version = tuple(splitted_version)

    def _compare(self, operator_, other):
        if isinstance(other, type(self)):
            return operator_(self.version, other.version)
        return operator_(self.version, type(self)(other).version)

    def __eq__(self, other) -> bool:
        return self._compare(operator.eq, other)

    def __lt__(self, other) -> bool:
        return self._compare(operator.lt, other)

    def __str__(self) -> str:
        return ".".join(str(i) for i in self.version)

    def __repr__(self) -> str:
        return f"NetboxVersion({str(self)})"

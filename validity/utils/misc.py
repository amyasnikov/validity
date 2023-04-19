from contextlib import contextmanager

from dcim.models import Device
from django.utils.html import format_html
from netbox.context import current_request

from validity.models import VDevice


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
    yield
    current_request.set(ctx)


def config(device: Device) -> dict | list | None:
    vdevice = VDevice()
    vdevice.__dict__ = device.__dict__.copy()
    return vdevice.config

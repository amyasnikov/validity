from typing import Any

from django import template
from django.db.models import Model
from django.utils.safestring import mark_safe
from utilities.templatetags.builtins.filters import linkify, placeholder
from dcim.models import Device


register = template.Library()


@register.filter
def colored_choice(obj: Model, field: str) -> str:
    value = getattr(obj, f"get_{field}_display")
    color = getattr(obj, f"get_{field}_color")
    return mark_safe(f'<span class="badge bg-{color()}">{value()}</span>')


@register.filter
def linkify_list(obj_list: list[Model], attr: str | None = None) -> str:
    result = ", ".join(linkify(obj, attr) for obj in obj_list)
    return placeholder("") if not result else mark_safe(result)


@register.filter
def checkmark(value: Any) -> str:
    value = bool(value)
    attr_map = {False: "mdi-close-thick text-danger", True: "mdi-check-bold text-success"}
    attr = attr_map[value]
    return mark_safe(f'<i class="mdi {attr}" title="{value}"></i>')


@register.filter
def device_config_url(device: Device) -> str:
    """
    Returns link to device config in external system
    device MUST be annotated with ".repo"
    """
    try:
        repo = device.repo
        file_path = repo.rendered_device_path(device)
        return repo.repo_url.rstrip('/') + '/' + file_path.lstrip('/')
    except AttributeError:
        return ''

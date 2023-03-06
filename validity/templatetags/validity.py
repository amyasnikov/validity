from typing import Any

from dcim.models import Device
from django import template
from django.db.models import Model
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from utilities.templatetags.builtins.filters import linkify, placeholder

from validity.models import GitRepoLinkMixin


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
def device_path(device: Device) -> str:
    """
    Returns device config path
    device MUST be annotated with ".repo"
    """
    try:
        repo = device.repo
        return repo.rendered_device_path(device)
    except AttributeError:
        return ""


@register.filter
def data_source(model: GitRepoLinkMixin) -> str:
    return _("Git") if model.repo else _("DB")


@register.simple_tag
def urljoin(*parts: str) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    middle_parts = "/".join((part.strip("/") for part in parts[1:-1]))
    url_parts = [parts[0].rstrip("/"), parts[-1].lstrip("/")]
    if middle_parts:
        url_parts.insert(1, middle_parts)
    return "/".join(url_parts)

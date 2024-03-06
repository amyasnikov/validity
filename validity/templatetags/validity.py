from typing import Any

from django import template
from django.db.models import Model
from django.http.request import HttpRequest
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from utilities.templatetags.builtins.filters import linkify, placeholder

from validity.utils.misc import colorful_percentage as _colorful_percentage


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
def data_source(model) -> str:
    return _("Data Source") if model.data_source else _("DB")


@register.filter
def colorful_percentage(percent):
    return _colorful_percentage(percent)


@register.simple_tag
def url_with_query_params(request: HttpRequest, **params):
    params = {k: [v] if not isinstance(v, list) else v for k, v in params.items()}
    query_params = request.GET.copy()
    query_params |= params
    return f"{request.path}?{query_params.urlencode()}"


@register.simple_tag
def urljoin(*parts: str) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    middle_parts = "/".join((part.strip("/") for part in parts[1:-1]))
    url_parts = [parts[0].rstrip("/"), parts[-1].lstrip("/")]
    if middle_parts:
        url_parts.insert(1, middle_parts)
    return "/".join(url_parts)


@register.inclusion_tag("validity/inc/report_stats_row.html")
def report_stats_row(obj, row_name, severity):
    for i, row_part in enumerate((row_parts := row_name.split())):
        if row_part.lower() in {"low", "middle", "high"}:
            row_parts[i] = f"<b>{row_part.upper()}</b>"
    row_name = mark_safe(" ".join(row_parts))
    count = getattr(obj, f"{severity}_count")
    passed = getattr(obj, f"{severity}_passed")
    percentage = getattr(obj, f"{severity}_percentage")
    return {"row_name": row_name, "passed": passed, "count": count, "percentage": percentage}

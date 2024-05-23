import json
from contextlib import suppress
from typing import Any

from django.forms import Select, Textarea


class PrettyJSONWidget(Textarea):
    def __init__(self, attrs=None, indent=2) -> None:
        super().__init__(attrs)
        self.attrs.setdefault("style", "font-family:monospace")
        self.indent = indent

    def format_value(self, value: Any) -> str | None:
        with suppress(Exception):
            return json.dumps(json.loads(value), indent=self.indent)
        return super().format_value(value)


class SelectWithPlaceholder(Select):
    def __init__(self, attrs=None, choices=()) -> None:
        super().__init__(attrs, choices)
        self.attrs["class"] = "netbox-static-select"

    def create_option(self, name, value, label, selected, index: int, subindex=..., attrs=...):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if index == 0:
            option["attrs"]["data-placeholder"] = "true"
        return option

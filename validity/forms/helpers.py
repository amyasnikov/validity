from typing import Sequence

from django.forms import ChoiceField, Select


class SelectWithPlaceholder(Select):
    def __init__(self, attrs=None, choices=()) -> None:
        super().__init__(attrs, choices)
        self.attrs["class"] = "netbox-static-select"

    def create_option(self, name, value, label, selected, index: int, subindex=..., attrs=...):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if index == 0:
            option["attrs"]["data-placeholder"] = "true"
        return option


class PlaceholderChoiceField(ChoiceField):
    def __init__(self, *, placeholder: str, **kwargs) -> None:
        kwargs["choices"] = (("", placeholder),) + tuple(kwargs["choices"])
        kwargs["widget"] = SelectWithPlaceholder()
        super().__init__(**kwargs)


class ExcludeMixin:
    def __init__(self, *args, exclude: Sequence[str] = (), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in exclude:
            self.fields.pop(field, None)

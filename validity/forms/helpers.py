from django.forms import ChoiceField
from utilities.forms import StaticSelect


class SelectWithPlaceholder(StaticSelect):
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

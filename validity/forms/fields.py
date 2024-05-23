from typing import Any

from django.forms import ChoiceField, JSONField

from validity.fields import EncryptedDict
from .widgets import SelectWithPlaceholder


class IntegerChoiceField(ChoiceField):
    def to_python(self, value: Any | None) -> Any | None:
        if value is not None:
            value = int(value)
        return value


class EncryptedDictField(JSONField):
    def to_python(self, value: Any) -> Any:
        value = super().to_python(value)
        if isinstance(value, dict):
            value = EncryptedDict(value)
        return value


class PlaceholderChoiceField(ChoiceField):
    def __init__(self, *, placeholder: str | None = None, **kwargs) -> None:
        placeholder = placeholder or kwargs["label"]
        kwargs["choices"] = (("", placeholder),) + tuple(kwargs["choices"])
        kwargs["widget"] = SelectWithPlaceholder()
        super().__init__(**kwargs)

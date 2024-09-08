import operator
from abc import ABC, abstractmethod
from typing import Any

from django.forms import ChoiceField, JSONField
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField

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


class ModelPropertyMixin(ABC):
    """
    Supplies model's field (property) instead of model itself
    """

    def __init__(self, *args, property_name: str = "pk", **kwargs):
        super().__init__(*args, **kwargs)
        self.property_name = property_name

    def clean(self, value):
        val = super().clean(value)
        return self.extract_property(val) if val is not None else None

    @abstractmethod
    def extract_property(self, value): ...


class DynamicModelChoicePropertyField(ModelPropertyMixin, DynamicModelChoiceField):
    def extract_property(self, value):
        return operator.attrgetter(self.property_name)(value)


class DynamicModelMultipleChoicePropertyField(ModelPropertyMixin, DynamicModelMultipleChoiceField):
    def extract_property(self, value):
        return [operator.attrgetter(self.property_name)(item) for item in value]

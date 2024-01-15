import json
from typing import Any, Sequence

from django.forms import ChoiceField, JSONField, Select
from utilities.forms import get_field_value

from validity.fields import EncryptedDict


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


class SubformMixin:
    main_fieldsets: Sequence[tuple[str, Sequence]]

    @property
    def type_field_name(self):
        return self.instance.subform_type_field

    @property
    def json_field_name(self):
        return self.instance.subform_json_field

    @property
    def json_field_value(self):
        if self.json_field_name in self.initial:
            return json.loads(self.initial[self.json_field_name])
        return getattr(self.instance, self.json_field_name)

    @json_field_value.setter
    def json_field_value(self, value):
        setattr(self.instance, self.json_field_name, value)

    @property
    def fieldset_title(self):
        return self.instance._meta.get_field(self.json_field_name).verbose_name

    @property
    def fieldsets(self):
        field_sets = list(self.main_fieldsets)
        if self.subform:
            field_sets.append((self.fieldset_title, self.subform.fields.keys()))
        return field_sets

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subform = None
        type_field_value = get_field_value(self, self.type_field_name)
        if type_field_value:
            setattr(self.instance, self.type_field_name, type_field_value)
            subform_cls = getattr(self.instance, self.json_field_name + "_form")
            self.subform = subform_cls(self.json_field_value)
            self.fields |= self.subform.fields
            self.initial |= self.subform.data

    def save(self, commit=True):
        json_field = {}
        if self.subform:
            for name in self.fields:
                if name in self.subform.fields:
                    json_field[name] = self.cleaned_data[name]
            self.json_field_value = json_field
        return super().save(commit)

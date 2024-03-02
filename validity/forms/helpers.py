import json
from contextlib import suppress
from typing import Any, Literal, Sequence

from django.forms import ChoiceField, JSONField, Select, Textarea
from utilities.forms import get_field_value

from validity.fields import EncryptedDict


class PrettyJSONWidget(Textarea):
    def __init__(self, attrs=None, indent=2) -> None:
        super().__init__(attrs)
        self.attrs.setdefault("style", "font-family:monospace")
        self.indent = indent

    def format_value(self, value: Any) -> str | None:
        with suppress(Exception):
            return json.dumps(json.loads(value), indent=self.indent)
        return super().format_value(value)


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
    main_fieldsets: Sequence[tuple[str, Sequence] | Literal["__subform__"]]

    @property
    def json_field_name(self) -> str:
        return self.instance.subform_json_field

    @property
    def json_field_value(self) -> dict:
        if self.data:
            return {k: v for k, v in self.data.items() if k in self.instance.subform_cls.base_fields}
        if value := self.initial.get(self.json_field_name):
            return json.loads(value)
        return self.instance.subform_json

    @property
    def fieldset_title(self):
        return self.instance._meta.get_field(self.json_field_name).verbose_name

    @property
    def fieldsets(self):
        if not self.subform or not self.subform.fields:
            return [fs for fs in self.main_fieldsets if fs != "__subform__"]
        field_sets = list(self.main_fieldsets)
        try:
            subforms_idx = field_sets.index("__subform__")
        except ValueError:
            field_sets.append(None)
            subforms_idx = -1
        field_sets[subforms_idx] = (self.fieldset_title, self.subform.fields.keys())
        return field_sets

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subform = None
        type_field_value = get_field_value(self, self.instance.subform_type_field)
        if type_field_value:
            self.instance.subform_type = type_field_value
            self.subform = self.instance.subform_cls(self.json_field_value)
            self.fields |= self.subform.fields
            self.initial |= self.subform.data

    def save(self, commit=True):
        json_field = {}
        if self.subform:
            for name in self.fields:
                if name in self.subform.fields:
                    json_field[name] = self.cleaned_data[name]
            self.instance.subform_json = json_field
        return super().save(commit)

    def clean(self):
        cleaned_data = super().clean()
        if self.subform:
            for field, error in self.subform.errors.items():
                self.add_error(field, error)
        return cleaned_data

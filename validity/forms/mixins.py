import json
from typing import Annotated, Literal, Sequence

from utilities.forms import get_field_value
from utilities.forms.fields import DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet

from validity import di, models


class AddM2MPlaceholderFormMixin:
    def __init__(self, *args, add_m2m_placeholder=False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not add_m2m_placeholder:
            return
        for field in self.fields.values():
            if isinstance(field, DynamicModelMultipleChoiceField):
                field.widget.attrs["placeholder"] = field.label


class ExcludeMixin:
    def __init__(self, *args, exclude: Sequence[str] = (), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in exclude:
            self.fields.pop(field, None)


class PollerCleanMixin:
    @di.inject
    def clean(self, command_types: Annotated[dict[str, list[str]], "PollerChoices.command_types"]):
        connection_type = self.cleaned_data.get("connection_type") or get_field_value(self, "connection_type")
        models.Poller.validate_commands(self.cleaned_data.get("commands", []), command_types, connection_type)
        return super().clean()


class SubformMixin:
    main_fieldsets: Sequence[FieldSet | Literal["__subform__"]]

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
        field_sets[subforms_idx] = FieldSet(*self.subform.fields.keys(), name=self.fieldset_title)
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
        if self.subform:
            self.instance.subform_json = self.subform.data_for_saving
        return super().save(commit)

    def clean(self):
        cleaned_data = super().clean()
        if self.subform:
            for field, error in self.subform.errors.items():
                self.add_error(field, error)
        return cleaned_data

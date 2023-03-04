from dcim.models import Device
from django.forms import Form, ChoiceField
from django.utils.translation import gettext_lazy as _
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, StaticSelect
from utilities.forms.fields import DynamicModelMultipleChoiceField


class SelectWithPlaceholder(StaticSelect):
    def create_option(self, name, value, label, selected, index: int, subindex=..., attrs=...):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if index == 0:
            option['attrs']['data-placeholder'] = 'true'
        return option


class PlaceholderChoiceField(ChoiceField):
    def __init__(self, *, placeholder: str, **kwargs) -> None:
        kwargs['choices'] = (('', placeholder),) + tuple(kwargs['choices'])
        kwargs['widget'] = SelectWithPlaceholder()
        super().__init__(**kwargs)


class TestResultFilterForm(Form):
    device_id = DynamicModelMultipleChoiceField(
        label=_("Device"),
        queryset=Device.objects.all(),
        required=False,
    )
    latest = PlaceholderChoiceField(required=False, placeholder=_('Latest'), choices=BOOLEAN_WITH_BLANK_CHOICES[1:])
    passed = PlaceholderChoiceField(required=False, placeholder=_('Passed'), choices=BOOLEAN_WITH_BLANK_CHOICES[1:],)

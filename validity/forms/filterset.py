from dcim.models import Device
from django.forms import Form
from django.utils.translation import gettext_lazy as _
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField

from .helpers import PlaceholderChoiceField


class TestResultFilterForm(Form):
    device_id = DynamicModelMultipleChoiceField(
        label=_("Device"),
        queryset=Device.objects.all(),
        required=False,
    )
    latest = PlaceholderChoiceField(required=False, placeholder=_("Latest"), choices=BOOLEAN_WITH_BLANK_CHOICES[1:])
    passed = PlaceholderChoiceField(
        required=False,
        placeholder=_("Passed"),
        choices=BOOLEAN_WITH_BLANK_CHOICES[1:],
    )

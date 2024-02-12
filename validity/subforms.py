"""
Subforms are needed to
    1. Render part of the main form for JSON Field
    2. Validate JSON Field
"""
import xml.etree.ElementTree as ET

from django import forms
from django.utils.translation import gettext_lazy as _
from utilities.forms import BootstrapMixin

from validity.choices import JSONAPIMethodChoices
from validity.utils.misc import reraise


class CLICommandForm(BootstrapMixin, forms.Form):
    cli_command = forms.CharField(label=_("CLI Command"))


class JSONAPICommandForm(BootstrapMixin, forms.Form):
    method = forms.ChoiceField(label=_("Method"), initial="GET", choices=JSONAPIMethodChoices.choices)
    url_path = forms.CharField(label=_("URL Path"))
    jq_query = forms.CharField(
        label=_("JQ Query"), required=False, help_text=_("Process API answer with this JQ expression")
    )
    body = forms.JSONField(
        label=_("Body"),
        required=False,
        help_text=_("Enter data in JSON format. You can use Jinja2 expressions as values."),
    )


class NetconfCommandForm(BootstrapMixin, forms.Form):
    rpc = forms.CharField(label=_("RPC"), widget=forms.Textarea(attrs={"placeholder": "<get-config/>"}))

    def clean_rpc(self):
        rpc = self.cleaned_data["rpc"]
        with reraise(Exception, forms.ValidationError, {"rpc": "Invalid XML"}):
            ET.fromstring(rpc)
        return rpc

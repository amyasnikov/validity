"""
Subforms are needed to
    1. Render part of the main form for JSON Field
    2. Validate JSON Field
"""

import textwrap
import xml.etree.ElementTree as ET

from django import forms
from django.utils.translation import gettext_lazy as _
from utilities.forms import BootstrapMixin

from validity.choices import JSONAPIMethodChoices
from validity.utils.json import jq
from validity.utils.misc import reraise


class BaseSubform(BootstrapMixin, forms.Form):
    def clean(self):
        if self.data.keys() - self.base_fields.keys():
            allowed_fields = ", ".join(self.base_fields.keys())
            raise forms.ValidationError(_("Only these keys are allowed: %(fields)s"), params={"fields": allowed_fields})
        return self.cleaned_data


# Command Subforms


class CLICommandForm(BaseSubform):
    cli_command = forms.CharField(label=_("CLI Command"))


class JSONAPICommandForm(BaseSubform):
    method = forms.ChoiceField(label=_("Method"), initial="GET", choices=JSONAPIMethodChoices.choices)
    url_path = forms.CharField(label=_("URL Path"))
    body = forms.JSONField(
        label=_("Body"),
        required=False,
        help_text=_("Enter data in JSON format. You can use Jinja2 expressions as values."),
    )


class NetconfCommandForm(BaseSubform):
    get_config = textwrap.dedent(
        """
        <get-config>
          <source>
            <running/>
          </source>
        </get-config>
        """
    ).lstrip("\n")
    rpc = forms.CharField(label=_("RPC"), widget=forms.Textarea(attrs={"placeholder": get_config}))

    def clean_rpc(self):
        rpc = self.cleaned_data["rpc"]
        with reraise(Exception, forms.ValidationError, {"rpc": "Invalid XML"}):
            ET.fromstring(rpc)
        return rpc


# Serializer Subforms


class SerializerBaseForm(BaseSubform):
    jq_expression = forms.CharField(
        label=_("JQ Expression"),
        required=False,
        help_text=_("Post-process parsing result with this JQ expression"),
        widget=forms.TextInput(attrs={"style": "font-family:monospace"}),
    )

    def clean_jq_expression(self):
        if jq_expression := self.cleaned_data.get("jq_expression"):
            with reraise(Exception, forms.ValidationError, "Invalid JQ Expression"):
                jq.compile(jq_expression)
        return jq_expression


class XMLSerializerForm(SerializerBaseForm):
    drop_attributes = forms.BooleanField(label=_("Drop XML Attributes"), initial=False, required=False)
    requires_template = False


class TTPSerializerForm(SerializerBaseForm):
    requires_template = True


class TEXTFSMSerializerForm(SerializerBaseForm):
    requires_template = True


class RouterOSSerializerForm(BaseSubform):
    requires_template = False


class YAMLSerializerForm(SerializerBaseForm):
    requires_template = False

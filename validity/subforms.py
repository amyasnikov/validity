"""
Subforms are needed to
    1. Render part of the main form for JSON Field
    2. Validate JSON Field
"""

import json
import textwrap
import xml.etree.ElementTree as ET

from django import forms
from django.forms.widgets import Textarea
from django.utils.translation import gettext_lazy as _

from validity.choices import JSONAPIMethodChoices
from validity.fields.encrypted import EncryptedDict
from validity.utils.json import jq
from validity.utils.misc import reraise


class SensitiveMixin:
    """
    Allows to hide encrypted values in DetailView
    """

    sensitive_fields: set[str] = {}

    placeholder: str = "*********"

    @classmethod
    def _sensitive_value(cls, field):
        if field.name in cls.sensitive_fields:
            return cls.placeholder
        return json.dumps(field.data) if isinstance(data := field.data, (dict, list)) else data

    def rendered_parameters(self):
        for field in self:
            yield field.label, self._sensitive_value(field)


class BaseSubform(SensitiveMixin, forms.Form):
    def __init__(self, data=None, *args, **kwargs):
        if isinstance(data, EncryptedDict):
            data = data.encrypted
        super().__init__(data, *args, **kwargs)

    def clean(self):
        if self.data.keys() - self.base_fields.keys():
            allowed_fields = ", ".join(self.base_fields.keys())
            raise forms.ValidationError(_("Only these keys are allowed: %(fields)s"), params={"fields": allowed_fields})
        return self.cleaned_data

    @property
    def data_for_saving(self):
        return self.cleaned_data


class PlainSubform(BaseSubform):
    """
    Displays all the params inside one JSONField called "params"
    params field MUST be defined in a sublcass
    """

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            if data.keys() != {"params"}:
                data = type(data)({"params": dict(data)})
        super().__init__(data, *args, **kwargs)

    def clean_params(self):
        params = self.cleaned_data["params"]
        if not isinstance(params, dict):
            raise forms.ValidationError("Value must be JSON object")
        return params

    @property
    def data_for_saving(self):
        return self.cleaned_data["params"]

    def rendered_parameters(self):
        for key, value in self.data["params"].items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            yield key, value


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


class CustomCommandForm(PlainSubform):
    params = forms.JSONField(
        label=_("Command Parameters"),
        help_text=_("JSON-encoded params"),
        widget=Textarea(attrs={"style": "font-family:monospace"}),
        initial=dict,
    )


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


# Backup Forms


class GitBackupForm(BaseSubform):
    username = forms.CharField(label=_("Username"), help_text=_("Required for HTTP authentication"))
    password = forms.CharField(
        label=_("Password"), help_text=_("Required for HTTP authentication. Will be encrypted before saving")
    )
    branch = forms.CharField(required=False, label=_("Branch"))

    sensitive_fields = {"password"}


class S3BackupForm(BaseSubform):
    aws_access_key_id = forms.CharField(label=_("AWS access key ID"))
    aws_secret_access_key = forms.CharField(
        label=_("AWS secret access key"), help_text=_("Will be encrypted before saving")
    )
    archive = forms.BooleanField(required=False, help_text=_("Compress the repo into zip archive before uploading"))

    sensitive_fields = {"aws_secret_access_key"}

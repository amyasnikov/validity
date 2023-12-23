"""
Subforms are needed to
    1. Render part of the main form for JSON Field
    2. Validate JSON Field
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from utilities.forms import BootstrapMixin


class CLICommandForm(BootstrapMixin, forms.Form):
    cli_command = forms.CharField(label=_("CLI Command"))

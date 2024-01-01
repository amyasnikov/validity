from core.forms.mixins import SyncedDataMixin
from dcim.models import DeviceType, Location, Manufacturer, Platform, Site
from django.forms import CharField, Textarea, ValidationError
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from netbox.forms import NetBoxModelForm
from tenancy.models import Tenant
from utilities.forms import get_field_value
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.widgets import HTMXSelect

from validity import models
from .helpers import SubformMixin


class ComplianceTestForm(SyncedDataMixin, NetBoxModelForm):
    selectors = DynamicModelMultipleChoiceField(queryset=models.ComplianceSelector.objects.all())
    expression = CharField(required=False, widget=Textarea(attrs={"style": "font-family:monospace"}))

    fieldsets = (
        (_("Compliance Test"), ("name", "severity", "description", "selectors", "tags")),
        (_("Expression from Data Source"), ("data_source", "data_file")),
        (_("Expression from DB"), ("expression",)),
    )

    class Meta:
        model = models.ComplianceTest
        fields = ("name", "severity", "description", "expression", "selectors", "data_source", "data_file", "tags")


class ComplianceSelectorForm(NetBoxModelForm):
    tag_filter = DynamicModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)
    manufacturer_filter = DynamicModelMultipleChoiceField(queryset=Manufacturer.objects.all(), required=False)
    type_filter = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(), required=False, label=_("Device Type Filter")
    )
    platform_filter = DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    location_filter = DynamicModelMultipleChoiceField(queryset=Location.objects.all(), required=False)
    site_filter = DynamicModelMultipleChoiceField(queryset=Site.objects.all(), required=False)
    tenant_filter = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)

    fieldsets = (
        (_("Common"), ("name", "tags")),
        (_("Dynamic Pairs"), ("dynamic_pairs", "dp_tag_prefix")),
        (
            _("Filters"),
            (
                "filter_operation",
                "name_filter",
                "type_filter",
                "location_filter",
                "manufacturer_filter",
                "platform_filter",
                "site_filter",
                "status_filter",
                "tag_filter",
                "tenant_filter",
            ),
        ),
    )

    class Meta:
        model = models.ComplianceSelector
        fields = (
            "name",
            "filter_operation",
            "dynamic_pairs",
            "dp_tag_prefix",
            "name_filter",
            "tag_filter",
            "manufacturer_filter",
            "type_filter",
            "platform_filter",
            "status_filter",
            "location_filter",
            "site_filter",
            "tenant_filter",
            "tags",
        )

    def clean(self):
        result = super().clean()
        if not self.cleaned_data.keys() & models.ComplianceSelector.filters.keys():
            raise ValidationError(_("You must specify at least one filter"))
        return result


class SerializerForm(SyncedDataMixin, NetBoxModelForm):
    template = CharField(required=False, widget=Textarea(attrs={"style": "font-family:monospace"}))

    fieldsets = (
        (_("Serializer"), ("name", "extraction_method", "tags")),
        (_("Template from Data Source"), ("data_source", "data_file")),
        (_("Template from DB"), ("template",)),
    )

    class Meta:
        model = models.Serializer
        fields = ("name", "extraction_method", "template", "data_source", "data_file", "tags")


class NameSetForm(NetBoxModelForm):
    tests = DynamicModelMultipleChoiceField(queryset=models.ComplianceTest.objects.all(), required=False)
    definitions = CharField(required=False, widget=Textarea(attrs={"style": "font-family:monospace"}))

    fieldsets = (
        (_("Name Set"), ("name", "description", "_global", "tests", "tags")),
        (_("Definitions from Data Source"), ("data_source", "data_file")),
        (_("Definitions from DB"), ("definitions",)),
    )

    class Meta:
        model = models.NameSet
        fields = ("name", "description", "_global", "tests", "definitions", "data_source", "data_file", "tags")


class PollerForm(NetBoxModelForm):
    commands = DynamicModelMultipleChoiceField(queryset=models.Command.objects.all())

    class Meta:
        model = models.Poller
        fields = ("name", "commands", "connection_type", "public_credentials", "private_credentials", "tags")
        widgets = {
            "public_credentials": Textarea(attrs={"style": "font-family:monospace"}),
            "private_credentials": Textarea(attrs={"style": "font-family:monospace"}),
        }

    def clean(self):
        connection_type = self.cleaned_data.get("connection_type") or get_field_value(self, "connection_type")
        models.Poller.validate_commands(connection_type, self.cleaned_data["commands"])
        return super().clean()


class CommandForm(SubformMixin, NetBoxModelForm):
    serializer = DynamicModelChoiceField(queryset=models.Serializer.objects.all(), required=False)

    main_fieldsets = [
        (_("Command"), ("name", "label", "type", "retrieves_config", "serializer", "tags")),
    ]

    class Meta:
        model = models.Command
        fields = ("name", "label", "type", "retrieves_config", "serializer", "tags")
        widgets = {"type": HTMXSelect()}

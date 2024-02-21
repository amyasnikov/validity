from core.forms.mixins import SyncedDataMixin
from dcim.models import DeviceType, Location, Manufacturer, Platform, Site
from django.forms import CharField, ChoiceField, Select, Textarea, ValidationError
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from netbox.forms import NetBoxModelForm
from tenancy.models import Tenant
from utilities.forms import add_blank_choice, get_field_value
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.widgets import HTMXSelect

from validity import models
from validity.choices import ConnectionTypeChoices
from .helpers import PrettyJSONWidget, SubformMixin


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


class SerializerForm(SyncedDataMixin, SubformMixin, NetBoxModelForm):
    template = CharField(required=False, widget=Textarea(attrs={"style": "font-family:monospace"}))

    main_fieldsets = (
        (_("Serializer"), ("name", "extraction_method", "tags")),
        "__subform__",
        (_("Template from Data Source"), ("data_source", "data_file")),
        (_("Template from DB"), ("template",)),
    )

    @property
    def fieldsets(self):
        fs = super().fieldsets
        if not self.subform or not self.subform.requires_template:
            fs = fs[:-2]  # drop "Template from..." fieldsets
        return fs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.subform or not self.subform.requires_template:
            for field in ["template", "data_source", "data_file"]:
                del self.fields[field]

    class Meta:
        model = models.Serializer
        fields = ("name", "extraction_method", "template", "data_source", "data_file", "tags")
        widgets = {"extraction_method": HTMXSelect()}


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
    connection_type = ChoiceField(
        choices=add_blank_choice(ConnectionTypeChoices.choices), widget=Select(attrs={"id": "connection_type_select"})
    )
    commands = DynamicModelMultipleChoiceField(queryset=models.Command.objects.all())

    class Meta:
        model = models.Poller
        fields = ("name", "commands", "connection_type", "public_credentials", "private_credentials", "tags")
        widgets = {
            "public_credentials": PrettyJSONWidget(),
            "private_credentials": PrettyJSONWidget(),
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

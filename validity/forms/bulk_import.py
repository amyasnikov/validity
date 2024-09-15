from core.models import DataFile, DataSource
from dcim.choices import DeviceStatusChoices
from dcim.models import DeviceType, Location, Manufacturer, Platform, Site
from django.forms import Form
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from netbox.forms import NetBoxModelImportForm
from tenancy.models import Tenant
from utilities.forms.fields import CSVChoiceField, CSVModelChoiceField, CSVModelMultipleChoiceField, JSONField

from validity import choices, models
from validity.api.helpers import SubformValidationMixin
from .mixins import PollerCleanMixin


class SubFormMixin(SubformValidationMixin):
    def clean(self):
        validated_data = {k: v for k, v in self.cleaned_data.items() if not k.startswith("_")}
        self.validate(validated_data)
        return self.cleaned_data


class DataSourceMixin(Form):
    data_source = CSVModelChoiceField(
        queryset=DataSource.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Data Source"),
    )
    data_file = CSVModelChoiceField(
        queryset=DataFile.objects.all(),
        required=False,
        to_field_name="path",
        help_text=_("File from Data Source"),
    )

    def clean_data_source(self):
        """
        Filters data file by known data source
        data_source MUST go before data_file in Meta.fields
        """
        data_source = self.cleaned_data["data_source"]
        if data_source is not None:
            datafile_field = self.fields["data_file"]
            datafile_field.queryset = datafile_field.queryset.filter(source=data_source)
        return data_source


class ComplianceTestImportForm(DataSourceMixin, NetBoxModelImportForm):
    severity = CSVChoiceField(choices=choices.SeverityChoices.choices, help_text=_("Test Severity"))
    selectors = CSVModelMultipleChoiceField(
        queryset=models.ComplianceSelector.objects.all(),
        to_field_name="name",
        help_text=_("Compliance Selector names separated by commas, encased with double quotes"),
    )

    class Meta:
        model = models.ComplianceTest
        fields = ("name", "severity", "description", "selectors", "expression", "data_source", "data_file", "tags")


class NameSetImportForm(DataSourceMixin, NetBoxModelImportForm):
    tests = CSVModelMultipleChoiceField(
        queryset=models.ComplianceTest.objects.all(),
        to_field_name="name",
        help_text=_("Compliance Test names separated by commas, encased with double quotes"),
        required=False,
    )

    class Meta:
        model = models.NameSet
        fields = ("name", "description", "_global", "tests", "definitions", "data_source", "data_file")

    def __init__(self, *args, headers=None, **kwargs):
        base_fields = {"global": self.base_fields["_global"]} | self.base_fields
        base_fields.pop("_global")
        self.base_fields = base_fields
        super().__init__(*args, headers=headers, **kwargs)

    def save(self, commit=True) -> choices.Any:
        if (_global := self.cleaned_data.get("global")) is not None:
            self.instance._global = _global
        return super().save(commit)


class SerializerImportForm(SubFormMixin, DataSourceMixin, NetBoxModelImportForm):
    extraction_method = CSVChoiceField(
        choices=choices.ExtractionMethodChoices.choices, help_text=_("Extraction Method")
    )
    parameters = JSONField(
        help_text=_(
            "JSON-encoded Serializer parameters depending on Extraction Method value. "
            "See REST API to check for specific keys/values"
        )
    )

    class Meta:
        model = models.Serializer
        fields = ("name", "extraction_method", "template", "parameters", "data_source", "data_file")


class ComplianceSelectorImportForm(NetBoxModelImportForm):
    filter_operation = CSVChoiceField(
        choices=choices.BoolOperationChoices.choices, help_text=_("Filter Join Operation")
    )
    tag_filter = CSVModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        to_field_name="slug",
        help_text=_("Tag slugs separated by commas, encased with double quotes"),
        required=False,
    )
    manufacturer_filter = CSVModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(),
        to_field_name="slug",
        help_text=_("Manufacturer slugs separated by commas, encased with double quotes"),
        required=False,
    )
    type_filter = CSVModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        to_field_name="slug",
        help_text=_("Device Type slugs separated by commas, encased with double quotes"),
        required=False,
    )
    platform_filter = CSVModelMultipleChoiceField(
        queryset=Platform.objects.all(),
        to_field_name="slug",
        help_text=_("Platform slugs separated by commas, encased with double quotes"),
        required=False,
    )
    status_filter = CSVChoiceField(choices=DeviceStatusChoices, help_text=_("Device Status Filter"), required=False)
    location_filter = CSVModelMultipleChoiceField(
        queryset=Location.objects.all(),
        to_field_name="slug",
        help_text=_("Location slugs separated by commas, encased with double quotes"),
        required=False,
    )
    site_filter = CSVModelMultipleChoiceField(
        queryset=Site.objects.all(),
        to_field_name="slug",
        help_text=_("Site slugs separated by commas, encased with double quotes"),
        required=False,
    )
    tenant_filter = CSVModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name="slug",
        help_text=("Tenant slugs separated by commas, encased with double quotes"),
        required=False,
    )
    dynamic_pairs = CSVChoiceField(
        choices=choices.DynamicPairsChoices.choices, required=False, help_text=_("Dynamic Pairs")
    )

    class Meta:
        model = models.ComplianceSelector
        fields = (
            "name",
            "filter_operation",
            "name_filter",
            "tag_filter",
            "manufacturer_filter",
            "type_filter",
            "platform_filter",
            "status_filter",
            "location_filter",
            "site_filter",
            "tenant_filter",
            "dynamic_pairs",
            "dp_tag_prefix",
        )


class CommandImportForm(SubFormMixin, NetBoxModelImportForm):
    serializer = CSVModelChoiceField(
        queryset=models.Serializer.objects.all(), to_field_name="name", help_text=_("Serializer"), required=False
    )
    type = CSVChoiceField(choices=choices.CommandTypeChoices.choices, help_text=_("Command Type"))
    parameters = JSONField(
        help_text=_(
            "JSON-encoded Command parameters depending on Type value. See REST API to check for specific keys/values"
        )
    )

    class Meta:
        model = models.Command
        fields = ("name", "label", "retrieves_config", "serializer", "type", "parameters")


class PollerImportForm(PollerCleanMixin, NetBoxModelImportForm):
    connection_type = CSVChoiceField(choices=choices.ConnectionTypeChoices.choices, help_text=_("Connection Type"))
    commands = CSVModelMultipleChoiceField(
        queryset=models.Command.objects.all(),
        to_field_name="label",
        help_text=_("Command labels separated by commas, encased with double quotes"),
    )
    public_credentials = JSONField(help_text=_("Public Credentials"), required=False)
    private_credentials = JSONField(
        help_text=_(
            "Private Credentials. ATTENTION: encryption depends on Django's SECRET_KEY var, "
            "values from another NetBox may not be decrypted properly"
        ),
        required=False,
    )

    def full_clean(self) -> None:
        return super().full_clean()

    class Meta:
        model = models.Poller
        fields = ("name", "connection_type", "commands", "public_credentials", "private_credentials")

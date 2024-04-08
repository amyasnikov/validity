from core.models import DataSource
from dcim.models import Device, DeviceRole, DeviceType, Location, Manufacturer, Platform, Site
from django.forms import CharField, Form, NullBooleanField, Select
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.models import Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField

from validity import models
from validity.choices import (
    BoolOperationChoices,
    CommandTypeChoices,
    ConnectionTypeChoices,
    DeviceGroupByChoices,
    DynamicPairsChoices,
    ExtractionMethodChoices,
    SeverityChoices,
)
from .helpers import ExcludeMixin, PlaceholderChoiceField


class DeviceReportFilterForm(ExcludeMixin, Form):
    q = CharField(label=_("Device Search"), required=False)
    compliance_passed = PlaceholderChoiceField(
        required=False, placeholder=_("Compliance Passed"), choices=BOOLEAN_WITH_BLANK_CHOICES[1:]
    )
    severity_ge = PlaceholderChoiceField(
        required=False, placeholder=_("Minimum Severity"), choices=SeverityChoices.choices[1:]
    )


class DataSourceDevicesFilterForm(Form):
    q = CharField(label=_("Device Search"), required=False)
    tenant_id = DynamicModelMultipleChoiceField(label=_("Tenant"), queryset=Tenant.objects.all(), required=False)


class TestResultFilterForm(ExcludeMixin, Form):
    latest = PlaceholderChoiceField(required=False, placeholder=_("Latest"), choices=BOOLEAN_WITH_BLANK_CHOICES[1:])
    passed = PlaceholderChoiceField(
        required=False,
        placeholder=_("Passed"),
        choices=BOOLEAN_WITH_BLANK_CHOICES[1:],
    )
    severity = PlaceholderChoiceField(required=False, placeholder=_("Severity"), choices=SeverityChoices.choices)
    device_id = DynamicModelMultipleChoiceField(
        label=_("Device"),
        queryset=Device.objects.all(),
        required=False,
    )
    test_id = DynamicModelMultipleChoiceField(
        label=_("Test"), queryset=models.ComplianceTest.objects.all(), required=False
    )
    report_id = DynamicModelMultipleChoiceField(
        label=_("Report"),
        queryset=models.ComplianceReport.objects.all(),
        required=False,
    )
    selector_id = DynamicModelMultipleChoiceField(
        label=_("Selector"), queryset=models.ComplianceSelector.objects.all(), required=False
    )
    device_type_id = DynamicModelMultipleChoiceField(
        required=False, label=("Device Type"), queryset=DeviceType.objects.all()
    )
    manufacturer_id = DynamicModelMultipleChoiceField(
        required=False, label=_("Manufacturer"), queryset=Manufacturer.objects.all()
    )
    device_role_id = DynamicModelMultipleChoiceField(
        required=False, label=_("Device Role"), queryset=DeviceRole.objects.all()
    )
    tenant_id = DynamicModelMultipleChoiceField(required=False, label=("Tenant"), queryset=Tenant.objects.all())
    platform_id = DynamicModelMultipleChoiceField(required=False, label=_("Platform"), queryset=Platform.objects.all())
    location_id = DynamicModelMultipleChoiceField(required=False, label=_("Location"), queryset=Location.objects.all())
    site_id = DynamicModelMultipleChoiceField(required=False, label=_("Site"), queryset=Site.objects.all())
    test_tag_id = DynamicModelMultipleChoiceField(required=False, label=_("Test Tags"), queryset=Tag.objects.all())


class ComplianceTestResultFilterForm(TestResultFilterForm, NetBoxModelFilterSetForm):
    model = models.ComplianceTestResult
    fieldsets = (
        [_("Common"), ("latest", "passed", "selector_id")],
        [_("Test"), ("severity", "test_id", "report_id", "test_tag_id")],
        [
            _("Device"),
            (
                "device_id",
                "device_type_id",
                "manufacturer_id",
                "device_role_id",
                "tenant_id",
                "platform_id",
                "location_id",
                "site_id",
            ),
        ],
    )


class ReportGroupByForm(Form):
    group_by = PlaceholderChoiceField(
        label=_("Group results by"),
        placeholder=_("Group results by"),
        required=False,
        choices=DeviceGroupByChoices.choices,
    )


class StateSelectForm(Form):
    state_item = PlaceholderChoiceField(
        label=_("State Item"), placeholder=_("Select State Item"), required=False, choices=[("config", "config")]
    )

    def __init__(self, *args, state, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["state_item"].choices += [
            (item.name, item.name) for item in state.values() if item.name != "config"
        ]


class NameSetFilterForm(NetBoxModelFilterSetForm):
    model = models.NameSet
    name = CharField(required=False)
    _global = NullBooleanField(label=_("Global"), required=False, widget=Select(choices=BOOLEAN_WITH_BLANK_CHOICES))
    datasource_id = DynamicModelMultipleChoiceField(
        label=_("Data Source"), queryset=DataSource.objects.all(), required=False
    )


class ComplianceSelectorFilterForm(NetBoxModelFilterSetForm):
    model = models.ComplianceSelector
    name = CharField(required=False)
    filter_operation = PlaceholderChoiceField(
        required=False, placeholder=_("Filter Operation"), choices=BoolOperationChoices.choices
    )
    dynamic_pairs = PlaceholderChoiceField(
        required=False, placeholder=_("Dynamic Pairs"), choices=DynamicPairsChoices.choices
    )


class SerializerFilterForm(NetBoxModelFilterSetForm):
    model = models.Serializer
    name = CharField(required=False)
    extraction_method = PlaceholderChoiceField(
        required=False, placeholder=_("Extraction Method"), choices=ExtractionMethodChoices.choices
    )
    datasource_id = DynamicModelMultipleChoiceField(
        label=_("Data Source"), queryset=DataSource.objects.all(), required=False
    )


class ComplianceTestFilterForm(NetBoxModelFilterSetForm):
    model = models.ComplianceTest
    name = CharField(required=False)
    severity = PlaceholderChoiceField(required=False, placeholder=_("Severity"), choices=SeverityChoices.choices)
    selector_id = DynamicModelMultipleChoiceField(
        label=_("Selector"), queryset=models.ComplianceSelector.objects.all(), required=False
    )
    datasource_id = DynamicModelMultipleChoiceField(
        label=_("Data Source"), queryset=DataSource.objects.all(), required=False
    )


class PollerFilterForm(NetBoxModelFilterSetForm):
    model = models.Poller
    name = CharField(required=False)
    connection_type = PlaceholderChoiceField(
        required=False, placeholder=_("Connection Type"), choices=ConnectionTypeChoices.choices
    )


class CommandFilterForm(NetBoxModelFilterSetForm):
    model = models.Command
    name = CharField(required=False)
    label = CharField(required=False)
    type = PlaceholderChoiceField(required=False, placeholder=_("Type"), choices=CommandTypeChoices.choices)
    retrieves_config = NullBooleanField(
        label=_("Global"), required=False, widget=Select(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    serializer_id = DynamicModelMultipleChoiceField(
        label=_("Serializer"), queryset=models.Serializer.objects.all(), required=False
    )
    poller_id = DynamicModelMultipleChoiceField(label=_("Poller"), queryset=models.Poller.objects.all(), required=False)

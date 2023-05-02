from dcim.models import Device, DeviceRole, DeviceType, Location, Manufacturer, Platform, Site
from django.forms import CharField, Form, NullBooleanField, Select
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.models import Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField

from validity import models
from validity.choices import (
    BoolOperationChoices,
    ConfigExtractionChoices,
    DeviceGroupByChoices,
    DynamicPairsChoices,
    SeverityChoices,
)
from .helpers import ExcludeMixin, PlaceholderChoiceField


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


class ComplianceTestResultFilterForm(TestResultFilterForm, NetBoxModelFilterSetForm):
    model = models.ComplianceTestResult
    fieldsets = (
        [_("Common"), ("latest", "passed", "selector_id")],
        [_("Test"), ("severity", "test_id", "report_id")],
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


class NameSetFilterForm(NetBoxModelFilterSetForm):
    model = models.NameSet
    name = CharField(required=False)
    _global = NullBooleanField(label=_("Global"), required=False, widget=Select(choices=BOOLEAN_WITH_BLANK_CHOICES))
    repo_id = DynamicModelMultipleChoiceField(
        label=_("Git Repository"), queryset=models.GitRepo.objects.all(), required=False
    )


class GitRepoFilterForm(NetBoxModelFilterSetForm):
    model = models.GitRepo
    name = CharField(required=False)
    default = NullBooleanField(required=False, widget=Select(choices=BOOLEAN_WITH_BLANK_CHOICES))
    username = CharField(required=False)
    branch = CharField(required=False)
    head_hash = CharField(required=False)


class ComplianceSelectorFilterForm(NetBoxModelFilterSetForm):
    model = models.ComplianceSelector
    name = CharField(required=False)
    filter_operation = PlaceholderChoiceField(
        required=False, placeholder=_("Filter Operation"), choices=BoolOperationChoices.choices
    )
    dynamic_pairs = PlaceholderChoiceField(
        required=False, placeholder=_("Dynamic Pairs"), choices=DynamicPairsChoices.choices
    )


class ConfigSerializerFilterForm(NetBoxModelFilterSetForm):
    model = models.ConfigSerializer
    name = CharField(required=False)
    extraction_method = PlaceholderChoiceField(
        required=False, placeholder=_("Extraction Method"), choices=ConfigExtractionChoices.choices
    )
    repo_id = DynamicModelMultipleChoiceField(
        label=_("Git Repository"), queryset=models.GitRepo.objects.all(), required=False
    )


class ComplianceTestFilterForm(NetBoxModelFilterSetForm):
    model = models.ComplianceTest
    name = CharField(required=False)
    severity = PlaceholderChoiceField(required=False, placeholder=_("Severity"), choices=SeverityChoices.choices)
    selector_id = DynamicModelMultipleChoiceField(
        label=_("Selector"), queryset=models.ComplianceSelector.objects.all(), required=False
    )
    repo_id = DynamicModelMultipleChoiceField(
        label=_("Git Repository"), queryset=models.GitRepo.objects.all(), required=False
    )

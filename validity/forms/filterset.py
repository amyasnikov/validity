from dcim.models import Device
from django.forms import CharField, Form, NullBooleanField
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm, StaticSelect
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
from .helpers import PlaceholderChoiceField


class TestResultFilterForm(Form):
    latest = PlaceholderChoiceField(required=False, placeholder=_("Latest"), choices=BOOLEAN_WITH_BLANK_CHOICES[1:])
    passed = PlaceholderChoiceField(
        required=False,
        placeholder=_("Passed"),
        choices=BOOLEAN_WITH_BLANK_CHOICES[1:],
    )
    test__severity = PlaceholderChoiceField(required=False, placeholder=_("Severity"), choices=SeverityChoices.choices)
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

    def __init__(self, *args, exclude: str = "", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if exclude:
            self.fields.pop(exclude, None)


class ComplianceTestResultFilterForm(TestResultFilterForm, NetBoxModelFilterSetForm):
    model = models.ComplianceTestResult


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
    _global = NullBooleanField(
        label=_("Global"), required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    repo_id = DynamicModelMultipleChoiceField(
        label=_("Git Repository"), queryset=models.GitRepo.objects.all(), required=False
    )


class GitRepoFilterForm(NetBoxModelFilterSetForm):
    model = models.GitRepo
    name = CharField(required=False)
    default = NullBooleanField(required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES))
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

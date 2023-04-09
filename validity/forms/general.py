from dcim.models import DeviceType, Location, Manufacturer, Platform, Site
from django.forms import PasswordInput, ValidationError
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from netbox.forms import NetBoxModelForm
from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField

from validity import models


class ComplianceTestForm(NetBoxModelForm):
    selectors = DynamicModelMultipleChoiceField(queryset=models.ComplianceSelector.objects.all())
    repo = DynamicModelChoiceField(queryset=models.GitRepo.objects.all(), required=False, label=_("Git Repository"))

    fieldsets = (
        (_("Compliance Test"), ("name", "severity", "description", "selectors", "tags")),
        (_("Expression from Git"), ("repo", "file_path")),
        (_("Expression from DB"), ("expression",)),
    )

    class Meta:
        model = models.ComplianceTest
        fields = ("name", "severity", "description", "expression", "selectors", "repo", "file_path", "tags")


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

    class Meta:
        model = models.ComplianceSelector
        fields = (
            "name",
            "filter_operation",
            "dynamic_pairs",
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
        super().clean()
        if not self.cleaned_data.keys() & models.ComplianceSelector.filters.keys():
            raise ValidationError(_("You must specify at least one filter"))


class GitRepoForm(NetBoxModelForm):
    password = CharField(widget=PasswordInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["password"].disabled = True

    class Meta:
        model = models.GitRepo
        fields = (
            "name",
            "git_url",
            "web_url",
            "device_config_path",
            "default",
            "username",
            "password",
            "branch",
            "tags",
        )

    def save(self, commit: bool = ...):
        if password := self.cleaned_data.pop("password", None):
            self.instance.password = password
        return super().save(commit)


class ConfigSerializerForm(NetBoxModelForm):
    repo = DynamicModelChoiceField(queryset=models.GitRepo.objects.all(), required=False, label=_("Git Repository"))

    fieldsets = (
        (_("Config Serializer"), ("name", "extraction_method", "tags")),
        (_("Template from Git"), ("repo", "file_path")),
        (_("Template from DB"), ("ttp_template",)),
    )

    class Meta:
        model = models.ConfigSerializer
        fields = ("name", "extraction_method", "ttp_template", "repo", "file_path", "tags")


class NameSetForm(NetBoxModelForm):
    tests = DynamicModelMultipleChoiceField(queryset=models.ComplianceTest.objects.all(), required=False)
    repo = DynamicModelChoiceField(queryset=models.GitRepo.objects.all(), required=False, label=_("Git Repository"))

    fieldsets = (
        (_("Name Set"), ("name", "description", "_global", "tests", "tags")),
        (_("Definitions from Git"), ("repo", "file_path")),
        (_("Definitions from DB"), ("definitions",)),
    )

    class Meta:
        model = models.NameSet
        fields = ("name", "description", "_global", "tests", "definitions", "repo", "file_path", "tags")

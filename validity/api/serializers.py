from typing import Annotated

from core.api.serializers import DataFileSerializer, DataSourceSerializer, JobSerializer
from core.models import DataSource
from dcim.api.serializers import (
    DeviceRoleSerializer,
    DeviceSerializer,
    DeviceTypeSerializer,
    LocationSerializer,
    ManufacturerSerializer,
    PlatformSerializer,
    SiteSerializer,
)
from dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Site
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from extras.api.serializers import TagSerializer
from extras.models import Tag
from netbox.api.fields import SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from tenancy.api.serializers import TenantSerializer
from tenancy.models import Tenant

from validity import di, models
from validity.choices import ExplanationVerbosityChoices
from .helpers import (
    EncryptedDictField,
    FieldsMixin,
    ListQPMixin,
    PrimaryKeyField,
    SubformValidationMixin,
    proxy_factory,
)


NestedDeviceSerializer = proxy_factory(DeviceSerializer, view_name="dcim-api:device-detail")
NestedDataSourceSerializer = proxy_factory(DataSourceSerializer, view_name="core-api:datasource-detail")
NestedDataFileSerializer = proxy_factory(DataFileSerializer, view_name="core-api:datafile-detail")


class ComplianceSelectorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:complianceselector-detail")
    tag_filter = SerializedPKRelatedField(
        serializer=TagSerializer,
        many=True,
        nested=True,
        required=False,
        queryset=Tag.objects.all(),
    )
    manufacturer_filter = SerializedPKRelatedField(
        serializer=ManufacturerSerializer, many=True, nested=True, required=False, queryset=Manufacturer.objects.all()
    )
    type_filter = SerializedPKRelatedField(
        serializer=DeviceTypeSerializer, many=True, nested=True, required=False, queryset=DeviceType.objects.all()
    )
    role_filter = SerializedPKRelatedField(
        serializer=DeviceRoleSerializer, many=True, nested=True, required=False, queryset=DeviceType.objects.all()
    )
    platform_filter = SerializedPKRelatedField(
        serializer=PlatformSerializer, many=True, nested=True, required=False, queryset=Platform.objects.all()
    )
    location_filter = SerializedPKRelatedField(
        serializer=LocationSerializer, many=True, nested=True, required=False, queryset=Location.objects.all()
    )
    site_filter = SerializedPKRelatedField(
        serializer=SiteSerializer, many=True, nested=True, required=False, queryset=Site.objects.all()
    )
    tenant_filter = SerializedPKRelatedField(
        serializer=TenantSerializer, many=True, nested=True, required=False, queryset=Tenant.objects.all()
    )

    class Meta:
        model = models.ComplianceSelector
        fields = (
            "id",
            "url",
            "display",
            "name",
            "filter_operation",
            "name_filter",
            "tag_filter",
            "manufacturer_filter",
            "type_filter",
            "role_filter",
            "platform_filter",
            "status_filter",
            "location_filter",
            "site_filter",
            "tenant_filter",
            "dynamic_pairs",
            "dp_tag_prefix",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")


class ComplianceTestSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetest-detail")
    selectors = SerializedPKRelatedField(
        serializer=ComplianceSelectorSerializer,
        nested=True,
        many=True,
        required=False,
        queryset=models.ComplianceSelector.objects.all(),
    )
    data_source = NestedDataSourceSerializer(required=False)
    data_file = NestedDataFileSerializer(required=False)
    effective_expression = serializers.ReadOnlyField()
    expression = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = models.ComplianceTest
        fields = (
            "id",
            "url",
            "display",
            "name",
            "severity",
            "description",
            "effective_expression",
            "expression",
            "data_source",
            "data_file",
            "selectors",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name", "severity")


class ComplianceReportSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancereport-detail")
    results_url = serializers.SerializerMethodField()
    device_count = serializers.ReadOnlyField()
    test_count = serializers.ReadOnlyField()
    total_passed = serializers.ReadOnlyField()
    total_count = serializers.ReadOnlyField()
    low_passed = serializers.ReadOnlyField()
    low_count = serializers.ReadOnlyField()
    middle_passed = serializers.ReadOnlyField()
    middle_count = serializers.ReadOnlyField()
    high_passed = serializers.ReadOnlyField()
    high_count = serializers.ReadOnlyField()

    class Meta:
        model = models.ComplianceReport
        fields = (
            "id",
            "url",
            "display",
            "device_count",
            "test_count",
            "total_passed",
            "total_count",
            "low_passed",
            "low_count",
            "middle_passed",
            "middle_count",
            "high_passed",
            "high_count",
            "results_url",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display")

    def get_results_url(self, obj) -> str:
        results_url = reverse("plugins-api:validity-api:compliancetestresult-list", request=self.context["request"])
        return results_url + f"?report_id={obj.pk}"


class ComplianceTestResultSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetestresult-detail")
    test = ComplianceTestSerializer(nested=True)
    device = NestedDeviceSerializer()
    dynamic_pair = NestedDeviceSerializer(allow_null=True)
    report = ComplianceReportSerializer(nested=True)

    class Meta:
        model = models.ComplianceTestResult
        fields = (
            "id",
            "url",
            "display",
            "test",
            "device",
            "dynamic_pair",
            "report",
            "passed",
            "explanation",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "passed")


class SerializerSerializer(SubformValidationMixin, NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:serializer-detail")
    template = serializers.CharField(write_only=True, required=False)
    effective_template = serializers.ReadOnlyField()
    data_source = NestedDataSourceSerializer(required=False)
    data_file = NestedDataFileSerializer(required=False)

    class Meta:
        model = models.Serializer
        fields = (
            "id",
            "url",
            "display",
            "name",
            "extraction_method",
            "effective_template",
            "template",
            "data_source",
            "data_file",
            "parameters",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")


class NameSetSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:nameset-detail")
    data_source = NestedDataSourceSerializer(required=False)
    data_file = NestedDataFileSerializer(required=False)
    definitions = serializers.CharField(write_only=True, required=False)
    effective_definitions = serializers.ReadOnlyField()

    class Meta:
        model = models.NameSet
        fields = (
            "id",
            "url",
            "display",
            "name",
            "description",
            "_global",
            "tests",
            "data_source",
            "data_file",
            "definitions",
            "effective_definitions",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["global"] = result.pop("_global")
        return result

    def run_validation(self, data=...):
        if "global" in data:
            data["_global"] = data.pop("global")
        return super().run_validation(data)


class DeviceReportSerializer(DeviceSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:device-detail")
    compliance_passed = serializers.BooleanField()
    results_passed = serializers.IntegerField()
    results_count = serializers.IntegerField()
    results = SerializedPKRelatedField(
        serializer=ComplianceTestResultSerializer, many=True, nested=True, required=False, read_only=True
    )

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.brief_fields + (
            "compliance_passed",
            "results_passed",
            "results_count",
            "results",
        )


class CommandSerializer(SubformValidationMixin, NetBoxModelSerializer):
    serializer = SerializerSerializer(required=False, nested=True)
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:command-detail")

    class Meta:
        model = models.Command
        fields = (
            "id",
            "url",
            "display",
            "name",
            "label",
            "retrieves_config",
            "serializer",
            "type",
            "parameters",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")


class PollerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:poller-detail")
    private_credentials = EncryptedDictField()
    commands = SerializedPKRelatedField(
        serializer=CommandSerializer,
        many=True,
        nested=True,
        queryset=models.Command.objects.all(),
        allow_empty=False,
    )

    class Meta:
        model = models.Poller
        fields = (
            "id",
            "url",
            "display",
            "name",
            "connection_type",
            "public_credentials",
            "private_credentials",
            "commands",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "name")

    @di.inject
    def validate(self, data, command_types: Annotated[dict[str, list[str]], "PollerChoices.command_types"]):
        models.Poller.validate_commands(data["commands"], command_types, data["connection_type"])
        return super().validate(data)


class BackupPointSerializer(SubformValidationMixin, NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:backuppoint-detail")
    data_source = NestedDataSourceSerializer()
    upload_url = serializers.CharField(source="url")
    parameters = EncryptedDictField(do_not_encrypt=models.BackupPoint._meta.get_field("parameters").do_not_encrypt)

    class Meta:
        model = models.BackupPoint
        fields = (
            "id",
            "url",
            "display",
            "name",
            "data_source",
            "backup_after_sync",
            "method",
            "upload_url",
            "ignore_rules",
            "parameters",
            "last_error",
            "last_status",
            "last_uploaded",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class SerializedStateItemSerializer(FieldsMixin, serializers.Serializer):
    name = serializers.CharField(read_only=True)
    serializer = SerializerSerializer(read_only=True, nested=True)
    data_source = NestedDataSourceSerializer(read_only=True, source="data_file.source")
    data_file = NestedDataFileSerializer(read_only=True)
    command = CommandSerializer(read_only=True, nested=True)
    last_updated = serializers.DateTimeField(allow_null=True, source="data_file.last_updated", read_only=True)
    error = serializers.CharField(read_only=True)
    value = serializers.SerializerMethodField(source="serialized", method_name="get_serialized")

    def get_serialized(self, state_item):
        if state_item.error is not None:
            return None
        return state_item.serialized


class SerializedStateSerializer(ListQPMixin, serializers.Serializer):
    count = serializers.SerializerMethodField()
    results = SerializedStateItemSerializer(many=True, read_only=True, source="*")

    def get_count(self, state):
        return len(state)

    def to_representation(self, instance):
        if name_filter := self.get_list_param("name"):
            instance = [item for item in instance if item.name in set(name_filter)]
        return super().to_representation(instance)


class RunTestsSerializer(serializers.Serializer):
    sync_datasources = serializers.BooleanField(required=False)
    selectors = PrimaryKeyField(
        many=True,
        required=False,
        queryset=models.ComplianceSelector.objects.all(),
    )
    devices = PrimaryKeyField(many=True, required=False, queryset=Device.objects.all())
    test_tags = PrimaryKeyField(many=True, required=False, queryset=Tag.objects.all())
    explanation_verbosity = serializers.ChoiceField(
        choices=ExplanationVerbosityChoices.choices, required=False, default=ExplanationVerbosityChoices.maximum
    )
    overriding_datasource = PrimaryKeyField(required=False, queryset=DataSource.objects.all())
    workers_num = serializers.IntegerField(min_value=1, default=1)
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    schedule_interval = serializers.IntegerField(required=False, allow_null=True)

    def validate_schedule_at(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError(_("Scheduled time must be in the future."))
        return value


class ScriptResultSerializer(serializers.Serializer):
    result = JobSerializer(read_only=True)

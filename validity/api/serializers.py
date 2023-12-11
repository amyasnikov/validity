from urllib.parse import urljoin

from core.api.nested_serializers import NestedDataFileSerializer, NestedDataSourceSerializer
from dcim.api.nested_serializers import (
    NestedDeviceSerializer,
    NestedDeviceTypeSerializer,
    NestedLocationSerializer,
    NestedManufacturerSerializer,
    NestedPlatformSerializer,
    NestedSiteSerializer,
)
from dcim.models import DeviceType, Location, Manufacturer, Platform, Site
from extras.api.nested_serializers import NestedTagSerializer
from extras.models import Tag
from netbox.api.fields import SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from tenancy.api.nested_serializers import NestedTenantSerializer
from tenancy.models import Tenant

from validity import models
from .helpers import EncryptedDictField, nested_factory


class ComplianceSelectorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:complianceselector-detail")
    tag_filter = SerializedPKRelatedField(
        serializer=NestedTagSerializer,
        many=True,
        required=False,
        queryset=Tag.objects.all(),
    )
    manufacturer_filter = SerializedPKRelatedField(
        serializer=NestedManufacturerSerializer, many=True, required=False, queryset=Manufacturer.objects.all()
    )
    type_filter = SerializedPKRelatedField(
        serializer=NestedDeviceTypeSerializer, many=True, required=False, queryset=DeviceType.objects.all()
    )
    platform_filter = SerializedPKRelatedField(
        serializer=NestedPlatformSerializer, many=True, required=False, queryset=Platform.objects.all()
    )
    location_filter = SerializedPKRelatedField(
        serializer=NestedLocationSerializer, many=True, required=False, queryset=Location.objects.all()
    )
    site_filter = SerializedPKRelatedField(
        serializer=NestedSiteSerializer, many=True, required=False, queryset=Site.objects.all()
    )
    tenant_filter = SerializedPKRelatedField(
        serializer=NestedTenantSerializer, many=True, required=False, queryset=Tenant.objects.all()
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


NestedComplianceSelectorSerializer = nested_factory(ComplianceSelectorSerializer, ("id", "url", "display", "name"))


class ComplianceTestSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetest-detail")
    selectors = SerializedPKRelatedField(
        serializer=NestedComplianceSelectorSerializer,
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


NestedComplianceTestSerializer = nested_factory(ComplianceTestSerializer, ("id", "url", "display", "name", "severity"))


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

    def get_results_url(self, obj):
        results_url = reverse("plugins-api:validity-api:compliancetestresult-list", request=self.context["request"])
        return results_url + f"?report_id={obj.pk}"


NestedComplianceReportSerializer = nested_factory(ComplianceReportSerializer, ("id", "url", "display"))


class ComplianceTestResultSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetestresult-detail")
    test = NestedComplianceTestSerializer()
    device = NestedDeviceSerializer()
    dynamic_pair = NestedDeviceSerializer(allow_null=True)
    report = NestedComplianceReportSerializer()

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


NestedComplianceTestResultSerializer = nested_factory(
    ComplianceTestResultSerializer, ("id", "url", "display", "passed")
)


class ConfigSerializerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:configserializer-detail")
    ttp_template = serializers.CharField(write_only=True, required=False)
    effective_template = serializers.ReadOnlyField()
    data_source = NestedDataSourceSerializer(required=False)
    data_file = NestedDataFileSerializer(required=False)

    class Meta:
        model = models.ConfigSerializer
        fields = (
            "id",
            "url",
            "display",
            "name",
            "extraction_method",
            "effective_template",
            "ttp_template",
            "data_source",
            "data_file",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedConfigSerializerSerializer = nested_factory(ConfigSerializerSerializer, ("id", "url", "display", "name"))


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

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["global"] = result.pop("_global")
        return result

    def run_validation(self, data=...):
        if "global" in data:
            data["_global"] = data.pop("global")
        return super().run_validation(data)


NestedNameSetSerializer = nested_factory(NameSetSerializer, ("id", "url", "display", "name"))


class SerializedConfigSerializer(serializers.Serializer):
    serializer = NestedConfigSerializerSerializer(read_only=True, source="device.serializer")
    data_source = NestedDataSourceSerializer(read_only=True, source="device.data_source")
    data_file = NestedDataFileSerializer(read_only=True, source="device.data_file")
    local_copy_last_updated = serializers.DateTimeField(allow_null=True, source="last_modified")
    config_web_link = serializers.SerializerMethodField()
    serialized_config = serializers.JSONField(source="serialized")

    def get_config_web_link(self, obj):
        return urljoin(obj.device.data_source.web_url, obj.device.config_path)


class DeviceReportSerializer(NestedDeviceSerializer):
    compliance_passed = serializers.BooleanField()
    results_passed = serializers.IntegerField()
    results_count = serializers.IntegerField()
    results = SerializedPKRelatedField(
        serializer=NestedComplianceTestResultSerializer, many=True, required=False, read_only=True
    )

    class Meta(NestedDeviceSerializer.Meta):
        fields = NestedDeviceSerializer.Meta.fields + [
            "compliance_passed",
            "results_passed",
            "results_count",
            "results",
        ]


class CommandSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:command-detail")

    class Meta:
        model = models.Command
        fields = (
            "id",
            "url",
            "display",
            "name",
            "slug",
            "retrieves_config",
            "type",
            "parameters",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedCommandSerializer = nested_factory(CommandSerializer, ("id", "url", "display", "name"))


class PollerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:poller-detail")
    private_credentials = EncryptedDictField()
    commands = SerializedPKRelatedField(
        serializer=NestedCommandSerializer, many=True, required=False, queryset=models.Command.objects.all()
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


NestedPollerSerializer = nested_factory(PollerSerializer, ("id", "url", "display", "name"))

from dcim.api.nested_serializers import (
    NestedDeviceSerializer,
    NestedDeviceTypeSerializer,
    NestedLocationSerializer,
    NestedManufacturerSerializer,
    NestedPlatformSerializer,
    NestedSiteSerializer,
)
from extras.api.nested_serializers import NestedTagSerializer
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from validity import models
from .helpers import PasswordField, nested_factory


class ComplianceSelectorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:complianceselector-detail")
    tags_filter = NestedTagSerializer(many=True, required=False)
    manufacturer_filter = NestedManufacturerSerializer(many=True, required=False)
    type_filter = NestedDeviceTypeSerializer(many=True, required=False)
    platform_filter = NestedPlatformSerializer(many=True, required=False)
    location_filter = NestedLocationSerializer(many=True, required=False)
    site_filter = NestedSiteSerializer(many=True, required=False)

    class Meta:
        model = models.ComplianceSelector
        fields = (
            "id",
            "url",
            "display",
            "name",
            "filter_operation",
            "name_filter",
            "tags_filter",
            "manufacturer_filter",
            "type_filter",
            "platform_filter",
            "status_filter",
            "location_filter",
            "site_filter",
            "dynamic_pairs",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedComplianceSelectorSerializer = nested_factory(
    ComplianceSelectorSerializer, ("id", "url", "display", "name", "created", "last_updated")
)


class ComplianceTestSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetest-detail")
    selectors = NestedComplianceSelectorSerializer(many=True)

    class Meta:
        model = models.ComplianceTest
        fields = (
            "id",
            "url",
            "display",
            "name",
            "expression",
            "selectors",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedComplianceTestSerializer = nested_factory(
    ComplianceTestSerializer, ("id", "url", "display", "name", "created", "last_updated")
)


class ComplianceTestResultSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:compliancetestresult-detail")
    test = NestedComplianceTestSerializer()
    device = NestedDeviceSerializer()

    class Meta:
        model = models.ComplianceTestResult
        fields = (
            "id",
            "url",
            "display",
            "test",
            "device",
            "passed",
            "explanation",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedComplianceTestResultSerializer = nested_factory(
    ComplianceTestResultSerializer, ("id", "url", "display", "passed", "created", "last_updated")
)


class GitRepoSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:gitrepo-detail")
    password = PasswordField()

    class Meta:
        model = models.GitRepo
        fields = (
            "id",
            "url",
            "display",
            "name",
            "git_url",
            "web_url",
            "device_config_path",
            "default",
            "username",
            "password",
            "branch",
            "head_hash",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


NestedGitRepoSerializer = nested_factory(
    GitRepoSerializer, ("id", "url", "display", "name", "default", "created", "last_updated")
)


class ConfigSerializerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:validity-api:configserializer-detail")

    class Meta:
        model = models.ConfigSerializer
        fields = ("id", "url", "display", "name", "ttp_template", "tags", "custom_fields", "created", "last_updated")


NestedConfigSerializerSerializer = nested_factory(
    ConfigSerializerSerializer, ("id", "url", "display", "name", "ttp_template", "created", "last_updated")
)

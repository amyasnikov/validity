from dcim.graphql.types import DeviceType
from graphene import Boolean, Field, Int, List, ObjectType
from netbox.graphql.fields import ObjectField, ObjectListField
from netbox.graphql.types import BaseObjectType, NetBoxObjectType

from validity import filtersets, models


class GitRepoType(NetBoxObjectType):
    class Meta:
        model = models.GitRepo
        fields = (
            "id",
            "name",
            "git_url",
            "web_url",
            "device_config_path",
            "default",
            "username",
            "branch",
            "head_hash",
            "created",
            "last_updated",
        )


class NameSetType(NetBoxObjectType):
    global_ = Field(name="global", type_=Boolean, source="_global")

    class Meta:
        model = models.NameSet
        fields = (
            "id",
            "name",
            "description",
            "tests",
            "definitions",
            "repo",
            "file_path",
            "created",
            "last_updated",
        )
        filterset_class = filtersets.NameSetFilterSet


selector_fields = (
    "id",
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
    "tests",
    "created",
    "last_updated",
)


class ComplianceSelectorType(NetBoxObjectType):
    class Meta:
        model = models.ComplianceSelector
        fields = selector_fields
        filterset_class = filtersets.ComplianceSelectorFilterSet


class ComplianceSelectorWithDevicesType(ComplianceSelectorType):
    devices = List(of_type=DeviceType)

    class Meta:
        model = models.ComplianceSelector
        fields = selector_fields


class ConfigSerializerType(NetBoxObjectType):
    class Meta:
        model = models.ConfigSerializer
        fields = ("id", "name", "extraction_method", "ttp_template", "repo", "file_path", "created", "last_updated")
        filterset_class = filtersets.ConfigSerializerFilterSet


class ComplianceTestType(NetBoxObjectType):
    class Meta:
        model = models.ComplianceTest
        fields = (
            "id",
            "name",
            "description",
            "severity",
            "selectors",
            "repo",
            "file_path",
            "namesets",
            "created",
            "last_updated",
        )
        filterset_class = filtersets.ComplianceTestFilterSet


class ComplianceTestResultType(BaseObjectType):
    class Meta:
        model = models.ComplianceTestResult
        fields = (
            "id",
            "test",
            "device",
            "dynamic_pair",
            "explanation",
            "passed",
            "explanation",
            "report",
            "created",
            "last_updated",
        )
        filterset_class = filtersets.ComplianceTestResultFilterSet


class ReportType(BaseObjectType):
    device_count = Int()
    test_count = Int()
    total_passed = Int()
    total_count = Int()
    low_passed = Int()
    low_count = Int()
    middle_passed = Int()
    middle_count = Int()
    high_passed = Int()
    high_count = Int()

    class Meta:
        model = models.ComplianceReport
        fields = ("id", "created", "last_updated", "results")

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.annotate_result_stats().count_devices_and_tests()


class Query(ObjectType):
    repo = ObjectField(GitRepoType)
    repo_list = ObjectListField(GitRepoType)

    nameset = ObjectField(NameSetType)
    nameset_list = ObjectListField(NameSetType)

    selector = ObjectField(ComplianceSelectorWithDevicesType)
    selector_list = ObjectListField(ComplianceSelectorType)

    serializer = ObjectField(ConfigSerializerType)
    serializer_list = ObjectListField(ConfigSerializerType)

    test = ObjectField(ComplianceTestType)
    test_list = ObjectListField(ComplianceTestType)

    test_result = ObjectField(ComplianceTestResultType)
    test_result_list = ObjectListField(ComplianceTestResultType)

    report = ObjectField(ReportType)
    report_list = ObjectListField(ReportType)


schema = Query

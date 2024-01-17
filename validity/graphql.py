from dcim.graphql.types import DeviceType
from graphene import Boolean, Field, Int, List, ObjectType
from netbox.graphql.fields import ObjectField, ObjectListField
from netbox.graphql.types import BaseObjectType, NetBoxObjectType

from validity import filtersets, models


class NameSetType(NetBoxObjectType):
    global_ = Field(name="global", type_=Boolean, source="_global")

    class Meta:
        model = models.NameSet
        fields = "__all__"
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


class SerializerType(NetBoxObjectType):
    class Meta:
        model = models.Serializer
        fields = "__all__"
        filterset_class = filtersets.SerializerFilterSet


class ComplianceTestType(NetBoxObjectType):
    class Meta:
        model = models.ComplianceTest
        fields = "__all__"
        filterset_class = filtersets.ComplianceTestFilterSet


class ComplianceTestResultType(BaseObjectType):
    class Meta:
        model = models.ComplianceTestResult
        fields = "__all__"
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
        fields = "__all__"

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.annotate_result_stats().count_devices_and_tests()


class PollerType(NetBoxObjectType):
    class Meta:
        model = models.Poller
        fields = "__all__"
        filterset_class = filtersets.PollerFilterSet


class CommandType(NetBoxObjectType):
    class Meta:
        model = models.Command
        fields = "__all__"
        filterset_class = filtersets.CommandFilterSet


class Query(ObjectType):
    nameset = ObjectField(NameSetType)
    nameset_list = ObjectListField(NameSetType)

    selector = ObjectField(ComplianceSelectorWithDevicesType)
    selector_list = ObjectListField(ComplianceSelectorType)

    serializer = ObjectField(SerializerType)
    serializer_list = ObjectListField(SerializerType)

    test = ObjectField(ComplianceTestType)
    test_list = ObjectListField(ComplianceTestType)

    test_result = ObjectField(ComplianceTestResultType)
    test_result_list = ObjectListField(ComplianceTestResultType)

    report = ObjectField(ReportType)
    report_list = ObjectListField(ReportType)

    poller = ObjectField(PollerType)
    poller_list = ObjectListField(PollerType)

    command = ObjectField(CommandType)
    command_list = ObjectListField(CommandType)


schema = Query

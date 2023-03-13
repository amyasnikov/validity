from netbox.api.viewsets import NetBoxModelViewSet

from validity import filtersets, models
from . import serializers


class ReadOnlyNetboxViewSet(NetBoxModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]


class ComplianceSelectorViewSet(NetBoxModelViewSet):
    queryset = models.ComplianceSelector.objects.prefetch_related(
        "tag_filter", "manufacturer_filter", "type_filter", "platform_filter", "location_filter", "site_filter", "tags"
    )
    serializer_class = serializers.ComplianceSelectorSerializer
    filterset_class = filtersets.ComplianceSelectorFilterSet


class ComplianceTestViewSet(NetBoxModelViewSet):
    queryset = models.ComplianceTest.objects.select_related("repo").prefetch_related("selectors", "tags")
    serializer_class = serializers.ComplianceTestSerializer
    filterset_class = filtersets.ComplianceTestFilterSet


class ComplianceTestResultViewSet(ReadOnlyNetboxViewSet):
    queryset = models.ComplianceTestResult.objects.select_related("device", "test", "report")
    serializer_class = serializers.ComplianceTestResultSerializer
    filterset_class = filtersets.ComplianceTestResultFilterSet


class GitRepoViewSet(NetBoxModelViewSet):
    queryset = models.GitRepo.objects.prefetch_related("tags")
    serializer_class = serializers.GitRepoSerializer
    filterset_class = filtersets.GitRepoFilterSet


class ConfigSerializerViewSet(NetBoxModelViewSet):
    queryset = models.ConfigSerializer.objects.select_related("repo").prefetch_related("tags")
    serializer_class = serializers.ConfigSerializerSerializer
    filterset_class = filtersets.ConfigSerializerFilterSet


class NameSetViewSet(NetBoxModelViewSet):
    queryset = models.NameSet.objects.select_related("repo").prefetch_related("tags")
    serializer_class = serializers.NameSetSerializer
    filterset_class = filtersets.NameSetFilterSet


class ComplianceReportViewSet(ReadOnlyNetboxViewSet):
    queryset = models.ComplianceReport.objects.annotate_result_stats().count_devices_and_tests()
    serializer_class = serializers.ComplianceReportSerializer

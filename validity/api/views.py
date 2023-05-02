from http import HTTPStatus

from netbox.api.viewsets import NetBoxModelViewSet
from netbox.settings import VERSION
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from validity import filtersets, models
from validity.config_compliance.device_config import DeviceConfig
from ..config_compliance.exceptions import DeviceConfigError
from . import serializers


if VERSION.split(".") < ["3", "5"]:
    from drf_yasg.utils import swagger_auto_schema as extend_schema
else:
    from drf_spectacular.utils import extend_schema


class ReadOnlyNetboxViewSet(NetBoxModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]


class ComplianceSelectorViewSet(NetBoxModelViewSet):
    queryset = models.ComplianceSelector.objects.prefetch_related(
        "tag_filter",
        "manufacturer_filter",
        "type_filter",
        "platform_filter",
        "location_filter",
        "site_filter",
        "tenant_filter",
        "tags",
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


class SerializedConfigView(APIView):
    queryset = models.VDevice.objects.all()

    def get_object(self, pk):
        try:
            return self.queryset.get(pk=pk)
        except models.VDevice.DoesNotExist:
            raise NotFound

    @extend_schema(
        responses={200: serializers.SerializedConfigSerializer()}, operation_id="dcim_devices_serialized_config"
    )
    def get(self, request, pk):
        device = self.get_object(pk)
        try:
            config = DeviceConfig.from_device(device)
            serializer = serializers.SerializedConfigSerializer(config, context={"request": request})
            return Response(serializer.data)
        except DeviceConfigError as e:
            return Response(
                data={"detail": "Unable to fetch serialized config", "error": str(e)}, status=HTTPStatus.BAD_REQUEST
            )

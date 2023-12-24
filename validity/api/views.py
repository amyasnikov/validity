from http import HTTPStatus

from netbox.api.viewsets import NetBoxModelViewSet
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from validity import config, filtersets, models
from validity.choices import SeverityChoices
from validity.config_compliance.device_config import DeviceConfig
from validity.config_compliance.exceptions import DeviceConfigError
from . import serializers


if config.netbox_version < "3.5.0":
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
    queryset = models.ComplianceTest.objects.select_related("data_source", "data_file").prefetch_related(
        "selectors", "tags"
    )
    serializer_class = serializers.ComplianceTestSerializer
    filterset_class = filtersets.ComplianceTestFilterSet


class ComplianceTestResultViewSet(ReadOnlyNetboxViewSet):
    queryset = models.ComplianceTestResult.objects.select_related("device", "test", "report")
    serializer_class = serializers.ComplianceTestResultSerializer
    filterset_class = filtersets.ComplianceTestResultFilterSet


class SerializerViewSet(NetBoxModelViewSet):
    queryset = models.Serializer.objects.select_related("data_source", "data_file").prefetch_related("tags")
    serializer_class = serializers.SerializerSerializer
    filterset_class = filtersets.SerializerFilterSet


class NameSetViewSet(NetBoxModelViewSet):
    queryset = models.NameSet.objects.select_related("data_source", "data_file").prefetch_related("tags")
    serializer_class = serializers.NameSetSerializer
    filterset_class = filtersets.NameSetFilterSet


class ComplianceReportViewSet(NetBoxModelViewSet):
    queryset = models.ComplianceReport.objects.annotate_result_stats().count_devices_and_tests()
    serializer_class = serializers.ComplianceReportSerializer
    http_method_names = ["get", "head", "options", "trace", "delete"]


class PollerViewSet(NetBoxModelViewSet):
    queryset = models.Poller.objects.prefetch_related("tags", "commands")
    serializer_class = serializers.PollerSerializer
    filterset_class = filtersets.PollerFilterSet


class CommandViewSet(NetBoxModelViewSet):
    queryset = models.Command.objects.prefetch_related("tags")
    serializer_class = serializers.CommandSerializer
    filterset_class = filtersets.CommandFilterSet


class DeviceReportView(ListAPIView):
    serializer_class = serializers.DeviceReportSerializer
    filterset_class = filtersets.DeviceReportFilterSet
    queryset = models.VDevice.objects.all()

    def get_queryset(self):
        severity_ge = SeverityChoices.from_request(self.request)
        pk = self.kwargs["pk"]
        return (
            self.queryset.filter(results__report__pk=pk)
            .annotate_result_stats(pk, severity_ge)
            .prefetch_results(pk, severity_ge)
        )


class SerializedConfigView(APIView):
    queryset = models.VDevice.objects.prefetch_datasource().prefetch_serializer().prefetch_poller()

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

from http import HTTPStatus
from typing import Annotated, Any

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from netbox.api.viewsets import NetBoxModelViewSet, NetBoxReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from validity import di, filtersets, models
from validity.choices import SeverityChoices
from validity.scripts import Launcher, RunTestsParams, ScriptParams
from . import serializers


class RunMixin:
    run_serializer_class: type[Serializer]
    params_class: type[ScriptParams]
    launcher: Launcher

    def get_params(self, serializer, request):
        return self.params_class(**serializer.validated_data, request=request)

    def get_result_data(self, job, request):
        serializer = serializers.ScriptResultSerializer({"result": job}, context={"request": request})
        return serializer.data

    def run(self, request):
        serializer = self.run_serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(status=HTTPStatus.BAD_REQUEST, data=serializer.errors)
        job = self.launcher(self.get_params(serializer, request))
        return Response(self.get_result_data(job, request))


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


@extend_schema_view(run=extend_schema(request=serializers.RunTestsSerializer))
class ComplianceTestViewSet(RunMixin, NetBoxModelViewSet):
    queryset = models.ComplianceTest.objects.select_related("data_source", "data_file").prefetch_related(
        "selectors", "tags"
    )
    serializer_class = serializers.ComplianceTestSerializer
    filterset_class = filtersets.ComplianceTestFilterSet
    run_serializer_class = serializers.RunTestsSerializer
    params_class = RunTestsParams

    @di.inject
    def __init__(self, launcher: Annotated[Launcher, "runtests_launcher"], **kwargs: Any) -> None:
        self.launcher = launcher
        super().__init__(**kwargs)

    @action(detail=False, methods=["post"], url_path="run")
    def run(self, request):
        return super().run(request)


class ComplianceTestResultViewSet(NetBoxReadOnlyModelViewSet):
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


class ComplianceReportViewSet(NetBoxReadOnlyModelViewSet):
    queryset = models.ComplianceReport.objects.annotate_result_stats().count_devices_and_tests()
    serializer_class = serializers.ComplianceReportSerializer
    filterset_class = filtersets.ComplianceReportFilterSet


class PollerViewSet(NetBoxModelViewSet):
    queryset = models.Poller.objects.prefetch_related("tags", "commands")
    serializer_class = serializers.PollerSerializer
    filterset_class = filtersets.PollerFilterSet


class CommandViewSet(NetBoxModelViewSet):
    queryset = models.Command.objects.select_related("serializer").prefetch_related("tags")
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


class SerializedStateView(APIView):
    queryset = models.VDevice.objects.prefetch_datasource().prefetch_serializer().prefetch_poller()

    def get_object(self, pk):
        try:
            return self.queryset.get(pk=pk)
        except models.VDevice.DoesNotExist as err:
            raise NotFound from err

    @extend_schema(
        responses={200: serializers.SerializedStateSerializer()},
        operation_id="dcim_devices_serialized_state",
        parameters=[
            OpenApiParameter(name="fields", type=str, many=True),
            OpenApiParameter(name="name", type=str, many=True),
        ],
    )
    def get(self, request, pk):
        device = self.get_object(pk)
        serializer = serializers.SerializedStateSerializer(device.state.values(), context={"request": request})
        return Response(serializer.data)

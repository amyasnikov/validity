from typing import Annotated

import strawberry
import strawberry_django
from core.graphql.types import DataFileType, DataSourceType
from core.models import Job
from dcim.graphql.types import DeviceType
from django.db.models import Count, Q
from netbox.graphql.types import BaseObjectType, NetBoxObjectType
from strawberry.scalars import JSON

from validity import models
from .filters import (
    BackupPointFilter,
    CommandFilter,
    ComplianceReportFilter,
    ComplianceSelectorFilter,
    ComplianceTestFilter,
    ComplianceTestResultFilter,
    NameSetFilter,
    PollerFilter,
    SerializerFilter,
)


@strawberry_django.type(
    Job,
    fields="__all__",
)
class JobType(BaseObjectType):
    pass


@strawberry_django.type(
    models.ComplianceSelector,
    fields="__all__",
    filters=ComplianceSelectorFilter,
    pagination=True,
)
class ComplianceSelectorType(NetBoxObjectType):
    tests: list[Annotated["ComplianceTestType", strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()

    @strawberry.field
    def devices(self) -> list[DeviceType]:
        return list(self.devices)


@strawberry_django.type(
    models.ComplianceTest,
    fields="__all__",
    filters=ComplianceTestFilter,
    pagination=True,
)
class ComplianceTestType(NetBoxObjectType):
    selectors: list[Annotated[ComplianceSelectorType, strawberry.lazy("validity.graphql.types")]] = (
        strawberry_django.field()
    )
    namesets: list[Annotated["NameSetType", strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()
    results: list[Annotated["ComplianceTestResultType", strawberry.lazy("validity.graphql.types")]] = (
        strawberry_django.field()
    )
    data_source: Annotated["DataSourceType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()
    data_file: Annotated["DataFileType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()


@strawberry_django.type(
    models.ComplianceTestResult,
    fields="__all__",
    filters=ComplianceTestResultFilter,
    pagination=True,
)
class ComplianceTestResultType(BaseObjectType):
    test: Annotated[ComplianceTestType, strawberry.lazy("validity.graphql.types")] = strawberry_django.field()
    device: Annotated["DeviceType", strawberry.lazy("dcim.graphql.types")] = strawberry_django.field()
    report: Annotated["ComplianceReportType", strawberry.lazy("validity.graphql.types")] | None = (
        strawberry_django.field()
    )


@strawberry_django.type(models.Serializer, fields="__all__", filters=SerializerFilter, pagination=True)
class SerializerType(NetBoxObjectType):
    commands: list[Annotated["CommandType", strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()
    data_source: Annotated["DataSourceType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()
    data_file: Annotated["DataFileType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()


@strawberry_django.type(
    models.NameSet,
    fields=(
        "id",
        "name",
        "description",
        "definitions",
        "tests",
        "created",
        "last_updated",
    ),
    filters=NameSetFilter,
    pagination=True,
)
class NameSetType(NetBoxObjectType):
    tests: list[Annotated[ComplianceTestType, strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()
    data_source: Annotated["DataSourceType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()
    data_file: Annotated["DataFileType", strawberry.lazy("core.graphql.types")] | None = strawberry_django.field()

    @strawberry.field(name="global")
    def global_alias(self) -> bool:
        return getattr(self, "_global", False)


@strawberry_django.type(
    models.ComplianceReport,
    fields="__all__",
    filters=ComplianceReportFilter,
    pagination=True,
)
class ComplianceReportType(BaseObjectType):
    results: list[Annotated[ComplianceTestResultType, strawberry.lazy("validity.graphql.types")]] = (
        strawberry_django.field()
    )
    jobs: list[Annotated["JobType", strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()

    device_count: int = strawberry_django.field(annotate=Count("results__device", distinct=True))
    test_count: int = strawberry_django.field(annotate=Count("results__test", distinct=True))
    total_passed: int = strawberry_django.field(annotate=Count("results", filter=Q(results__passed=True)))
    total_count: int = strawberry_django.field(annotate=Count("results"))
    low_passed: int = strawberry_django.field(
        annotate=Count("results", filter=Q(results__test__severity="LOW") & Q(results__passed=True))
    )
    low_count: int = strawberry_django.field(annotate=Count("results", filter=Q(results__test__severity="LOW")))
    middle_passed: int = strawberry_django.field(
        annotate=Count("results", filter=Q(results__test__severity="MIDDLE") & Q(results__passed=True))
    )
    middle_count: int = strawberry_django.field(annotate=Count("results", filter=Q(results__test__severity="MIDDLE")))
    high_passed: int = strawberry_django.field(
        annotate=Count("results", filter=Q(results__test__severity="HIGH") & Q(results__passed=True))
    )
    high_count: int = strawberry_django.field(annotate=Count("results", filter=Q(results__test__severity="HIGH")))

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.order_by("-created")


@strawberry_django.type(
    models.Poller,
    fields=(
        "id",
        "name",
        "connection_type",
        "public_credentials",
        "commands",
        "created",
        "last_updated",
    ),
    filters=PollerFilter,
    pagination=True,
)
class PollerType(NetBoxObjectType):
    commands: list[Annotated["CommandType", strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()


@strawberry_django.type(
    models.Command,
    fields=(
        "id",
        "name",
        "label",
        "retrieves_config",
        "serializer",
        "type",
        "pollers",
        "created",
        "last_updated",
    ),
    filters=CommandFilter,
    pagination=True,
)
class CommandType(NetBoxObjectType):
    serializer: Annotated[SerializerType, strawberry.lazy("validity.graphql.types")] | None = strawberry_django.field()
    pollers: list[Annotated[PollerType, strawberry.lazy("validity.graphql.types")]] = strawberry_django.field()

    @strawberry.field
    def parameters(self) -> JSON | None:
        value = getattr(self, "parameters", None)
        return value


@strawberry_django.type(
    models.BackupPoint,
    fields=(
        "id",
        "name",
        "backup_after_sync",
        "method",
        "url",
        "last_uploaded",
        "last_status",
        "last_error",
        "created",
        "last_updated",
    ),
    filters=BackupPointFilter,
    pagination=True,
)
class BackupPointType(NetBoxObjectType):
    data_source: Annotated["DataSourceType", strawberry.lazy("core.graphql.types")] = strawberry_django.field()

    @strawberry.field
    def parameters(self) -> JSON:
        value = getattr(self, "parameters", None)
        if value is None:
            return None  # type: ignore[return-value]
        decrypted = getattr(value, "decrypted", None)
        return decrypted if decrypted is not None else value

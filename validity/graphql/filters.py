from typing import Annotated

import strawberry
import strawberry_django
from core.graphql.filters import DataSourceFilter
from core.models import Job
from dcim.graphql.filters import DeviceFilter
from django.db.models import Q, QuerySet
from strawberry.scalars import ID
from strawberry_django import FilterLookup, StrFilterLookup

from validity import models
from validity.netbox_changes import BaseModelFilter, NetBoxModelFilter


@strawberry_django.filter_type(Job, lookups=True)
class JobFilter(NetBoxModelFilter):
    pass


@strawberry_django.filter_type(models.ComplianceSelector, lookups=True)
class ComplianceSelectorFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")


@strawberry_django.filter_type(models.ComplianceTest, lookups=True)
class ComplianceTestFilter(NetBoxModelFilter):
    id: FilterLookup[ID] | None = strawberry_django.filter_field()
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")
    selectors: Annotated["ComplianceSelectorFilter", strawberry.lazy("validity.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )


@strawberry_django.filter_type(models.ComplianceTestResult, lookups=True)
class ComplianceTestResultFilter(BaseModelFilter):
    test: Annotated["ComplianceTestFilter", strawberry.lazy("validity.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )

    device: Annotated["DeviceFilter", strawberry.lazy("dcim.graphql.filters")] | None = strawberry_django.filter_field()

    report: Annotated["ComplianceReportFilter", strawberry.lazy("validity.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )

    @strawberry_django.filter_field
    def latest(self, queryset: QuerySet, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value and queryset.model == models.ComplianceTestResult:
            queryset = queryset.only_latest()
        return queryset, Q()


@strawberry_django.filter_type(models.Serializer, lookups=True)
class SerializerFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")


@strawberry_django.filter_type(models.NameSet, lookups=True)
class NameSetFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")
    _global: Annotated["bool", strawberry.lazy("builtins")] | None = strawberry_django.filter_field(name="global")


@strawberry_django.filter_type(models.ComplianceReport, lookups=True)
class ComplianceReportFilter(BaseModelFilter):
    jobs: list[Annotated["JobFilter", strawberry.lazy("validity.graphql.filters")]] = strawberry_django.filter_field()


@strawberry_django.filter_type(models.Poller, lookups=True)
class PollerFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")


@strawberry_django.filter_type(models.Command, lookups=True)
class CommandFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")
    serializer: Annotated["SerializerFilter", strawberry.lazy("validity.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )

    pollers: Annotated["PollerFilter", strawberry.lazy("validity.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )


@strawberry_django.filter_type(models.BackupPoint, lookups=True)
class BackupPointFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field(name="name")
    data_source: Annotated["DataSourceFilter", strawberry.lazy("core.graphql.filters")] | None = (
        strawberry_django.filter_field()
    )

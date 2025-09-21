from typing import Annotated

import strawberry
import strawberry_django

from validity import models
from .filters import NameSetFilter
from .types import (
    BackupPointType,
    CommandType,
    ComplianceReportType,
    ComplianceSelectorType,
    ComplianceTestResultType,
    ComplianceTestType,
    NameSetType,
    PollerType,
    SerializerType,
)


@strawberry.type
class Query:
    # ComplianceSelector
    validity_selector: ComplianceSelectorType | None = strawberry_django.field()
    validity_selector_list: list[ComplianceSelectorType] = strawberry_django.field()

    # ComplianceTest
    validity_test: ComplianceTestType | None = strawberry_django.field()
    validity_test_list: list[ComplianceTestType] = strawberry_django.field()

    # ComplianceTestResult
    validity_test_result: ComplianceTestResultType | None = strawberry_django.field()
    validity_test_result_list: list[ComplianceTestResultType] = strawberry_django.field()

    # Serializer
    validity_serializer: SerializerType | None = strawberry_django.field()
    validity_serializer_list: list[SerializerType] = strawberry_django.field()

    # NameSet
    validity_nameset: NameSetType | None = strawberry_django.field()

    @strawberry.field
    def validity_nameset_list(
        self,
        info,
        filters: NameSetFilter | None = None,
        global_filter: Annotated[bool | None, strawberry.argument(name="global")] = None,
    ) -> list[NameSetType]:
        queryset = models.NameSet.objects.all()
        if filters is not None:
            queryset = strawberry_django.filters.apply(filters, queryset, info=info)
        if global_filter is not None:
            queryset = queryset.filter(_global=global_filter)
        return list(queryset)

    # ComplianceReport
    validity_report: ComplianceReportType | None = strawberry_django.field()
    validity_report_list: list[ComplianceReportType] = strawberry_django.field()

    # Poller
    validity_poller: PollerType | None = strawberry_django.field()
    validity_poller_list: list[PollerType] = strawberry_django.field()

    # Command
    validity_command: CommandType | None = strawberry_django.field()
    validity_command_list: list[CommandType] = strawberry_django.field()

    # BackupPoint
    validity_backup_point: BackupPointType | None = strawberry_django.field()
    validity_backup_point_list: list[BackupPointType] = strawberry_django.field()


schema = (Query,)

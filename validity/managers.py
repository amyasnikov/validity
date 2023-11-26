from itertools import chain
from typing import TypeVar

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    BigIntegerField,
    BooleanField,
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Prefetch,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from netbox.models import RestrictedQuerySet

from validity import settings
from validity.choices import DeviceGroupByChoices, SeverityChoices
from validity.utils.orm import CustomPrefetchMixin, RegexpReplace


class ComplianceTestQS(RestrictedQuerySet):
    def pf_latest_results(self) -> "ComplianceTestQS":
        from validity.models import ComplianceTestResult

        return self.prefetch_related(Prefetch("results", ComplianceTestResult.objects.only_latest()))

    def annotate_latest_count(self):
        from validity.models import ComplianceTestResult

        return self.annotate(
            passed=Count(
                "results",
                distinct=True,
                filter=Q(results__passed=True, results__in=ComplianceTestResult.objects.only_latest()),
            ),
            failed=Count(
                "results",
                distinct=True,
                filter=Q(results__passed=False, results__in=ComplianceTestResult.objects.only_latest()),
            ),
        )


class ComplianceTestResultQS(RestrictedQuerySet):
    def only_latest(self, exclude: bool = False) -> "ComplianceTestResultQS":
        qs = self.order_by("test__pk", "device__pk", "-created").distinct("test__pk", "device__pk")
        if exclude:
            return self.exclude(pk__in=qs.values("pk"))
        return self.filter(pk__in=qs.values("pk"))

    def last_more_than(self, than: int) -> "ComplianceTestResultQS":
        qs = self.values("device", "test").annotate(ids=ArrayAgg(F("id"), ordering="-created"))
        last_ids = chain.from_iterable(record["ids"][than:] for record in qs.iterator())
        return self.filter(pk__in=last_ids)

    def count_devices_and_tests(self):
        return self.aggregate(device_count=Count("devices", distinct=True), test_count=Count("tests", distinct=True))

    def delete_old(self, _settings=settings):
        del_count = self.filter(report=None).last_more_than(_settings.store_last_results)._raw_delete(self.db)
        return (del_count, {"validity.ComplianceTestResult": del_count})


def percentage(field1: str, field2: str) -> Case:
    return Case(
        When(Q(**{f"{field2}__gt": 0}), then=Value(100.0) * F(field1) / F(field2)),
        default=100.0,
        output_field=FloatField(),
    )


class VDataFileQS(RestrictedQuerySet):
    pass


class VDataSourceQS(CustomPrefetchMixin, RestrictedQuerySet):
    def annotate_config_path(self):
        return self.annotate(device_config_path=KeyTextTransform("device_config_path", "custom_field_data"))

    def prefetch_config_files(self):
        from validity.models import VDataFile

        config_path = RegexpReplace(F("device_config_path"), Value("{{.+?}}"), Value(".+?"))
        path_filter = Q(datafiles__path__regex=config_path)
        return (
            self.annotate_config_path()
            .annotate(config_files_id=ArrayAgg(F("datafiles__pk"), filter=path_filter))
            .annotate(config_file_count=Count("datafiles__pk", filter=path_filter))
            .custom_prefetch("config_files", VDataFile.objects.all(), many=True)
        )


class ComplianceReportQS(RestrictedQuerySet):
    def annotate_result_stats(self, groupby_field: DeviceGroupByChoices | None = None):
        qs = self
        if groupby_field:
            qs = self.values(f"results__{groupby_field.pk_field()}", f"results__{groupby_field}")
        only_passed = Q(results__passed=True)
        qs = qs.annotate(
            total_count=Count("results"),
            total_passed=Count("results", filter=only_passed),
            total_percentage=percentage("total_passed", "total_count"),
        )
        for severity, _ in SeverityChoices.choices:
            s_lower = severity.lower()
            s_filter = Q(results__test__severity=severity)
            qs = qs.annotate(
                **{
                    f"{s_lower}_count": Count("results", filter=s_filter),
                    f"{s_lower}_passed": Count("results", filter=s_filter & only_passed),
                    f"{s_lower}_percentage": percentage(f"{s_lower}_passed", f"{s_lower}_count"),
                }
            )
        return qs

    def count_devices_and_tests(self):
        return self.annotate(
            device_count=Count("results__device", distinct=True), test_count=Count("results__test", distinct=True)
        )

    def delete_old(self, _settings=settings):
        from validity.models import ComplianceTestResult

        old_reports = list(self.order_by("-created").values_list("pk", flat=True)[_settings.store_reports :])
        deleted_results = ComplianceTestResult.objects.filter(report__pk__in=old_reports)._raw_delete(self.db)
        deleted_reports, _ = self.filter(pk__in=old_reports).delete()
        return (
            deleted_results + deleted_reports,
            {"validity.ComplianceTestResult": deleted_results, "validity.ComplianceReport": deleted_reports},
        )


_QS = TypeVar("_QS", bound=QuerySet)


class VDeviceQS(CustomPrefetchMixin, RestrictedQuerySet):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.selector = None

    def _clone(self, *args, **kwargs):
        c = super()._clone(*args, **kwargs)
        c.selector = self.selector
        return c

    def set_selector(self, selector):
        self.selector = selector
        return self

    def _fetch_all(self):
        super()._fetch_all()
        if self.selector:
            for item in self._result_cache:
                if isinstance(item, self.model):
                    item.selector = self.selector

    def annotate_datasource_id(self: _QS) -> _QS:
        from validity.models import VDataSource

        return self.annotate(
            bound_source=Cast(KeyTextTransform("config_data_source", "tenant__custom_field_data"), BigIntegerField())
        ).annotate(
            data_source_id=Case(
                When(bound_source__isnull=False, then=F("bound_source")),
                default=VDataSource.objects.filter(custom_field_data__device_config_default=True).values("id")[:1],
                output_field=BigIntegerField(),
            )
        )

    def prefetch_datasource(self: _QS, prefetch_config_files: bool = False) -> _QS:
        from validity.models import VDataSource

        datasource_qs = VDataSource.objects.all()
        if prefetch_config_files:
            datasource_qs = datasource_qs.prefetch_config_files()
        return self.annotate_datasource_id().custom_prefetch("data_source", datasource_qs)

    def annotate_serializer_id(self: _QS) -> _QS:
        return (
            self.annotate(device_s=KeyTextTransform("serializer", "custom_field_data"))
            .annotate(
                devtype_s=KeyTextTransform("serializer", "device_type__custom_field_data"),
            )
            .annotate(manufacturer_s=KeyTextTransform("serializer", "device_type__manufacturer__custom_field_data"))
            .annotate(
                serializer_id=Case(
                    When(device_s__isnull=False, then=Cast(F("device_s"), BigIntegerField())),
                    When(devtype_s__isnull=False, then=Cast(F("devtype_s"), BigIntegerField())),
                    When(manufacturer_s__isnull=False, then=Cast(F("manufacturer_s"), BigIntegerField())),
                )
            )
        )

    def prefetch_serializer(self: _QS) -> _QS:
        from validity.models import ConfigSerializer

        return self.annotate_serializer_id().custom_prefetch(
            "serializer", ConfigSerializer.objects.select_related("data_file")
        )

    def _count_per_something(self, field: str, annotate_method: str) -> dict[int | None, int]:
        qs = getattr(self, annotate_method)().values(field).annotate(cnt=Count("id", distinct=True))
        result = {}
        for values in qs:
            result[values[field]] = values["cnt"]
        return result

    def count_per_serializer(self) -> dict[int | None, int]:
        return self._count_per_something("serializer_id", "annotate_serializer_id")

    def annotate_result_stats(self, report_id: int, severity_ge: SeverityChoices = SeverityChoices.LOW):
        results_filter = Q(results__report__pk=report_id) & self._severity_filter(severity_ge, "results")
        return self.annotate(
            results_count=Count("results", filter=results_filter),
            results_passed=Count("results", filter=results_filter & Q(results__passed=True)),
            results_percentage=percentage("results_passed", "results_count"),
            compliance_passed=ExpressionWrapper(Q(results_count=F("results_passed")), output_field=BooleanField()),
        )

    @staticmethod
    def _severity_filter(severity: SeverityChoices, query_base: str = "") -> Q:
        query_path = "test__severity__in"
        if query_base:
            query_path = f"{query_base}__{query_path}"
        return Q(**{query_path: SeverityChoices.ge(severity)})

    def prefetch_results(self, report_id: int, severity_ge: SeverityChoices = SeverityChoices.LOW):
        from validity.models import ComplianceTestResult

        return self.prefetch_related(
            Prefetch(
                "results",
                queryset=ComplianceTestResult.objects.filter(self._severity_filter(severity_ge), report__pk=report_id)
                .select_related("test")
                .order_by("test__name"),
            )
        )

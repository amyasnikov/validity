from itertools import chain
from typing import TYPE_CHECKING, TypeVar

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import BigIntegerField, Case, Count, F, FloatField, OuterRef, Prefetch, Q, QuerySet, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, JSONObject
from netbox.models import RestrictedQuerySet

from validity import settings
from validity.choices import DeviceGroupByChoices, SeverityChoices


if TYPE_CHECKING:
    from validity.models.base import BaseModel


class JSONObjMixin:
    def as_json(self):
        return self.values(json=JSONObject(**{f: f for f in self.model.json_fields}))


class GitRepoQS(JSONObjMixin, RestrictedQuerySet):
    pass


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
        return self.model.objects.filter(pk__in=last_ids)

    def count_devices_and_tests(self):
        return self.aggregate(device_count=Count("devices", distinct=True), test_count=Count("tests", distinct=True))

    def delete_old(self):
        return self.filter(report=None).last_more_than(settings.store_last_results).delete()


class ConfigSerializerQS(JSONObjMixin, RestrictedQuerySet):
    pass


class NameSetQS(JSONObjMixin, RestrictedQuerySet):
    pass


class ComplianceReportQS(RestrictedQuerySet):
    def annotate_result_stats(self, groupby_field: DeviceGroupByChoices | None = None):
        def percentage(field1: str, field2: str) -> Case:
            return Case(
                When(Q(**{f"{field2}__gt": 0}), then=Value(100.0) * F(field1) / F(field2)),
                default=100.0,
                output_field=FloatField(),
            )

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

    def delete_old(self):
        return self.filter(
            pk__in=self.values_list("pk", flat=True).order_by("-created")[settings.store_reports :]
        ).delete()


_QS = TypeVar("_QS", bound=QuerySet)


def annotate_json(qs: _QS, field: str, annotate_model: type["BaseModel"]) -> _QS:
    return qs.annotate(**{f"json_{field}": annotate_model.objects.filter(pk=OuterRef(f"{field}_id")).as_json()})


class VDeviceQS(RestrictedQuerySet):
    def annotate_git_repo_id(self: _QS) -> _QS:
        from validity.models import GitRepo

        return self.annotate(
            bound_repo=Cast(KeyTextTransform("repo", "tenant__custom_field_data"), BigIntegerField())
        ).annotate(
            repo_id=Case(
                When(bound_repo__isnull=False, then=F("bound_repo")),
                default=GitRepo.objects.filter(default=True).values("id")[:1],
                output_field=BigIntegerField(),
            )
        )

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

    def annotate_json_serializer_repo(self: _QS) -> _QS:
        from validity.models import GitRepo

        return self.annotate(
            json_serializer_repo=GitRepo.objects.filter(configserializer__pk=OuterRef("serializer_id")).as_json()
        )

    def annotate_json_repo(self: _QS) -> _QS:
        from validity.models import GitRepo

        qs = self.annotate_git_repo_id()
        return annotate_json(qs, "repo", GitRepo)

    def annotate_json_serializer(self: _QS) -> _QS:
        from validity.models import ConfigSerializer

        qs = self.annotate_serializer_id().annotate_json_serializer_repo()
        return annotate_json(qs, "serializer", ConfigSerializer)

    def _count_per_something(self, field: str, annotate_method: str) -> dict[int | None, int]:
        qs = getattr(self, annotate_method)().values(field).annotate(cnt=Count("id", distinct=True))
        result = {}
        for values in qs:
            result[values[field]] = values["cnt"]
        return result

    def count_per_repo(self) -> dict[int | None, int]:
        return self._count_per_something("repo_id", "annotate_git_repo_id")

    def count_per_serializer(self) -> dict[int | None, int]:
        return self._count_per_something("serializer_id", "annotate_serializer_id")

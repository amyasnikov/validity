from itertools import chain
from typing import TYPE_CHECKING, Optional

from dcim.models import Device
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case, Count, F, FloatField, Prefetch, Q, Value, When
from django.db.models.functions import JSONObject
from netbox.models import RestrictedQuerySet

from validity.choices import DeviceGroupByChoices, SeverityChoices


if TYPE_CHECKING:
    from validity.models import ConfigSerializer, GitRepo


class JSONObjMixin:
    def as_json(self):
        return self.values(json=JSONObject(**{f: f for f in self.model.json_fields}))


class GitRepoQS(JSONObjMixin, RestrictedQuerySet):
    def from_device(self, device: Device) -> Optional["GitRepo"]:
        if device.tenant and (git_repo := device.tenant.cf.get("git_repo")):
            return git_repo
        return self.filter(default=True).first()


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


class ConfigSerializerQS(JSONObjMixin, RestrictedQuerySet):
    def from_device(self, device: Device) -> Optional["ConfigSerializer"]:
        if ser := device.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.manufacturer.cf.get("config_serializer"):
            return ser
        return None


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

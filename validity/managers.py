from itertools import chain
from typing import TYPE_CHECKING, Optional

from dcim.models import Device
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, F, Prefetch, Q
from django.db.models.functions import JSONObject
from netbox.models import RestrictedQuerySet


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
        return qs

    def last_more_than(self, than: int) -> "ComplianceTestResultQS":
        qs = self.values("device", "test").annotate(ids=ArrayAgg(F("id"), ordering="-created"))
        last_ids = chain.from_iterable(record["ids"][than:] for record in qs.iterator())
        return self.model.objects.filter(pk__in=last_ids)


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

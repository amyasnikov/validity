from typing import TYPE_CHECKING, Optional

from dcim.models import Device
from django.db.models import Prefetch
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

        return self.prefetch_related(
            Prefetch("results", ComplianceTestResult.objects.order_by("device", "-last_updated").distinct())
        )


class ConfigSerializerQS(JSONObjMixin, RestrictedQuerySet):
    def from_device(self, device: Device) -> Optional["ConfigSerializer"]:
        if ser := device.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.manufacturer.cf.get("config_serializer"):
            return ser
        return None

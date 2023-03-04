from typing import TYPE_CHECKING, Optional

from dcim.models import Device
from django.db.models import BigIntegerField, Case, Count, OuterRef, Prefetch, Q, When
from django.db.models.functions import Cast
from netbox.models import RestrictedQuerySet


if TYPE_CHECKING:
    from validity.models import ConfigSerializer, GitRepo


class GitRepoQS(RestrictedQuerySet):
    def from_device(self, device: Device) -> Optional["GitRepo"]:
        if device.tenant and (git_repo := device.tenant.cf.get("git_repo")):
            return git_repo
        return self.filter(default=True).first()

    def annotate_total_devices(self) -> "GitRepoQS":
        total_devices = Case(
            When(
                default=True, then=Count(Device.objects.filter(~Q(custom_field_data__has_key="git_repo")).values("id"))
            ),
            default=Count(
                Device.objects.select_related("tenant")
                .annotate(git_repo=Cast("tenant__custom_field_data__git_repo", BigIntegerField()))
                .filter(git_repo=OuterRef("id"))
                .values("id")
            ),
        )
        return self.annotate(total_devices=total_devices)


class ComplianceTestQS(RestrictedQuerySet):
    def pf_latest_results(self) -> "ComplianceTestQS":
        from validity.models import ComplianceTestResult

        return self.prefetch_related(
            Prefetch("results", ComplianceTestResult.objects.order_by("device", "-last_updated").distinct())
        )


class ConfigSerializerQS(RestrictedQuerySet):
    def from_device(self, device: Device) -> Optional["ConfigSerializer"]:
        if ser := device.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.cf.get("config_serializer"):
            return ser
        if ser := device.device_type.manufacturer.cf.get("config_serializer"):
            return ser
        return None

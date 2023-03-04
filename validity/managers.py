from typing import TYPE_CHECKING

from dcim.models import Device
from django.db.models import OuterRef, Prefetch
from netbox.models import RestrictedQuerySet


if TYPE_CHECKING:
    from validity.models import GitRepo


class GitRepoQS(RestrictedQuerySet):
    def for_device(self, device: Device | int) -> "GitRepo":
        if isinstance(device, int):
            device = Device.objects.get(pk=device)
        return device.cf.get("git_repo", self.get(default=True))


class ComplianceTestQS(RestrictedQuerySet):
    def pf_latest_results(self) -> "ComplianceTestQS":
        from validity.models import ComplianceTestResult

        return self.prefetch_related(
            Prefetch("results", ComplianceTestResult.objects.order_by("device", "-last_updated").distinct())
        )

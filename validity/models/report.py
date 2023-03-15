from netbox.models import ChangeLoggingMixin

from validity.managers import ComplianceReportQS
from .base import BaseReadOnlyModel


class ComplianceReport(ChangeLoggingMixin, BaseReadOnlyModel):
    objects = ComplianceReportQS.as_manager()

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"report-{self.pk}"

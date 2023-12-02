from netbox.models import ChangeLoggingMixin

from validity.managers import ComplianceReportQS
from .base import BaseReadOnlyModel


class ComplianceReport(ChangeLoggingMixin, BaseReadOnlyModel):
    objects = ComplianceReportQS.as_manager()

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        # Without this hack django.messages displays report deletion as "Deleted report-None"
        if "__str__" not in self.__dict__:
            self.__dict__["__str__"] = f"report-{self.pk}"
        return self.__dict__["__str__"]

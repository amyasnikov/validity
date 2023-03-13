from dcim.models import Device
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity import settings
from validity.managers import ComplianceTestResultQS
from .base import BaseReadOnlyModel
from .test import ComplianceTest


class ComplianceTestResult(BaseReadOnlyModel):
    test = models.ForeignKey(ComplianceTest, verbose_name=_("Test"), related_name="results", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, verbose_name=_("Device"), related_name="results", on_delete=models.CASCADE)
    passed = models.BooleanField(_("Passed"))
    explanation = models.JSONField(_("Explanation"), default=list)
    report = models.ForeignKey(
        "ComplianceReport",
        verbose_name=_("Report"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="results",
    )

    objects = ComplianceTestResultQS.as_manager()

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        passed = "passed" if self.passed else "not passed"
        return f"{self.test.name}:{self.device}:{passed}"

    def save(self, **kwargs) -> None:
        super().save(**kwargs)
        type(self).objects.filter(device=self.device_id, test=self.test_id).last_more_than(
            settings.store_last_results
        ).delete()

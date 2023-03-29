from json import JSONEncoder

from dcim.models import Device
from deepdiff.serialization import json_dumps
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.managers import ComplianceTestResultQS
from .base import BaseReadOnlyModel
from .test import ComplianceTest


class DeepDiffEncoder(JSONEncoder):
    def encode(self, o) -> str:
        return json_dumps(o)


class ComplianceTestResult(BaseReadOnlyModel):
    test = models.ForeignKey(ComplianceTest, verbose_name=_("Test"), related_name="results", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, verbose_name=_("Device"), related_name="results", on_delete=models.CASCADE)
    passed = models.BooleanField(_("Passed"))
    explanation = models.JSONField(_("Explanation"), default=list, encoder=DeepDiffEncoder)
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
        return f"{self.test.name}::{self.device}::{passed}"

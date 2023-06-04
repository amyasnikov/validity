from json import JSONEncoder

from deepdiff.serialization import json_dumps
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.managers import ComplianceTestResultQS
from .base import BaseReadOnlyModel
from .device import VDevice
from .test import ComplianceTest


class DeepDiffEncoder(JSONEncoder):
    def encode(self, o) -> str:
        return json_dumps(o, default_mapping={type({}.values()): list, type({}.keys()): list, object: str})


class ComplianceTestResult(BaseReadOnlyModel):
    test = models.ForeignKey(ComplianceTest, verbose_name=_("Test"), related_name="results", on_delete=models.CASCADE)
    device = models.ForeignKey(VDevice, verbose_name=_("Device"), related_name="results", on_delete=models.CASCADE)
    dynamic_pair = models.ForeignKey(
        VDevice, verbose_name=_("Dynamic Pair"), related_name="+", on_delete=models.CASCADE, null=True, blank=True
    )
    passed = models.BooleanField(_("Passed"))
    explanation = models.JSONField(_("Explanation"), default=list, encoder=DeepDiffEncoder, blank=True)
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
        passed = "passed" if self.passed else "failed"
        return f"{self.test.name}::{self.device}::{passed}"

import ast
from functools import partial
from typing import Any, Callable

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import SeverityChoices
from validity.compliance.eval import ExplanationalEval
from validity.managers import ComplianceTestQS
from .base import BaseModel, DataSourceMixin


class ComplianceTest(DataSourceMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"))
    severity = models.CharField(
        _("Severity"), max_length=10, choices=SeverityChoices.choices, default=SeverityChoices.MIDDLE
    )
    expression = models.TextField(_("Expression"), blank=True)
    selectors = models.ManyToManyField(to="ComplianceSelector", related_name="tests", verbose_name=_("Selectors"))

    clone_fields = ("expression", "selectors", "severity", "data_source", "data_file")
    text_db_field_name = "expression"
    evaluator_cls = partial(ExplanationalEval, load_defaults=True)

    objects = ComplianceTestQS.as_manager()

    class Meta:
        ordering = ("name",)

    def clean(self):
        super().clean()
        if self.expression:
            err = {"expression": "Invalid Python expression"}
            try:
                expr = ast.parse(self.expression)
                if len(expr.body) != 1 or not isinstance(expr.body[0], ast.Expr):
                    raise ValidationError(err)
            except SyntaxError as e:
                raise ValidationError(err) from e

    def __str__(self) -> str:
        return self.name

    def get_severity_color(self):
        return SeverityChoices.colors.get(self.severity)

    @property
    def effective_expression(self):
        return self.effective_text_field()

    def run(
        self, device, functions: dict[str, Callable], extra_names: dict[str, Any] | None = None, verbosity: int = 2
    ) -> tuple[bool, list]:
        names = {"device": device, "_poller": device.poller, "_data_source": device.data_source}
        if extra_names:
            names |= extra_names
        evaluator = self.evaluator_cls(names=names, functions=functions, verbosity=verbosity)
        passed = bool(evaluator.eval(self.effective_expression))
        return passed, evaluator.explanation

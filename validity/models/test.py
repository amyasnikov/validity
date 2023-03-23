import ast

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import SeverityChoices
from validity.managers import ComplianceTestQS
from .base import BaseModel, GitRepoLinkMixin


class ComplianceTest(GitRepoLinkMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"))
    severity = models.CharField(
        _("Severity"), max_length=10, choices=SeverityChoices.choices, default=SeverityChoices.MIDDLE
    )
    expression = models.TextField(_("Expression"), blank=True)
    selectors = models.ManyToManyField(to="ComplianceSelector", related_name="tests", verbose_name=_("Selectors"))

    clone_fields = ("expression", "selectors", "severity", "repo", "file_path")
    text_db_field_name = "expression"

    objects = ComplianceTestQS.as_manager()

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

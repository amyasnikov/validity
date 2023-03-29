import ast

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.managers import NameSetQS
from .base import BaseModel, GitRepoLinkMixin
from .test import ComplianceTest


class NameSet(GitRepoLinkMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField()
    _global = models.BooleanField(_("Global"), blank=True, default=False)
    tests = models.ManyToManyField(
        ComplianceTest, verbose_name=_("Compliance Tests"), blank=True, related_name="namesets"
    )
    definitions = models.TextField(help_text=_("Here you can write python functions or imports"), blank=True)

    objects = NameSetQS.as_manager()

    clone_fields = ("description", "_global", "tests", "definitions", "repo", "file_path")
    json_fields = ("id", "name", "description", "_global", "definitions", "file_path")
    text_db_field_name = "definitions"

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        if not self.definitions:
            return
        try:
            definitions = ast.parse(self.definitions)
        except SyntaxError as e:
            raise ValidationError({"definitions": _("Invalid python syntax")}) from e
        assign_counter = 0
        for obj in definitions.body:
            if isinstance(obj, ast.Assign):
                assign_counter += 1
                if len(obj.targets) != 1 or obj.targets[0].id != "__all__":
                    raise ValidationError({"definitions": _("Assignments besides '__all__' are not allowed")})
            elif not isinstance(obj, (ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
                raise ValidationError(
                    {"definitions": _("Only 'def', 'from-import' and 'class' statements are allowed on the top level")}
                )
        if not assign_counter:
            raise ValidationError({"definitions": _("You must define __all__")})

    @property
    def effective_definitions(self):
        return self.effective_text_field()

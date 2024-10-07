import ast
from typing import Any, Callable

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import BaseModel, DataSourceMixin
from .test import ComplianceTest


class NameSet(DataSourceMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField()
    _global = models.BooleanField(_("Global"), blank=True, default=False)
    tests = models.ManyToManyField(
        ComplianceTest, verbose_name=_("Compliance Tests"), blank=True, related_name="namesets"
    )
    definitions = models.TextField(help_text=_("Here you can write python functions or imports"), blank=True)

    clone_fields = ("description", "_global", "tests", "definitions", "data_source", "data_file")
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

    def extract(self, extra_globals: dict[str, Any] | None = None) -> dict[str, Callable]:
        all_globals = extra_globals.copy() if extra_globals else {}
        exec(self.effective_definitions, all_globals)
        __all__ = set(all_globals.get("__all__", []))
        return {k: v for k, v in all_globals.items() if k in __all__ and callable(v)}

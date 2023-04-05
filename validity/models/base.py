import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import (
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    NetBoxModel,
    RestrictedQuerySet,
    WebhooksMixin,
)

from validity.utils import git


logger = logging.getLogger(__name__)


class URLMixin:
    def get_absolute_url(self):
        return reverse(f"plugins:validity:{self._meta.model_name}", kwargs={"pk": self.pk})


def validate_file_path(path: str) -> None:
    if path.startswith("/"):
        raise ValidationError(_("Path must be relative, do not use / at the beginning"))
    if path.startswith("./"):
        raise ValidationError(_("Do not use ./ at the start of the path, start with the name of directory or file"))


class GitRepoLinkMixin(models.Model):
    repo = models.ForeignKey(
        "GitRepo", on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Git Repository")
    )
    file_path = models.CharField(_("File Path"), blank=True, max_length=255, validators=[validate_file_path])

    text_db_field_name: str

    class Meta:
        abstract = True

    def _validate_db_or_git_filled(self) -> bool:
        return True

    def clean(self) -> None:
        text_value = getattr(self, self.text_db_field_name)
        if text_value and (self.file_path or self.repo):
            raise ValidationError(_(f"You cannot set both: repo/file_path and {self.text_db_field_name}"))
        if self._validate_db_or_git_filled() and not text_value and (not self.repo or not self.file_path):
            raise ValidationError(
                {
                    self.text_db_field_name: _(
                        f"You must set either {self.text_db_field_name} or both: repo and file_path"
                    )
                }
            )

    def effective_text_field(self) -> str:
        text_db_value = getattr(self, self.text_db_field_name)
        if text_db_value:
            return text_db_value
        if not self.repo:
            logger.error("%s %s has no %s and no git repo defined", type(self).__name__, self, self.text_db_field_name)
            return ""
        git_repo = git.GitRepo.from_db(self.repo)
        file_path = git_repo.local_path / self.file_path
        try:
            with file_path.open("r") as file:
                return file.read()
        except FileNotFoundError:
            logger.error("File %s related to %s %s not found on the disk", file_path, type(self).__name__, self)
            return ""


class BaseModel(URLMixin, NetBoxModel):
    json_fields: tuple[str, ...] = ("id",)

    class Meta:
        abstract = True


class BaseReadOnlyModel(
    URLMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    WebhooksMixin,
    models.Model,
):

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        abstract = True

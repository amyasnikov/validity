import logging
from fnmatch import fnmatchcase
from typing import Annotated, Any

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from validity import di
from validity.choices import BackupMethodChoices, BackupStatusChoices
from validity.data_backup import BackupBackend
from validity.fields import EncryptedDictField
from validity.subforms import GitBackupForm, S3BackupForm
from .base import BaseModel, SubformMixin
from .data import VDataSource


logger = logging.getLogger(__name__)


class BackupPoint(SubformMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    data_source = models.ForeignKey(
        VDataSource, verbose_name=_("Data Source"), on_delete=models.CASCADE, related_name="backup_points"
    )
    backup_after_sync = models.BooleanField(
        _("Back Up After Sync"), help_text=_("Back up every time the linked Data Source is being synced"), default=True
    )
    method = models.CharField(_("Backup Method"), choices=BackupMethodChoices.choices, max_length=20)
    # TODO: add link to the docs specifying possible URLs
    url = models.CharField(_("URL"), max_length=255, validators=[URLValidator(schemes=["http", "https"])])
    ignore_rules = models.TextField(
        verbose_name=_("Ignore Rules"),
        blank=True,
        help_text=_("Patterns (one per line) matching files to ignore when uploading"),
    )
    parameters = EncryptedDictField(
        _("Parameters"), do_not_encrypt=("username", "branch", "aws_access_key_id", "archive")
    )
    last_uploaded = models.DateTimeField(_("Last Uploaded"), editable=False, blank=True, null=True)
    last_status = models.CharField(_("Last Status"), editable=False, blank=True, choices=BackupStatusChoices.choices)
    last_error = models.CharField(_("Last Error"), editable=False, blank=True)

    clone_fields = ("data_source", "url", "backup_after_sync", "method", "ignore_rules", "parameters")
    subform_type_field = "method"
    subform_json_field = "parameters"
    subforms = {"git": GitBackupForm, "S3": S3BackupForm}

    class Meta:
        verbose_name = _("Backup Point")
        verbose_name_plural = _("Backup Points")
        ordering = ("name",)
        permissions = [
            ("backup", "Can back up Data Source contents"),
        ]

    @di.inject
    def __init__(self, *args: Any, backup_backend: Annotated[BackupBackend, ...], **kwargs: Any) -> None:
        self._backup_backend = backup_backend
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if hasattr(self, "data_source") and self.data_source.type != "device_polling":
            raise ValidationError(
                {"data_source": _('Backups are supported for Data Sources with type "Device Polling" only')}
            )
        if self.method == "S3" and self.parameters.get("archive") and not self.url.endswith(".zip"):
            raise ValidationError(_('URL must end with ".zip" if archiving is chosen'))

    def get_method_color(self):
        return BackupMethodChoices.colors.get(self.method)

    def get_last_status_color(self):
        return BackupStatusChoices.colors.get(self.last_status)

    def serialize_object(self, exclude=None):
        self.parameters = self._meta.get_field("parameters").to_python(self.parameters)
        return super().serialize_object(exclude)

    def do_backup(self) -> None:
        """
        Perform backup depending on chosen method
        """
        try:
            self._backup_backend(self)
            self.last_status = BackupStatusChoices.completed
            self.last_error = ""
        except Exception as e:
            self.last_error = repr(e)
            self.last_status = BackupStatusChoices.failed
            raise
        finally:
            self.last_uploaded = timezone.now()

    def ignore_file(self, path: str) -> bool:
        for rule in self.ignore_rules.splitlines():
            if fnmatchcase(path, rule):
                return True
        return False

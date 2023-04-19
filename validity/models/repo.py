import logging
import os

from dcim.models import Device
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from jinja2 import BaseLoader, Environment

from validity.managers import GitRepoQS
from validity.utils.password import EncryptedString, PasswordField
from .base import BaseModel, validate_file_path


logger = logging.getLogger(__name__)


class GitRepo(BaseModel):
    name = models.CharField(_("Name"), max_length=255, blank=True, unique=True)
    git_url = models.CharField(
        _("Git URL"),
        max_length=255,
        validators=[URLValidator()],
        help_text=_("This URL will be used in Git operations"),
    )
    web_url = models.CharField(
        _("Web URL"),
        max_length=255,
        blank=True,
        help_text=_("This URL will be used to display links to config files. Use {{branch}} if needed"),
    )
    device_config_path = models.CharField(
        _("Device config path"),
        max_length=255,
        validators=[validate_file_path],
        help_text=_("Jinja2 syntax allowed. E.g. devices/{{device.name}}.txt"),
    )
    default = models.BooleanField(_("Default"), default=False)
    username = models.CharField(_("Username"), max_length=255, blank=True)
    encrypted_password = PasswordField(_("Password"), null=True, blank=True, default=None)
    branch = models.CharField(
        _("Branch"), max_length=255, blank=True, default="master", validators=[RegexValidator(r"[a-zA-Z_-]*")]
    )
    head_hash = models.CharField(_("Head Hash"), max_length=40, blank=True)

    objects = GitRepoQS.as_manager()
    clone_fields = ("git_url", "web_url", "device_config_path", "username", "branch")
    json_fields = (
        "id",
        "name",
        "git_url",
        "web_url",
        "device_config_path",
        "default",
        "username",
        "encrypted_password",
        "branch",
        "head_hash",
    )

    class Meta:
        verbose_name = _("Git Repository")
        verbose_name_plural = _("Git Repositories")

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if self.default:
            if (default_repo := GitRepo.objects.filter(default=True).first()) and default_repo.pk != self.pk:
                raise ValidationError({"default": _("Default Repository already exists")})

    def save(self, **kwargs) -> None:
        if not self.name:
            self.name = self.git_url.split("://")[-1]
        return super().save(**kwargs)

    def bound_devices(self) -> models.QuerySet[Device]:
        from .device import VDevice

        return (
            VDevice.objects.annotate_git_repo_id()
            .filter(repo_id=self.pk)
            .select_related("site", "device_role", "device_type__manufacturer")
        )

    @property
    def password(self):
        if self.encrypted_password:
            return self.encrypted_password.decrypt()
        return ""

    @password.setter
    def password(self, value: str | None):
        if not value:
            self.encrypted_password = None
            return
        #  112 password symbols lead to 273 encrypted symbols which is more than db field can store
        if len(value) >= 112:
            raise ValidationError(_("Password must be max 111 symbols long"))
        salt = os.urandom(16)
        self.encrypted_password = EncryptedString.from_plain_text(value, salt)

    @property
    def full_git_url(self) -> str:
        if len(splitted := self.git_url.split("://")) != 2:
            logger.warning("Possibly wrong GIT URL '%s' for repository '%s'", self.git_url, self.name)
            return self.git_url
        if not self.username and not self.encrypted_password:
            return self.git_url
        schema, rest_of_url = splitted
        return f"{schema}://{self.username}:{self.password}@{rest_of_url}"

    def rendered_device_path(self, device: Device) -> str:
        template = Environment(loader=BaseLoader()).from_string(self.device_config_path)
        return template.render(device=device)

    @property
    def rendered_web_url(self):
        template = Environment(loader=BaseLoader()).from_string(self.web_url)
        return template.render(branch=self.branch)

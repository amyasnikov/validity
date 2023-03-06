import ast
import logging
import operator
import os
import re
from functools import reduce
from typing import Generator

from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceType, Location, Manufacturer, Platform
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from jinja2 import BaseLoader, Environment
from netbox.models import (
    ChangeLoggingMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    NetBoxModel,
    WebhooksMixin,
)

from validity import settings
from validity.config_compliance import git
from validity.managers import ComplianceTestQS, ComplianceTestResultQS, ConfigSerializerQS, GitRepoQS, NameSetQS
from validity.utils.password import EncryptedString, PasswordField
from .choices import BoolOperationChoices, ConfigExtractionChoices, DynamicPairsChoices, SeverityChoices
from .config_compliance.dynamic_pairs import DynamicNamePairFilter, dpf_factory
from .queries import DeviceQS


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
                        "You must set either {self.text_db_field_name} or both: Git repository and File Path"
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
        try:
            ast.parse(self.expression)
        except SyntaxError as e:
            raise ValidationError({"expression": "Invalid Python expression"}) from e

    def __str__(self) -> str:
        return self.name

    def get_severity_color(self):
        return SeverityChoices.colors.get(self.severity)

    @property
    def effective_expression(self):
        return self.effective_text_field()


class ComplianceTestResult(
    URLMixin,
    ChangeLoggingMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    WebhooksMixin,
    models.Model,
):
    test = models.ForeignKey(ComplianceTest, verbose_name=_("Test"), related_name="results", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, verbose_name=_("Device"), related_name="results", on_delete=models.CASCADE)
    passed = models.BooleanField(_("Passed"))
    explanation = models.JSONField(_("Explanation"), default=list)

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


class ComplianceSelector(BaseModel):
    name = models.CharField(_("Selector Name"), max_length=255, unique=True)
    filter_operation = models.CharField(
        _("Multi-filter operation"),
        max_length=3,
        choices=BoolOperationChoices.choices,
        default="AND",
    )
    name_filter = models.CharField(_("Device Name Filter"), max_length=255, blank=True)
    tag_filter = models.ManyToManyField(Tag, verbose_name=_("Tag Filter"), blank=True, related_name="+")
    manufacturer_filter = models.ManyToManyField(
        Manufacturer, verbose_name=_("Manufacturer Filter"), blank=True, related_name="+"
    )
    type_filter = models.ManyToManyField(DeviceType, verbose_name=_("Device Type Filter"), blank=True, related_name="+")
    platform_filter = models.ManyToManyField(Platform, verbose_name=_("Platform Filter"), blank=True, related_name="+")
    status_filter = models.CharField(max_length=50, choices=DeviceStatusChoices, blank=True)
    location_filter = models.ManyToManyField(Location, verbose_name=_("Location Filter"), blank=True, related_name="+")
    site_filter = models.ManyToManyField(Location, verbose_name=_("Site Filter"), blank=True, related_name="+")
    dynamic_pairs = models.CharField(
        _("Dynamic Pairs"), max_length=20, choices=DynamicPairsChoices.choices, default="NO"
    )

    clone_fields = (
        "filter_operation",
        "filter_operation",
        "name_filter",
        "tag_filter",
        "manufacturer_filter",
        "type_filter",
        "platform_filter",
        "status_filter",
        "location_filter",
        "site_filter",
        "dynamic_pairs",
    )

    filters = {
        "name_filter": "name__regex",
        "tag_filter": "tags",
        "manufacturer_filter": "device_type__manufacturer",
        "type_filter": "device_type",
        "platform_filter": "platform",
        "status_filter": "status",
        "location_filter": "location",
    }

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        try:
            re.compile(self.name_filter)
        except re.error:
            raise ValidationError({"name_filter": "Invalid regular expression"})
        if self.dynamic_pairs == DynamicPairsChoices.NAME:
            if not DynamicNamePairFilter.extract_first_group(self.name_filter):
                raise ValidationError({"name_filter": "You must define regexp group if dynamic_pairs is set to NAME"})

    def get_filter_operation_color(self):
        return BoolOperationChoices.colors.get(self.filter_operation)

    def get_status_filter_color(self):
        return DeviceStatusChoices.colors.get(self.status_filter)

    def get_dynamic_pairs_color(self):
        return DynamicPairsChoices.colors.get(self.dynamic_pairs)

    def _filters_flatten(self) -> Generator[models.Q, None, None]:
        for attr_name, filter_name in self.filters.items():
            attr = getattr(self, attr_name)
            if isinstance(attr, models.Manager):
                yield from (models.Q(**{filter_name: instance}) for instance in attr.all())
            else:
                yield models.Q(**{filter_name: attr})

    @property
    def filter(self) -> models.Q:
        op = operator.or_ if self.filter_operation == BoolOperationChoices.OR else operator.and_
        return reduce(op, self._filters_flatten())

    @property
    def devices(self) -> models.QuerySet:
        return Device.objects.filter(self.filter)

    def dynamic_pair_filter(self, device: Device) -> models.Q | None:
        if dp_filter := dpf_factory(self, device).filter:
            return self.filter & dp_filter & ~models.Q(pk=device.pk)


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
        return (
            DeviceQS()
            .annotate_git_repo_id()
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


class ConfigSerializer(GitRepoLinkMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    extraction_method = models.CharField(
        _("Config Extraction Method"), max_length=10, choices=ConfigExtractionChoices.choices, default="TTP"
    )
    ttp_template = models.TextField(_("TTP Template"), blank=True)

    objects = ConfigSerializerQS.as_manager()

    clone_fields = ("ttp_template", "extraction_method", "repo", "file_path")
    json_fields = ("id", "name", "ttp_template", "extraction_method", "file_path")
    text_db_field_name = "ttp_template"

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_extraction_method_color(self):
        return ConfigExtractionChoices.colors.get(self.extraction_method)

    def _validate_db_or_git_filled(self) -> bool:
        return self.extraction_method == "TTP"

    def clean(self) -> None:
        super().clean()
        if self.extraction_method != "TTP" and self.ttp_template:
            raise ValidationError({"ttp_template": _("TTP Template must be empty if extraction method is not TTP")})
        if self.extraction_method != "TTP" and (self.repo or self.file_path):
            raise ValidationError(_("Git properties may be set only if extraction method is TTP"))
        if self.extraction_method == "TTP" and not (self.ttp_template or self.repo):
            raise ValidationError(_("TTP Template must be defined if extraction method is TTP"))

    def bound_devices(self) -> models.QuerySet[Device]:
        return (
            DeviceQS()
            .annotate_serializer_id()
            .filter(serializer_id=self.pk)
            .select_related("site", "device_role", "device_type__manufacturer")
        )

    @property
    def effective_template(self) -> str:
        return self.effective_text_field()


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
        try:
            definitions = ast.parse(self.definitions)
        except SyntaxError as e:
            raise ValidationError({"definitions": _("Invalid python syntax")}) from e
        for obj in definitions.body:
            if isinstance(obj, ast.Assign):
                if len(obj.targets) != 1 or obj.targets[0].id != "__all__":
                    raise ValidationError({"definitions": _("Assignments besides '__all__' are not allowed")})
            elif not isinstance(obj, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
                raise ValidationError(
                    {"definitions": _("Only 'import' and 'def' statements are allowed on the top level")}
                )

    @property
    def effective_definitions(self):
        return self.effective_text_field()

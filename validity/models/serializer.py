from dcim.models import Device
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import ConfigExtractionChoices
from validity.managers import ConfigSerializerQS
from .base import BaseModel, GitRepoLinkMixin


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
        from .device import VDevice

        return (
            VDevice.objects.annotate_serializer_id()
            .filter(serializer_id=self.pk)
            .select_related("site", "device_role", "device_type__manufacturer")
        )

    @property
    def effective_template(self) -> str:
        return self.effective_text_field()

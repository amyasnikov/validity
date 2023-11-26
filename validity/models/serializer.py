from dcim.models import Device
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import ConfigExtractionChoices
from validity.netbox_changes import DEVICE_ROLE_RELATION
from .base import BaseModel, DataSourceMixin


class ConfigSerializer(DataSourceMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    extraction_method = models.CharField(
        _("Config Extraction Method"), max_length=10, choices=ConfigExtractionChoices.choices, default="TTP"
    )
    ttp_template = models.TextField(_("TTP Template"), blank=True)

    clone_fields = ("ttp_template", "extraction_method", "data_source", "data_file")
    text_db_field_name = "ttp_template"

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_extraction_method_color(self):
        return ConfigExtractionChoices.colors.get(self.extraction_method)

    @property
    def _validate_db_or_git_filled(self) -> bool:
        return self.extraction_method == "TTP"

    def clean(self) -> None:
        super().clean()
        if self.extraction_method != "TTP" and self.ttp_template:
            raise ValidationError({"ttp_template": _("TTP Template must be empty if extraction method is not TTP")})
        if self.extraction_method != "TTP" and (self.data_source or self.data_file):
            raise ValidationError(_("Git properties may be set only if extraction method is TTP"))
        if self.extraction_method == "TTP" and not (self.ttp_template or self.data_source):
            raise ValidationError(_("TTP Template must be defined if extraction method is TTP"))

    @property
    def bound_devices(self) -> models.QuerySet[Device]:
        from .device import VDevice

        return (
            VDevice.objects.annotate_serializer_id()
            .filter(serializer_id=self.pk)
            .select_related("site", DEVICE_ROLE_RELATION, "device_type__manufacturer")
        )

    @property
    def effective_template(self) -> str:
        return self.effective_text_field()

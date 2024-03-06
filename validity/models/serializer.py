from dcim.models import Device
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import ExtractionMethodChoices
from validity.compliance.serialization import serialize
from validity.netbox_changes import DEVICE_ROLE_RELATION
from validity.subforms import (
    RouterOSSerializerForm,
    TEXTFSMSerializerForm,
    TTPSerializerForm,
    XMLSerializerForm,
    YAMLSerializerForm,
)
from .base import BaseModel, DataSourceMixin, SubformMixin


class Serializer(SubformMixin, DataSourceMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    extraction_method = models.CharField(_("Extraction Method"), max_length=10, choices=ExtractionMethodChoices.choices)
    template = models.TextField(_("Template"), blank=True)
    parameters = models.JSONField(_("Parameters"), default=dict, blank=True)

    clone_fields = ("template", "extraction_method", "data_source", "data_file")
    text_db_field_name = "template"
    requires_template = {"TTP", "TEXTFSM"}
    _serialize = serialize
    subform_json_field = "parameters"
    subform_type_field = "extraction_method"
    subforms = {
        "ROUTEROS": RouterOSSerializerForm,
        "XML": XMLSerializerForm,
        "TTP": TTPSerializerForm,
        "TEXTFSM": TEXTFSMSerializerForm,
        "YAML": YAMLSerializerForm,
    }

    class Meta:
        ordering = ("name",)
        default_permissions = ()

    def __str__(self) -> str:
        return self.name

    def get_extraction_method_color(self):
        return ExtractionMethodChoices.colors.get(self.extraction_method)

    @property
    def _validate_db_or_git_filled(self) -> bool:
        return self.extraction_method in self.requires_template

    def clean(self) -> None:
        super().clean()
        if self.extraction_method not in self.requires_template and self.template:
            raise ValidationError({"template": _("Template must be empty for selected extraction method")})
        if self.extraction_method not in self.requires_template and (self.data_source or self.data_file):
            raise ValidationError(_("Data Source/File properties cannot be set for selected extraction method"))
        if self.extraction_method in self.requires_template and not (
            self.template or self.data_source and self.data_file
        ):
            raise ValidationError(_("Template must be defined for selected extraction method"))

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

    def serialize(self, data: str) -> dict:
        return self._serialize(self, data)

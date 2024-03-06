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
)

from validity.netbox_changes import EventRulesMixin


logger = logging.getLogger(__name__)


class URLMixin:
    def get_absolute_url(self):
        return reverse(f"plugins:validity:{self._meta.model_name}", kwargs={"pk": self.pk})


class DataSourceMixin(models.Model):
    text_db_field_name: str

    data_source = models.ForeignKey(
        to="validity.VDataSource",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        help_text=_("Remote data source"),
    )
    data_file = models.ForeignKey(
        to="validity.VDataFile", on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )

    class Meta:
        abstract = True

    @property
    def _validate_db_or_git_filled(self) -> bool:
        return True

    def clean(self) -> None:
        text_value = getattr(self, self.text_db_field_name)
        if text_value and (self.data_source or self.data_file):
            raise ValidationError(_(f"You cannot set both: data_source/data_file and {self.text_db_field_name}"))
        if self._validate_db_or_git_filled and not text_value and (not self.data_source or not self.data_file):
            raise ValidationError(
                {
                    self.text_db_field_name: _(
                        f"You must set either {self.text_db_field_name} or both: data_source and data_file"
                    )
                }
            )

    def effective_text_field(self) -> str:
        text_db_value = getattr(self, self.text_db_field_name)
        if text_db_value:
            return text_db_value
        if not self.data_file:
            logger.error("%s %s has no %s and no Data File defined", type(self).__name__, self, self.text_db_field_name)
            return ""
        return self.data_file.data_as_string


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
    EventRulesMixin,
    models.Model,
):
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        abstract = True


class SubformMixin:
    subform_json_field: str
    subform_type_field: str
    subforms: dict

    @property
    def subform_type(self):
        return getattr(self, self.subform_type_field)

    @subform_type.setter
    def subform_type(self, value):
        setattr(self, self.subform_type_field, value)

    @property
    def subform_cls(self):
        return self.subforms[self.subform_type]

    @property
    def subform_json(self):
        return getattr(self, self.subform_json_field)

    @subform_json.setter
    def subform_json(self, value):
        setattr(self, self.subform_json_field, value)

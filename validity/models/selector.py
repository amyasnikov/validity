import operator
import re
from functools import reduce
from typing import Generator

from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from extras.models import Tag
from tenancy.models import Tenant

from validity.choices import BoolOperationChoices, DynamicPairsChoices
from validity.compliance.dynamic_pairs import DynamicPairNameFilter, dpf_factory
from validity.utils.misc import reraise
from .base import BaseModel
from .device import VDevice


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
    site_filter = models.ManyToManyField(Site, verbose_name=_("Site Filter"), blank=True, related_name="+")
    tenant_filter = models.ManyToManyField(Tenant, verbose_name=_("Tenant Filter"), blank=True, related_name="+")
    dynamic_pairs = models.CharField(
        _("Dynamic Pairs"), max_length=20, choices=DynamicPairsChoices.choices, default="NO"
    )
    dp_tag_prefix = models.CharField(_("Dynamic Pair Tag Prefix"), max_length=255, blank=True)

    clone_fields = (
        "filter_operation",
        "name_filter",
        "tag_filter",
        "manufacturer_filter",
        "type_filter",
        "platform_filter",
        "status_filter",
        "location_filter",
        "site_filter",
        "tenant_filter",
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
        "site_filter": "site",
        "tenant_filter": "tenant",
    }

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        with reraise(re.error, ValidationError, {"name_filter": _("Invalid regular expression")}):
            re.compile(self.name_filter)
        if self.dynamic_pairs == DynamicPairsChoices.NAME:
            if not DynamicPairNameFilter.extract_first_group(self.name_filter):
                raise ValidationError(
                    {"name_filter": _("You must define regexp group if dynamic_pairs is set to NAME")}
                )
        elif self.dynamic_pairs == DynamicPairsChoices.TAG and not self.dp_tag_prefix:
            raise ValidationError({"dp_tag_prefix": _("You must define Tag Prefix if dynamic_pairs is set to TAG")})
        if self.dp_tag_prefix and self.dynamic_pairs != DynamicPairsChoices.TAG:
            raise ValidationError({"dp_tag_prefix": _("This field may be used only if dynamic_pairs is set to TAG")})

    def get_filter_operation_color(self):
        return BoolOperationChoices.colors.get(self.filter_operation)

    def get_status_filter_color(self):
        return DeviceStatusChoices.colors.get(self.status_filter)

    def get_dynamic_pairs_color(self):
        return DynamicPairsChoices.colors.get(self.dynamic_pairs)

    def q_objects(self) -> Generator[models.Q, None, None]:
        for attr_name, filter_name in self.filters.items():
            attr = getattr(self, attr_name)
            if isinstance(attr, models.Manager):
                q = reduce(operator.or_, (models.Q(**{filter_name: instance}) for instance in attr.all()), models.Q())
                if q:
                    yield q
            elif attr:
                yield models.Q(**{filter_name: attr})

    @property
    def filter(self) -> models.Q:
        op = operator.or_ if self.filter_operation == BoolOperationChoices.OR else operator.and_
        return reduce(op, self.q_objects(), models.Q())

    @property
    def devices(self) -> models.QuerySet:
        return VDevice.objects.filter(self.filter).set_selector(self)

    def dynamic_pair_filter(self, device: Device) -> models.Q | None:
        if dp_filter := dpf_factory(self, device).filter:
            return dp_filter & ~models.Q(pk=device.pk)

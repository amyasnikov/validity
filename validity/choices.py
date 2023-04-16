from typing import Optional

from django.db.models import TextChoices
from django.db.models.enums import ChoicesMeta
from django.utils.translation import gettext_lazy as _


class ColoredChoiceMeta(ChoicesMeta):
    """
    Allows to write choice fields with a color like that:
        option1 = 'red'
        option2 = ('option2', 'yellow')
        option3 = ('option3', 'Option3', 'green')
    """

    def __new__(cls, name, bases, namespace, **kwargs):
        colors = {}
        member_names = namespace._member_names
        namespace._member_names = []
        for key in member_names:
            attr = namespace.pop(key)
            if isinstance(attr, str):
                colors[key] = attr
                attr = key
            elif isinstance(attr, (list, tuple)):
                colors[key] = attr[-1]
                attr = attr[:-1]
            namespace[key] = attr
        namespace["_colors"] = colors
        namespace._member_names.remove("_colors")
        return super().__new__(cls, name, bases, namespace, **kwargs)

    @property
    def colors(self):
        return self._colors


class BoolOperationChoices(TextChoices, metaclass=ColoredChoiceMeta):
    OR = "OR", _("OR"), "purple"
    AND = "AND", _("AND"), "blue"


class DynamicPairsChoices(TextChoices, metaclass=ColoredChoiceMeta):
    NO = "NO", _("NO"), "red"
    NAME = "NAME", _("By name"), "blue"


class SeverityChoices(TextChoices, metaclass=ColoredChoiceMeta):
    LOW = "LOW", _("LOW"), "green"
    MIDDLE = "MIDDLE", _("MIDDLE"), "yellow"
    HIGH = "HIGH", _("HIGH"), "red"


class ConfigExtractionChoices(TextChoices, metaclass=ColoredChoiceMeta):
    TTP = "TTP", "TTP", "purple"
    YAML = "YAML", "YAML", "info"


class DeviceGroupByChoices(TextChoices):
    DEVICE = "device__name", _("Device")
    DEVICE_TYPE = "device__device_type__slug", _("Device Type")
    MANUFACTURER = "device__device_type__manufacturer__slug", _("Manufacturer")
    DEVICE_ROLE = "device__device_role__slug", _("Device Role")
    TENANT = "device__tenant__slug", _("Tenant")
    PLATFORM = "device__platform__slug", _("Platform")
    LOCATION = "device__location__slug", _("Location")
    SITE = "device__site__slug", _("Site")
    TEST = "test__name", _("Test")

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls._value2member_map_

    @classmethod
    def member(cls, value: str) -> Optional["DeviceGroupByChoices"]:
        return cls._value2member_map_.get(value)  # type: ignore

    def viewname(self) -> str:
        view_prefixes = {self.TENANT: "tenancy:", self.TEST: "plugins:validity:compliance"}
        default_prefix = "dcim:"
        model_name = self.value.split("__")[-2].replace("_", "")
        return view_prefixes.get(self, default_prefix) + model_name

    def pk_field(self):
        pk_path = self.value.split("__")[:-1] + ["pk"]
        return "__".join(pk_path)

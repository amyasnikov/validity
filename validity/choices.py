from typing import Any, Optional, TypeVar

from django.db.models import IntegerChoices, TextChoices
from django.db.models.enums import ChoicesMeta
from django.utils.translation import gettext_lazy as _

from validity.netbox_changes import DEVICE_ROLE_RELATION


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
        namespace._member_names = type(namespace._member_names)()  # clean container
        for key in member_names:
            attr = namespace.pop(key)
            if isinstance(attr, str):
                colors[key] = attr
                attr = key
            elif isinstance(attr, (list, tuple)):
                colors[key] = attr[-1]
                attr = attr[:-1]
            namespace[key] = attr
        namespace["__colors__"] = colors
        return super().__new__(cls, name, bases, namespace, **kwargs)

    @property
    def colors(self):
        return self.__colors__


_Type = TypeVar("_Type")


class MemberMixin:
    @classmethod
    def member(cls: type[_Type], value: Any) -> Optional[_Type]:
        return cls._value2member_map_.get(value)  # type: ignore


class BoolOperationChoices(TextChoices, metaclass=ColoredChoiceMeta):
    OR = "OR", _("OR"), "purple"
    AND = "AND", _("AND"), "blue"


class DynamicPairsChoices(TextChoices, metaclass=ColoredChoiceMeta):
    NO = "NO", _("NO"), "red"
    NAME = "NAME", _("By name"), "blue"
    TAG = "TAG", _("By tag"), "purple"


class SeverityChoices(MemberMixin, TextChoices, metaclass=ColoredChoiceMeta):
    LOW = "LOW", _("LOW"), "green"
    MIDDLE = "MIDDLE", _("MIDDLE"), "yellow"
    HIGH = "HIGH", _("HIGH"), "red"

    @classmethod
    def from_request(cls, request):
        severity_query = request.GET.get("severity_ge")
        if isinstance(severity_query, str):
            severity_query = severity_query.upper()
        severity_ge = SeverityChoices.member(severity_query)
        if not severity_ge:
            severity_ge = SeverityChoices.LOW
        return severity_ge

    @classmethod
    def ge(cls, severity: "SeverityChoices") -> list[str]:
        index = SeverityChoices.labels.index(severity.label)
        return cls.labels[index:]


class ExtractionMethodChoices(TextChoices, metaclass=ColoredChoiceMeta):
    TTP = "TTP", "TTP", "purple"
    TEXTFSM = "TEXTFSM", "TEXTFSM", "blue"
    YAML = "YAML", "YAML", "info"
    XML = "XML", "XML", "orange"
    ROUTEROS = "ROUTEROS", "ROUTEROS", "green"


class DeviceGroupByChoices(MemberMixin, TextChoices):
    DEVICE = "device__name", _("Device")
    DEVICE_TYPE = "device__device_type__slug", _("Device Type")
    MANUFACTURER = "device__device_type__manufacturer__slug", _("Manufacturer")
    DEVICE_ROLE = f"device__{DEVICE_ROLE_RELATION}__slug", _("Device Role")
    TENANT = "device__tenant__slug", _("Tenant")
    PLATFORM = "device__platform__slug", _("Platform")
    LOCATION = "device__location__slug", _("Location")
    SITE = "device__site__slug", _("Site")
    TEST = "test__name", _("Test")

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls._value2member_map_

    def viewname(self) -> str:
        view_prefixes = {self.TENANT: "tenancy:", self.TEST: "plugins:validity:compliance"}
        default_prefix = "dcim:"
        model_name = self.value.split("__")[-2].replace("_", "")
        return view_prefixes.get(self, default_prefix) + model_name

    def pk_field(self):
        pk_path = self.value.split("__")[:-1] + ["pk"]
        return "__".join(pk_path)


class ConnectionTypeChoices(TextChoices, metaclass=ColoredChoiceMeta):
    netmiko = "netmiko", "netmiko", "blue"
    requests = "requests", "requests", "info"
    scrapli_netconf = "scrapli_netconf", "scrapli_netconf", "orange"

    __command_types__ = {"netmiko": "CLI", "scrapli_netconf": "netconf", "requests": "json_api"}

    @property
    def acceptable_command_type(self) -> "CommandTypeChoices":
        return CommandTypeChoices[self.__command_types__[self.name]]


class CommandTypeChoices(TextChoices, metaclass=ColoredChoiceMeta):
    CLI = "CLI", "CLI", "blue"
    netconf = "netconf", "orange"
    json_api = "json_api", "JSON API", "info"


class ExplanationVerbosityChoices(IntegerChoices):
    disabled = 0, _("0 - Disabled")
    medium = 1, _("1 - Medium")
    maximum = 2, _("2 - Maximum")


class JSONAPIMethodChoices(TextChoices):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"

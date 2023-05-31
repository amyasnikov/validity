from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from dcim.models import Device

from validity.utils.misc import reraise
from ..exceptions import DeviceConfigError


@dataclass
class BaseDeviceConfig:
    device: Device
    plain_config: str
    last_modified: datetime | None = None
    serialized: dict | list | None = None

    _config_classes: ClassVar[dict[str, type]] = {}

    @classmethod
    def from_device(cls, device: Device) -> "BaseDeviceConfig":
        """
        Get DeviceConfig from dcim.models.Device
        Device MUST be annotated with ".plain_config"
        Device MUST be annotated with ".serializer" pointing to appropriate config serializer instance
        """
        with reraise((AssertionError, FileNotFoundError, AttributeError), DeviceConfigError):
            assert getattr(device, "data_file", None), f"{device} has no bound data file"
            assert getattr(device, "serializer", None), f"{device} has no bound serializer"
            return cls._config_classes[device.serializer.extraction_method]._from_device(device)

    @classmethod
    def _from_device(cls, device: Device) -> "BaseDeviceConfig":         
        instance = cls(device, device.data_file.data_as_string, device.data_file.last_updated)
        instance.serialize()
        return instance

    @abstractmethod
    def serialize(self, override: bool = False) -> None:
        pass


class DeviceConfigMeta(type):
    def __init__(cls, name, bases, dct):
        if name != "DeviceConfig":
            BaseDeviceConfig._config_classes[dct["extract_method"]] = cls
        super().__init__(name, bases, dct)


class DeviceConfig(BaseDeviceConfig, metaclass=DeviceConfigMeta):
    pass

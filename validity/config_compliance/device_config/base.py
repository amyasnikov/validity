from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from dcim.models import Device
from django.utils.timezone import make_aware

from validity import settings
from validity.utils.misc import reraise
from ..exceptions import DeviceConfigError


@dataclass
class BaseDeviceConfig:
    device: Device
    config_path: Path
    last_modified: datetime | None = None
    serialized: dict | list | None = None
    _git_folder: ClassVar[Path] = settings.git_folder
    _config_classes: ClassVar[dict[str, type]] = {}

    @classmethod
    def _full_config_path(cls, device: Device) -> Path:
        return cls._git_folder / device.repo.name / device.repo.rendered_device_path(device)

    @classmethod
    def from_device(cls, device: Device) -> "BaseDeviceConfig":
        """
        Get DeviceConfig from dcim.models.Device
        Device MUST be annotated with ".repo" pointing to a repo with device config file
        Device MUST be annotated with ".serializer" pointing to appropriate config serializer instance
        """
        with reraise((AssertionError, FileNotFoundError), DeviceConfigError):
            assert getattr(device, "repo", None), f"{device} has no bound repository"
            assert getattr(device, "serializer", None), f"{device} has no bound serializer"
            return cls._config_classes[device.serializer.extraction_method]._from_device(device)

    @classmethod
    def _from_device(cls, device: Device) -> "BaseDeviceConfig":
        with reraise(AttributeError, DeviceConfigError):
            device_path = cls._full_config_path(device)
            last_modified = None
            if device_path.is_file():
                lm_timestamp = device_path.stat().st_mtime
                last_modified = make_aware(datetime.fromtimestamp(lm_timestamp))
            instance = cls(device, device_path, last_modified)
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

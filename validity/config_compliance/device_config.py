import json
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import yaml
from dcim.models import Device
from django.utils.timezone import make_aware
from ttp import ttp

from validity import settings
from .exceptions import DeviceConfigError


@dataclass
class TTPTemplate:
    name: str
    template: str = ""  # according to TTP API this may contain a template iteslf or a filepath


@dataclass
class DeviceConfig:
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
    def from_device(cls, device: Device) -> "DeviceConfig":
        """
        Get DeviceConfig from dcim.models.Device
        Device MUST be annotated with ".repo" pointing to a repo with device config file
        Device MUST be annotated with ".serializer" pointing to appropriate config serializer instance
        """
        assert hasattr(device, "repo"), "Device must be annotated with .repo"
        assert hasattr(device, "serializer"), "Device must be annotated with .serializer"
        return cls._config_classes[device.serializer.extraction_method]._from_device(device)

    @classmethod
    def _from_device(cls, device: Device) -> "DeviceConfig":
        try:
            device_path = cls._full_config_path(device)
            last_modified = None
            if device_path.is_file():
                lm_timestamp = device_path.stat().st_mtime
                last_modified = make_aware(datetime.fromtimestamp(lm_timestamp))
            instance = cls(device, device_path, last_modified)
            instance.serialize()
            return instance
        except AttributeError as e:
            raise DeviceConfigError(str(e)) from e

    @abstractmethod
    def serialize(self, override: bool = False) -> None:
        pass


class DeviceConfigMeta(type):
    def __init__(cls, name, bases, dct):
        DeviceConfig._config_classes[dct["extract_method"]] = cls
        super().__init__(name, bases, dct)


@dataclass
class TTPDeviceConfig(DeviceConfig, metaclass=DeviceConfigMeta):
    extract_method: ClassVar[str] = "TTP"
    _template: TTPTemplate = field(init=False)

    def __post_init__(self):
        self._template = TTPTemplate(
            name=self.device.serializer.name, template=self.device.serializer.effective_template
        )

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            parser = ttp(data=str(self.config_path), template=self._template.template)
            parser.parse()
            try:
                self.serialized = parser.result()[0][0]
            except IndexError as e:
                raise DeviceConfigError(f"Invalid parsed config for {self.device}: {parser.result()}") from e


class JSONDeviceConfig(DeviceConfig, metaclass=DeviceConfigMeta):
    extract_method: ClassVar[str] = "JSON"

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            with self.config_path.open("r") as cfg_file:
                try:
                    self.serialized = json.load(cfg_file)
                except json.JSONDecodeError as e:
                    raise DeviceConfigError(f"Trying to parse invalid JSON as device config for {self.device}") from e


class YAMLDeviceConfig(DeviceConfig, metaclass=DeviceConfigMeta):
    extract_method: ClassVar[str] = "YAML"

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            with self.config_path.open("r") as cfg_file:
                try:
                    self.serialized = yaml.safe_load(cfg_file)
                except yaml.YAMLError as e:
                    raise DeviceConfigError(f"Trying to parse invalid YAML as device config for {self.device}") from e

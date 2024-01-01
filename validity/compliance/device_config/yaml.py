from typing import ClassVar

import yaml

from validity.utils.misc import reraise
from ..exceptions import SerializationError
from .base import DeviceConfig


class YAMLDeviceConfig(DeviceConfig):
    extract_method: ClassVar[str] = "YAML"

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            with reraise(
                yaml.YAMLError,
                SerializationError,
                f"Trying to parse invalid YAML as device config for {self.device}",
            ):
                self.serialized = yaml.safe_load(self.plain_config)

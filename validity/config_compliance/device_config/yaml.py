from typing import ClassVar

import yaml

from validity.utils.misc import reraise
from ..exceptions import DeviceConfigError
from .base import DeviceConfig


class YAMLDeviceConfig(DeviceConfig):
    extract_method: ClassVar[str] = "YAML"

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            with self.config_path.open("r") as cfg_file:
                with reraise(
                    yaml.YAMLError,
                    DeviceConfigError,
                    msg=f"Trying to parse invalid YAML as device config for {self.device}",
                ):
                    self.serialized = yaml.safe_load(cfg_file)

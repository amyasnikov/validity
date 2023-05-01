from dataclasses import dataclass, field
from typing import ClassVar

from ttp import ttp

from validity.utils.misc import reraise
from ..exceptions import DeviceConfigError
from .base import DeviceConfig


@dataclass
class TTPTemplate:
    name: str
    template: str = ""  # according to TTP API this may contain a template itself or a filepath


@dataclass
class TTPDeviceConfig(DeviceConfig):
    extract_method: ClassVar[str] = "TTP"
    _template: TTPTemplate = field(init=False)

    def __post_init__(self):
        self._template = TTPTemplate(
            name=self.device.serializer.name, template=self.device.serializer.effective_template
        )

    def serialize(self, override: bool = False) -> None:
        if not self.serialized or override:
            if not self.config_path.is_file():
                raise DeviceConfigError(f"{self.config_path} does not exist")
            parser = ttp(data=str(self.config_path), template=self._template.template)
            parser.parse()
            with reraise(
                IndexError, DeviceConfigError, msg=f"Invalid parsed config for {self.device}: {parser.result()}"
            ):
                self.serialized = parser.result()[0][0]

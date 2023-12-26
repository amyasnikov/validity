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
            parser = ttp(data=self.plain_config, template=self._template.template)
            parser.parse()
            with reraise(IndexError, DeviceConfigError, f"Invalid parsed config for {self.device}: {parser.result()}"):
                self.serialized = parser.result()[0][0]

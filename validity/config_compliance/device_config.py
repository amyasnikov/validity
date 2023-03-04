from collections import defaultdict
import logging
from dataclasses import dataclass

from dcim.models import Device
from ttp import ttp

from ..models import GitRepo


logger = logging.getLogger(__name__)


@dataclass
class TTPTemplate:
    name: str
    template: str = ''


@dataclass
class DeviceConfig:
    device: Device
    plain: str = ""
    template: TTPTemplate | None = None
    serialized: dict | list | None = None

    @classmethod
    def from_device(cls, device: Device, git_repo: GitRepo) -> 'DeviceConfig':
        


def serialize_configs(*configs: DeviceConfig, override: bool = False) -> None:
    parser = ttp()
    configs_by_template = defaultdict(list)
    templates = {}
    for config in configs:
        if config.template:
            configs_by_template[config.template.name].append(config)
            templates.setdefault(config.template.name, config.template.template)
    for template_name, config_group in configs_by_template.items():
        parser.add_template(template=templates[template_name], template_name=template_name)
        for config in config_group:
            parser.add_input(data=config.plain, template_name=template_name)
    parser.parse()
    for template_name, config_group in configs_by_template.items():
        result = parser.result(templates=[template_name])
        for config, serialized in zip(config_group, result):
            if override or config.serialized is not None:
                config.serialized = serialized

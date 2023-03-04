from collections import defaultdict
import logging
from dataclasses import dataclass
from jinja2 import Environment, BaseLoader


from dcim.models import Device
from ttp import ttp

from validity import settings
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class TTPTemplate:
    name: str
    template: str = ''  # according to TTP API this may contain a template iteslf or a filepath


@dataclass
class DeviceConfig:
    device: Device
    config_path: Path
    template: TTPTemplate | None = None
    serialized: dict | list | None = None

    @staticmethod
    def eval_device_path(path: str, device: Device) -> str:
        template = Environment(loader=BaseLoader()).from_string(path)
        return template.render(device=device)

    @classmethod
    def from_device(cls, device: Device) -> 'DeviceConfig':
        """
        Get DeviceConfig from dcim.models.Device
        Device MUST be annotated with ".git_repo" pointing to a repo with device config file
        Device MUST be annotated with ".serializer" pointing to appropriate config serializer instance
        """
        assert hasattr(device, 'git_repo'), 'Device must be annotated with .git_repo'
        assert hasattr(device, 'serializer'), 'Device must be annotated with .serializer'
        device_path = settings.git_folder / cls.eval_device_path(device.git_repo.device_config_path, device)
        template = TTPTemplate(name=device.serializer.name, template=device.serializer.effective_template)
        return cls(device, device_path, template)


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
            parser.add_input(data=config.config_path, template_name=template_name)
    parser.parse()
    for template_name, config_group in configs_by_template.items():
        result = parser.result(templates=[template_name])
        for config, serialized in zip(config_group, result):
            if override or config.serialized is not None:
                config.serialized = serialized

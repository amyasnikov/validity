import json
from unittest.mock import Mock

import pytest
import yaml
from factories import DeviceFactory

from validity.config_compliance.device_config import DeviceConfig


@pytest.fixture
def set_git_folder(tests_root):
    DeviceConfig._git_folder = tests_root


JSON_CONFIG = """
{
    "ntp_servers": [
        "1.1.1.1",
        "2.2.2.2"
    ]
}
"""

YAML_CONFIG = """
ntp_servers:
- 1.1.1.1
- 2.2.2.2
- 3.3.3.3
"""

TTP_TEMPLATE = """
<group name="interfaces">
interface {{ interface }}
 ip address {{ ip }} {{ mask }}
</group>
"""

TTP_CONFIG = """
interface Vlan163
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 ip address 192.168.10.3 255.255.255.0
"""

TTP_SERIALIZED = {
    "interfaces": [
        {"interface": "Vlan163", "ip": "10.0.10.3", "mask": "255.255.255.0"},
        {"interface": "GigabitEthernet6/41", "ip": "192.168.10.3", "mask": "255.255.255.0"},
    ]
}


@pytest.mark.parametrize(
    "extraction_method, file_content, serialized",
    [
        pytest.param("JSON", JSON_CONFIG, json.loads(JSON_CONFIG), id="JSON"),
        pytest.param("YAML", YAML_CONFIG, yaml.safe_load(YAML_CONFIG), id="YAML"),
        pytest.param("TTP", TTP_CONFIG, TTP_SERIALIZED, id="TTP"),
    ],
)
@pytest.mark.django_db
def test_device_congig(temp_file_and_folder, set_git_folder, tests_root, extraction_method, file_content, serialized):
    device = DeviceFactory()
    device.serializer = Mock(name="some_serializer", extraction_method=extraction_method)
    if extraction_method == "TTP":
        device.serializer.effective_template = TTP_TEMPLATE
    temp_file_and_folder(tests_root, "some_repo", "config_file.txt", file_content)
    device.repo = Mock(rendered_device_path=Mock(return_value="config_file.txt"))
    device.repo.name = "some_repo"
    device_config = DeviceConfig.from_device(device)
    assert extraction_method in type(device_config).__name__
    assert device_config.serialized == serialized

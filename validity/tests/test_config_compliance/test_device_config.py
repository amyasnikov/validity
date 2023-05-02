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


ROUTEROS_CONFIG = """
# comment
/system script
add dont-require-permissions=no name=test_script owner=admin policy=\\
    ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon source=\\
    "/ppp active print\\
    \\n/system resource print\\
    \\n/ip address print\\
    \\n"
/ip pool
add name=pool1 ranges=192.168.1.100-192.168.1.199
add name=pool2 ranges=192.168.2.100-192.168.2.199
/ip service
set www-ssl certificate=some_cert disabled=no
/ipv6 settings
set disable-ipv6=yes max-neighbor-entries=8192
/interface ethernet
set [ find default-name=ether1 ] comment="some comment"
"""

ROUTEROS_SERIALIZED = {
    "interface": {
        "ethernet": {"values": [{"comment": "some comment", "find_by": [{"key": "default-name", "value": "ether1"}]}]}
    },
    "ip": {
        "pool": {
            "values": [
                {"name": "pool1", "ranges": "192.168.1.100-192.168.1.199"},
                {"name": "pool2", "ranges": "192.168.2.100-192.168.2.199"},
            ]
        },
        "service": {"values": [{"certificate": "some_cert", "disabled": False, "name": "www-ssl"}]},
    },
    "ipv6": {"settings": {"properties": {"disable-ipv6": True, "max-neighbor-entries": 8192}}},
    "system": {
        "script": {
            "values": [
                {
                    "dont-require-permissions": False,
                    "name": "test_script",
                    "owner": "admin",
                    "policy": "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon",
                    "source": (
                        "/ppp active print\\\n    \\n/system resource print\\\n    \\n/ip address print\\\n    \\n"
                    ),
                }
            ]
        }
    },
}


@pytest.mark.parametrize(
    "extraction_method, file_content, serialized",
    [
        pytest.param("YAML", JSON_CONFIG, json.loads(JSON_CONFIG), id="YAML-JSON"),
        pytest.param("YAML", YAML_CONFIG, yaml.safe_load(YAML_CONFIG), id="YAML"),
        pytest.param("TTP", TTP_CONFIG, TTP_SERIALIZED, id="TTP"),
        pytest.param("ROUTEROS", ROUTEROS_CONFIG, ROUTEROS_SERIALIZED, id="ROUTEROS"),
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
    assert extraction_method.lower() in type(device_config).__name__.lower()
    assert device_config.serialized == serialized

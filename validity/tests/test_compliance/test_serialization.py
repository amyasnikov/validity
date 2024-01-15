import json

import pytest
import yaml

from validity.compliance.serialization import serialize


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
    "extraction_method, contents, template, serialized",
    [
        pytest.param("YAML", JSON_CONFIG, "", json.loads(JSON_CONFIG), id="YAML-JSON"),
        pytest.param("YAML", YAML_CONFIG, "", yaml.safe_load(YAML_CONFIG), id="YAML"),
        pytest.param("TTP", TTP_CONFIG, TTP_TEMPLATE, TTP_SERIALIZED, id="TTP"),
        pytest.param("ROUTEROS", ROUTEROS_CONFIG, "", ROUTEROS_SERIALIZED, id="ROUTEROS"),
    ],
)
@pytest.mark.django_db
def test_serialization(extraction_method, contents, template, serialized):
    serialize_result = serialize(extraction_method, contents, template)
    assert serialize_result == serialized

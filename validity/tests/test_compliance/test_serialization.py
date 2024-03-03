import json
from unittest.mock import Mock

import pytest
import yaml

from validity.compliance.serialization import serialize
from validity.compliance.serialization.common import postprocess_jq


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


TEXTFSM_TEMPLATE = r"""Value INTF (\S+)
Value ADDR (\S+)
Value STATUS (up|down)
Value PROTO (up|down)

Start
  ^${INTF}\s+${ADDR}\s+\w+\s+\w+\s+${STATUS}\s+${PROTO} -> Record
"""

TEXTFSM_STATE = """
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0/0            15.0.15.1       YES manual up                    up
FastEthernet0/1            10.0.12.1       YES manual up                    up
FastEthernet0/2            unassigned      YES manual up                    up
Loopback100                100.0.0.1       YES manual up                    up
"""

TEXTFSM_SERIALIZED = [
    {"ADDR": "15.0.15.1", "INTF": "FastEthernet0/0", "PROTO": "up", "STATUS": "up"},
    {"ADDR": "10.0.12.1", "INTF": "FastEthernet0/1", "PROTO": "up", "STATUS": "up"},
    {"ADDR": "unassigned", "INTF": "FastEthernet0/2", "PROTO": "up", "STATUS": "up"},
    {"ADDR": "100.0.0.1", "INTF": "Loopback100", "PROTO": "up", "STATUS": "up"},
]


@pytest.mark.parametrize(
    "extraction_method, contents, template, serialized",
    [
        pytest.param("YAML", JSON_CONFIG, "", json.loads(JSON_CONFIG), id="YAML-JSON"),
        pytest.param("YAML", YAML_CONFIG, "", yaml.safe_load(YAML_CONFIG), id="YAML"),
        pytest.param("TTP", TTP_CONFIG, TTP_TEMPLATE, TTP_SERIALIZED, id="TTP"),
        pytest.param("ROUTEROS", ROUTEROS_CONFIG, "", ROUTEROS_SERIALIZED, id="ROUTEROS"),
        pytest.param("XML", "<a><b>text</b></a>", "", {"a": {"b": "text"}}, id="XML"),
        pytest.param("TEXTFSM", TEXTFSM_STATE, TEXTFSM_TEMPLATE, TEXTFSM_SERIALIZED, id="TEXTFSM"),
    ],
)
@pytest.mark.django_db
def test_serialization(extraction_method, contents, template, serialized):
    serializer = Mock(extraction_method=extraction_method, effective_template=template, parameters={})
    serialize_result = serialize(serializer, contents)
    assert serialize_result == serialized


@pytest.mark.parametrize(
    "serialized_data, jq_expression, expected_result",
    [({"a": {"b": [1, 2]}}, ".a.b", [1, 2]), ({"a": {"b": "c"}}, ". | mkarr(.a.b)", {"a": {"b": ["c"]}})],
)
def test_postprocess_jq(serialized_data, jq_expression, expected_result):
    @postprocess_jq
    def serialization_method(plain_data, template, parameters):
        return json.loads(plain_data)

    json_data = json.dumps(serialized_data)
    result = serialization_method(json_data, "", {"jq_expression": jq_expression})
    assert result == expected_result

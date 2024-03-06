from .backend import SerializationBackend
from .routeros import serialize_ros
from .serializable import Serializable
from .textfsm import serialize_textfsm
from .ttp import serialize_ttp
from .xml import serialize_xml
from .yaml import serialize_yaml


serialize = SerializationBackend(
    extraction_methods={
        "YAML": serialize_yaml,
        "ROUTEROS": serialize_ros,
        "TTP": serialize_ttp,
        "TEXTFSM": serialize_textfsm,
        "XML": serialize_xml,
    }
)

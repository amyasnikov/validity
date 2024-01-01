from .backend import SerializationBackend
from .routeros import serialize_ros
from .serializable import Serializable
from .ttp import serialize_ttp
from .yaml import serialize_yaml


serialize = SerializationBackend(
    extraction_methods={"YAML": serialize_yaml, "ROUTEROS": serialize_ros, "TTP": serialize_ttp}
)

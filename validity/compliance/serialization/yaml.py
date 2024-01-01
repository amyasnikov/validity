import yaml

from validity.utils.misc import reraise
from ..exceptions import SerializationError


def serialize_yaml(plain_data: str, template: str = "") -> dict:
    with reraise(yaml.YAMLError, SerializationError, "Got invalid JSON/YAML"):
        return yaml.safe_load(plain_data)

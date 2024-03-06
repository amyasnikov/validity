import yaml

from validity.utils.misc import reraise
from ..exceptions import SerializationError
from .common import postprocess_jq


@postprocess_jq
def serialize_yaml(plain_data: str, template: str, parameters: dict) -> dict:
    with reraise(yaml.YAMLError, SerializationError, "Got invalid JSON/YAML"):
        return yaml.safe_load(plain_data)

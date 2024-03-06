from xml.parsers.expat import ExpatError

import xmltodict

from validity.utils.json import transform_json
from validity.utils.misc import reraise
from ..exceptions import SerializationError
from .common import postprocess_jq


@postprocess_jq
def serialize_xml(plain_data: str, template: str, parameters: dict):
    with reraise(ExpatError, SerializationError, "Got invalid XML"):
        result = xmltodict.parse(plain_data)
    if parameters.get("drop_attributes"):
        result = transform_json(
            result,
            match_fn=lambda key, _: isinstance(key, str) and key.startswith("@"),
            transform_fn=lambda key, value: None,
        )
    return result

import logging
from xml.parsers.expat import ExpatError

import xmltodict

from validity.utils.json import transform_json
from validity.utils.misc import log_exceptions, reraise
from ..exceptions import SerializationError
from .common import postprocess_jq


logger = logging.getLogger(__name__)


@log_exceptions(logger, "info", log_traceback=True)
@postprocess_jq
def serialize_xml(plain_data: str, template: str, parameters: dict):
    with reraise(ExpatError, SerializationError, "Got invalid XML", orig_error_param=None):
        result = xmltodict.parse(plain_data)
    if parameters.get("drop_attributes"):
        result = transform_json(
            result,
            match_fn=lambda key, _: isinstance(key, str) and key.startswith("@"),
            transform_fn=lambda key, value: None,
        )
    return result

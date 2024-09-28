import logging

from ttp import ttp

from validity.utils.misc import log_exceptions
from .common import postprocess_jq


logger = logging.getLogger(__name__)


@log_exceptions(logger, "info", log_traceback=True)
@postprocess_jq
def serialize_ttp(plain_data: str, template: str, parameters: dict):
    parser = ttp(data=plain_data, template=template)
    parser.parse()
    return parser.result()[0][0]

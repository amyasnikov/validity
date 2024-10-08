import io
import logging

import textfsm

from validity.utils.misc import log_exceptions
from .common import postprocess_jq


logger = logging.getLogger(__name__)


@log_exceptions(logger, "info", log_traceback=True)
@postprocess_jq
def serialize_textfsm(plain_data: str, template: str, parameters: dict) -> list[dict]:
    dict_results = []
    template_file = io.StringIO(template)
    fsm = textfsm.TextFSM(template_file)
    for fsm_result in fsm.ParseText(plain_data):
        dict_results.append({k: v for k, v in zip(fsm.header, fsm_result)})
    return dict_results

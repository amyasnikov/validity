from ttp import ttp

from .common import postprocess_jq


@postprocess_jq
def serialize_ttp(plain_data: str, template: str, parameters: dict):
    parser = ttp(data=plain_data, template=template)
    parser.parse()
    return parser.result()[0][0]

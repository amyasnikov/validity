import xmltodict

from .common import postprocess_jq


@postprocess_jq
def serialize_xml(plain_data: str, template: str, parameters: dict):
    return xmltodict.parse(plain_data)

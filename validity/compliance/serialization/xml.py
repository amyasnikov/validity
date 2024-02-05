import xmltodict


def serialize_xml(plain_data: str, template: str = ""):
    return xmltodict.parse(plain_data)

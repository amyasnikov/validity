from ttp import ttp


def serialize_ttp(plain_data: str, template: str):
    parser = ttp(data=plain_data, template=template)
    parser.parse()
    return parser.result()[0][0]

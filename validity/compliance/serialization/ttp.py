from ttp import ttp

from validity.utils.misc import reraise
from ..exceptions import SerializationError


def serialize_ttp(plain_data: str, template: str):
    with reraise(Exception, SerializationError):
        parser = ttp(data=plain_data, template=template)
        parser.parse()
        return parser.result()[0][0]

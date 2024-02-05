from typing import Callable

from validity.utils.misc import reraise
from ..exceptions import SerializationError


class SerializationBackend:
    def __init__(self, extraction_methods: dict[str, Callable[[str, str], dict]]) -> None:
        self.extraction_methods = extraction_methods

    def __call__(self, extraction_method: str, plain_data: str, template: str):
        extraction_function = self.extraction_methods[extraction_method]
        with reraise(Exception, SerializationError):
            return extraction_function(plain_data, template)

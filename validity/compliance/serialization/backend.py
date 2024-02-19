from typing import TYPE_CHECKING, Callable

from validity.utils.misc import reraise
from ..exceptions import SerializationError


if TYPE_CHECKING:
    from validity.models import Serializer


class SerializationBackend:
    def __init__(self, extraction_methods: dict[str, Callable[[str, str, dict], dict | list]]) -> None:
        self.extraction_methods = extraction_methods

    def __call__(self, serializer: "Serializer", plain_data: str):
        extraction_function = self.extraction_methods[serializer.extraction_method]
        with reraise(Exception, SerializationError):
            return extraction_function(plain_data, serializer.effective_template, serializer.parameters)

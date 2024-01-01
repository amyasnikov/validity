from typing import Callable


class SerializationBackend:
    def __init__(self, extraction_methods: dict[str, Callable[[str, str], dict]]) -> None:
        self.extraction_methods = extraction_methods

    def __call__(self, extraction_method: str, plain_data: str, template: str):
        extraction_function = self.extraction_methods[extraction_method]
        return extraction_function(plain_data, template)

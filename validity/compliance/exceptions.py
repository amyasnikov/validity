class OrigErrorMixin:
    def __init__(self, *args, orig_error: Exception | None = None) -> None:
        self.orig_error = orig_error
        super().__init__(*args)

    def __str__(self) -> str:
        if self.orig_error is not None:
            return f"{type(self.orig_error).__name__}: {self.orig_error}"
        return super().__str__()


class EvalError(OrigErrorMixin, Exception):
    pass


class SerializationError(OrigErrorMixin, Exception):
    pass


class NoComponentError(SerializationError):
    """
    Indicates lack of the required component (e.g. serializer) to do serialization
    """

    def __init__(self, missing_component: str, parent: str | None = None) -> None:
        self.missing_component = missing_component
        self.parent = parent

    def __str__(self) -> str:
        result = f"There is no bound {self.missing_component}"
        if self.parent:
            result += f' for "{self.parent}"'
        return result


class BadDataFileContentsError(SerializationError):
    pass


class StateKeyError(KeyError):
    def __str__(self) -> str:
        key = str(self.args[0]).strip("\"'")
        return f"State has no '{key}' item"

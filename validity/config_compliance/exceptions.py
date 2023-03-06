class EvalError(Exception):
    def __init__(self, orig_error: Exception) -> None:
        self.orig_error = orig_error

    def __str__(self) -> str:
        return f"{type(self.orig_error).__name__}: {self.orig_error}"


class DeviceConfigError(Exception):
    pass

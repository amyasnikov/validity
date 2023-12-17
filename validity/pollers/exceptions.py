class PollingError(Exception):
    def __init__(self, message, *, device_wide=True, orig_error=None) -> None:
        self.device_wide = device_wide
        if orig_error:
            message = f"{type(orig_error).__name__}: {orig_error}"
        super().__init__(message)

    message = property(lambda self: self.args[0])

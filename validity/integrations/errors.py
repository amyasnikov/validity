class IntegrationError(Exception):
    """
    Error happening during network communication with an integration
    """

    def __init__(self, message: str = "", orig_error: Exception | None = None):
        self.message = message
        self.orig_error = orig_error

    def __str__(self):
        if self.orig_error is not None:
            return f"{type(self.orig_error).__name__}: {self.orig_error}"
        return self.message

    def __repr__(self):
        if self.orig_error:
            return repr(self.orig_error)
        return super().__repr__()

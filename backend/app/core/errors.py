class BadRequestError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnauthorizedError(Exception):
    def __init__(self, message: str = "Not authenticated") -> None:
        self.message = message
        super().__init__(message)


class ForbiddenError(Exception):
    """Raised when a user is authenticated but lacks the required role."""
    def __init__(self, message: str = "Access forbidden.") -> None:
        self.message = message
        super().__init__(message)


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

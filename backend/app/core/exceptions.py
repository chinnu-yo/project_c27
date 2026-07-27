class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(AppException):
    """Raised when input validation or business rules check fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class DatabaseError(AppException):
    """Raised on relational or vector database failures."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class SecurityError(AppException):
    """Raised when authentication, tenant isolation, or access check fails."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message, status_code=status_code)

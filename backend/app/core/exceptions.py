"""
Custom exceptions for the application.
"""
from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Exception for authentication failures."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Exception for authorization failures."""

    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(HTTPException):
    """Exception for resource not found."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found"
        )


class ConflictError(HTTPException):
    """Exception for resource conflicts (e.g., duplicate entries)."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ValidationError(HTTPException):
    """Exception for validation failures."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ContentBlockedError(HTTPException):
    """Exception for blocked content."""

    def __init__(self, reason: str = "Content blocked by parent rules"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Message blocked: {reason}"
        )


class AIServiceError(HTTPException):
    """Exception for AI service failures."""

    def __init__(self, detail: str = "AI service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class RateLimitError(HTTPException):
    """Exception for rate limit exceeded."""

    def __init__(self, detail: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

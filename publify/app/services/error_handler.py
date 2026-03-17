"""Error handling and custom exceptions."""
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class PublifyException(Exception):
    """Base exception for Publify application."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationRequiredError(PublifyException):
    """Raised when authentication is required but not provided."""

    def __init__(self, message: str = "Authentication required", details: dict | None = None) -> None:
        super().__init__(
            message=message,
            code="AUTH_REQUIRED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class InvalidAPIKeyError(PublifyException):
    """Raised when API key is invalid."""

    def __init__(self, message: str = "Invalid API key", details: dict | None = None) -> None:
        super().__init__(
            message=message,
            code="INVALID_API_KEY",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ContentValidationError(PublifyException):
    """Raised when content validation fails."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            code="INVALID_CONTENT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class MediaTooLargeError(PublifyException):
    """Raised when media file is too large."""

    def __init__(
        self,
        message: str = "Media file too large",
        max_size: str | None = None,
        details: dict | None = None,
    ) -> None:
        if details is None:
            details = {}
        if max_size:
            details["max_size"] = max_size
        super().__init__(
            message=message,
            code="MEDIA_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details,
        )


class PlatformError(PublifyException):
    """Raised when platform API returns an error."""

    def __init__(
        self,
        message: str = "Platform API error",
        platform: str | None = None,
        details: dict | None = None,
    ) -> None:
        if details is None:
            details = {}
        if platform:
            details["platform"] = platform
        super().__init__(
            message=message,
            code="PLATFORM_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class RateLimitedError(PublifyException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int | None = None,
        reset_at: int | None = None,
        details: dict | None = None,
    ) -> None:
        if details is None:
            details = {}
        if limit is not None:
            details["limit"] = limit
        if reset_at is not None:
            details["reset_at"] = reset_at
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


async def publify_exception_handler(request: Request, exc: PublifyException) -> JSONResponse:
    """Handle PublifyException and return appropriate JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and return consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
            },
        },
    )


def get_error_response(code: str, message: str, details: dict | None = None) -> dict[str, Any]:
    """Get standardized error response."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


# Error codes mapping for documentation
ERROR_CODES = {
    "AUTH_REQUIRED": "User must authenticate to access this resource",
    "INVALID_API_KEY": "The provided API key is invalid or inactive",
    "INVALID_CONTENT": "The content format is invalid",
    "MEDIA_TOO_LARGE": "Media file exceeds size limit",
    "PLATFORM_ERROR": "Error communicating with external platform API",
    "RATE_LIMITED": "Request rate limit exceeded",
    "VALIDATION_ERROR": "Request validation failed",
    "INTERNAL_ERROR": "Internal server error",
}

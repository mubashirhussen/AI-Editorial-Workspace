"""
Centralized Application Exceptions for AI Editorial Workspace.
Provides typed domain exceptions mapped to HTTP status codes and error categories.
"""
from typing import Any, Optional, Dict

class AppException(Exception):
    """Base application exception for standardized API error handling."""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers

class ResourceNotFoundException(AppException):
    def __init__(self, resource: str, identifier: Any, details: Optional[Any] = None):
        super().__init__(
            message=f"{resource} with ID '{identifier}' not found.",
            status_code=404,
            code="NOT_FOUND",
            details=details
        )

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED",
            details=details,
            headers={"WWW-Authenticate": "Bearer"}
        )

class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to access this resource or perform this action.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            code="FORBIDDEN",
            details=details
        )

class ConflictException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=409,
            code="RESOURCE_CONFLICT",
            details=details
        )

class ValidationException(AppException):
    def __init__(self, message: str = "Request payload validation failed.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            code="VALIDATION_ERROR",
            details=details
        )

class RateLimitException(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please wait before making more requests.", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)}
        )

class AiProviderException(AppException):
    def __init__(self, message: str = "AI Provider request failed or timed out.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=502,
            code="AI_PROVIDER_ERROR",
            details=details
        )

class ExternalServiceException(AppException):
    def __init__(self, message: str = "External network service request failed.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=502,
            code="EXTERNAL_SERVICE_ERROR",
            details=details
        )

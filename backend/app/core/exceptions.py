"""
Custom exception classes for the application.
"""

from typing import Any


class BaseAppException(Exception):
    """Base exception class for application-specific exceptions."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(BaseAppException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=422,
        )


class BusinessLogicException(BaseAppException):
    """Exception raised for business logic errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            status_code=400,
        )


class ResourceNotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
            status_code=404,
        )


class DatabaseException(BaseAppException):
    """Exception raised for database-related errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=500,
        )


class ExternalServiceException(BaseAppException):
    """Exception raised for external service errors."""

    def __init__(
        self,
        message: str = "External service error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=502,
        )

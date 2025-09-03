"""
Global error handling middleware for FastAPI application.
"""

import traceback
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import BaseAppException
from app.schemas.error import ErrorResponse, ValidationErrorDetail, ValidationErrorResponse


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions."""
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response

        except (HTTPException, RequestValidationError, ValidationError, BaseAppException):
            # Let these be handled by exception handlers
            raise
        except Exception as exc:
            return await self._handle_exception(request, exc, request_id)

    async def _handle_exception(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Handle different types of exceptions and return appropriate responses."""

        # Log the exception with context
        await self._log_exception(request, exc, request_id)

        # Handle different exception types
        # Note: BaseAppException, HTTPException, RequestValidationError and ValidationError
        # are now handled by exception handlers, so middleware only handles unexpected exceptions
        return await self._handle_unexpected_exception(exc, request_id)

    async def _handle_app_exception(self, exc: BaseAppException, request_id: str) -> JSONResponse:
        """Handle application-specific exceptions."""
        error_response = ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    async def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_response = ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            details={"status_code": exc.status_code},
            request_id=request_id,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    async def _handle_validation_exception(self, exc: RequestValidationError, request_id: str) -> JSONResponse:
        """Handle FastAPI request validation exceptions."""
        validation_errors = []

        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                ValidationErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    value=error.get("input"),
                )
            )

        error_response = ValidationErrorResponse(
            message="Request validation failed",
            validation_errors=validation_errors,
            request_id=request_id,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    async def _handle_pydantic_validation_exception(self, exc: ValidationError, request_id: str) -> JSONResponse:
        """Handle Pydantic validation exceptions."""
        validation_errors = []

        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                ValidationErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    value=error.get("input"),
                )
            )

        error_response = ValidationErrorResponse(
            message="Data validation failed",
            validation_errors=validation_errors,
            request_id=request_id,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    async def _handle_unexpected_exception(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected exceptions."""
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__},
            request_id=request_id,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )

    async def _log_exception(self, request: Request, exc: Exception, request_id: str) -> None:
        """Log exception with request context."""
        # Extract request information
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)

        # Remove sensitive headers
        sensitive_headers = {"authorization", "cookie", "x-api-key"}
        filtered_headers = {k: v if k.lower() not in sensitive_headers else "[REDACTED]" for k, v in headers.items()}

        # Prepare log context
        log_context = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "headers": filtered_headers,
            "exception_type": type(exc).__name__,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Log based on exception type
        if isinstance(exc, BaseAppException):
            logger.warning(
                "Application exception occurred",
                extra={
                    **log_context,
                    "exception_message": exc.message,
                    "error_code": exc.error_code,
                    "status_code": exc.status_code,
                    "details": exc.details,
                },
            )

        elif isinstance(exc, HTTPException):
            logger.warning(
                "HTTP exception occurred",
                extra={
                    **log_context,
                    "exception_detail": exc.detail,
                    "status_code": exc.status_code,
                },
            )

        elif isinstance(exc, RequestValidationError | ValidationError):
            logger.warning(
                "Validation exception occurred",
                extra={
                    **log_context,
                    "exception_message": str(exc),
                    "validation_errors": exc.errors() if hasattr(exc, "errors") else str(exc),
                },
            )

        else:
            # Log unexpected exceptions with full traceback
            logger.error(
                "Unexpected exception occurred",
                extra={
                    **log_context,
                    "exception_message": str(exc),
                    "exception_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                },
            )


# Exception handler functions for FastAPI
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the exception
    await _log_http_exception(request, exc, request_id)

    error_response = ErrorResponse(
        error="HTTP_ERROR",
        message=exc.detail,
        details={"status_code": exc.status_code},
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the exception
    await _log_validation_exception(request, exc, request_id)

    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append(
            ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                value=error.get("input"),
            )
        )

    error_response = ValidationErrorResponse(
        message="Request validation failed",
        validation_errors=validation_errors,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def handle_pydantic_validation_exception(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the exception
    await _log_validation_exception(request, exc, request_id)

    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append(
            ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                value=error.get("input"),
            )
        )

    error_response = ValidationErrorResponse(
        message="Data validation failed",
        validation_errors=validation_errors,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def handle_app_exception(request: Request, exc: BaseAppException) -> JSONResponse:
    """Handle application-specific exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the exception
    await _log_app_exception(request, exc, request_id)

    error_response = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


# Helper logging functions
async def _log_http_exception(request: Request, exc: HTTPException, request_id: str) -> None:
    """Log HTTP exception with request context."""
    log_context = _get_log_context(request, request_id)

    logger.warning(
        "HTTP exception occurred",
        extra={
            **log_context,
            "exception_detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


async def _log_validation_exception(request: Request, exc: RequestValidationError | ValidationError, request_id: str) -> None:
    """Log validation exception with request context."""
    log_context = _get_log_context(request, request_id)

    logger.warning(
        "Validation exception occurred",
        extra={
            **log_context,
            "exception_message": str(exc),
            "validation_errors": exc.errors() if hasattr(exc, "errors") else str(exc),
        },
    )


async def _log_app_exception(request: Request, exc: BaseAppException, request_id: str) -> None:
    """Log application exception with request context."""
    log_context = _get_log_context(request, request_id)

    logger.warning(
        "Application exception occurred",
        extra={
            **log_context,
            "exception_message": exc.message,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )


def _get_log_context(request: Request, request_id: str) -> dict:
    """Get common log context from request."""
    method = request.method
    url = str(request.url)
    headers = dict(request.headers)

    # Remove sensitive headers
    sensitive_headers = {"authorization", "cookie", "x-api-key"}
    filtered_headers = {k: v if k.lower() not in sensitive_headers else "[REDACTED]" for k, v in headers.items()}

    return {
        "request_id": request_id,
        "method": method,
        "url": url,
        "headers": filtered_headers,
        "timestamp": datetime.now(UTC).isoformat(),
    }

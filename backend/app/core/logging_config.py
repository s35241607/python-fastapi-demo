"""
Loguru-based structured logging configuration.
"""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import settings
from app.core.logging_models import format_log_record


def setup_logging() -> None:
    """
    Setup structured logging with Loguru.

    Configures:
    - Console output with appropriate formatting
    - File output with JSON formatting and rotation
    - Log levels based on environment
    """
    # Remove default handler
    logger.remove()

    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Console handler - different formats for different environments
    if settings.is_development():
        # Development: Human-readable format
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            format=console_format,
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # Production/Testing: JSON format
        logger.add(
            sys.stdout,
            format=lambda record: format_log_record(record),
            level=settings.LOG_LEVEL,
            serialize=False,  # We handle JSON formatting ourselves
        )

    # File handler - always JSON format with rotation
    log_file_path = Path(settings.get_log_file_path())
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_file_path),
        level=settings.LOG_LEVEL,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="30 days",  # Keep logs for 30 days
        compression="gz",  # Compress rotated files
        serialize=True,  # Use Loguru's built-in JSON serialization
        backtrace=True,
        diagnose=True,
    )

    # Add error file for ERROR and CRITICAL logs
    error_log_path = log_file_path.parent / "error.log"
    logger.add(
        str(error_log_path),
        level="ERROR",
        rotation="10 MB",
        retention="90 days",  # Keep error logs longer
        compression="gz",
        serialize=True,  # Use Loguru's built-in JSON serialization
        backtrace=True,
        diagnose=True,
    )

    # Configure logging for different environments
    if settings.is_production():
        # In production, be more conservative with logging
        logger.add(
            sys.stderr,
            level="ERROR",
            serialize=True,
        )

    logger.info(
        "Logging configured",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "log_file": str(log_file_path),
            "log_format": settings.LOG_FORMAT,
        },
    )


def get_logger(name: str = None) -> "logger":
    """
    Get a logger instance with optional name binding.

    Args:
        name: Optional name to bind to the logger

    Returns:
        Loguru logger instance
    """
    if name:
        return logger.bind(logger_name=name)
    return logger


def log_with_context(level: str, message: str, context: dict[str, Any] = None, **kwargs) -> None:
    """
    Log a message with additional context.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        context: Additional context to include
        **kwargs: Additional keyword arguments
    """
    extra = {}
    if context:
        extra.update(context)
    if kwargs:
        extra.update(kwargs)

    logger.opt(depth=1).log(level, message, extra=extra)


def log_request(
    method: str,
    path: str,
    request_id: str,
    user_id: str = None,
    client_ip: str = None,
    user_agent: str = None,
    query_params: dict[str, Any] = None,
) -> None:
    """
    Log incoming request information.

    Args:
        method: HTTP method
        path: Request path
        request_id: Unique request identifier
        user_id: User ID if available
        client_ip: Client IP address
        user_agent: User agent string
        query_params: Query parameters
    """
    from app.core.logging_models import create_request_context

    context = create_request_context(
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id,
        client_ip=client_ip,
        user_agent=user_agent,
        query_params=query_params,
    )

    logger.info(f"Request started: {method} {path}", extra=context)


def log_response(
    request_id: str,
    status_code: int,
    duration_ms: float,
    response_size: int = None,
) -> None:
    """
    Log response information.

    Args:
        request_id: Unique request identifier
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        response_size: Response size in bytes
    """
    from app.core.logging_models import create_response_context

    context = create_response_context(
        request_id=request_id,
        status_code=status_code,
        duration_ms=duration_ms,
        response_size=response_size,
    )

    # Choose log level based on status code
    if status_code >= 500:
        level = "ERROR"
    elif status_code >= 400:
        level = "WARNING"
    else:
        level = "INFO"

    logger.log(level, f"Request completed: {status_code} ({duration_ms:.2f}ms)", extra=context)


def log_error(
    request_id: str,
    error_type: str,
    error_message: str,
    stack_trace: str = None,
    additional_context: dict[str, Any] = None,
) -> None:
    """
    Log error information.

    Args:
        request_id: Unique request identifier
        error_type: Type of error
        error_message: Error message
        stack_trace: Stack trace if available
        additional_context: Additional context information
    """
    from app.core.logging_models import create_error_context

    context = create_error_context(
        request_id=request_id,
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        additional_context=additional_context,
    )

    logger.error(f"Error occurred: {error_type} - {error_message}", extra=context)


def log_performance(
    operation: str,
    duration_ms: float,
    context: dict[str, Any] = None,
) -> None:
    """
    Log performance metrics.

    Args:
        operation: Operation name
        duration_ms: Operation duration in milliseconds
        context: Additional context
    """
    extra = {
        "operation": operation,
        "duration_ms": duration_ms,
        "performance": True,
    }

    if context:
        extra.update(context)

    # Log as warning if operation is slow
    level = "WARNING" if duration_ms > 1000 else "INFO"

    logger.log(level, f"Performance: {operation} completed in {duration_ms:.2f}ms", extra=extra)


# Initialize logging when module is imported
setup_logging()

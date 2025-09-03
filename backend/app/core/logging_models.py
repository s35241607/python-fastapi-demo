"""
Logging data models and formatters for structured logging.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Structured log entry model"""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    level: str
    message: str
    request_id: str | None = None
    user_id: str | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    duration_ms: float | None = None
    extra: dict[str, Any] | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class RequestLogEntry(LogEntry):
    """Request-specific log entry model"""

    method: str
    path: str
    query_params: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
    client_ip: str | None = None
    user_agent: str | None = None


class ResponseLogEntry(LogEntry):
    """Response-specific log entry model"""

    status_code: int
    duration_ms: float
    response_size: int | None = None


class ErrorLogEntry(LogEntry):
    """Error-specific log entry model"""

    error_type: str
    error_message: str
    stack_trace: str | None = None
    context: dict[str, Any] | None = None


def format_log_record(record: dict) -> str:
    """
    Format log record as JSON string for structured logging.

    Args:
        record: Log record dictionary from Loguru

    Returns:
        JSON formatted string
    """
    import json

    # Extract basic information
    log_data = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add extra fields if present - handle nested extra structure
    if "extra" in record and record["extra"]:
        # Loguru sometimes nests extra fields under an 'extra' key
        extra_data = record["extra"]
        if "extra" in extra_data:
            log_data.update(extra_data["extra"])
        else:
            log_data.update(extra_data)

    # Add exception information if present
    if record.get("exception"):
        log_data["exception"] = {
            "type": record["exception"]["type"].__name__ if record["exception"]["type"] else None,
            "value": str(record["exception"]["value"]) if record["exception"]["value"] else None,
            "traceback": record["exception"]["traceback"] if record["exception"]["traceback"] else None,
        }

    return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))


def create_request_context(
    request_id: str,
    method: str,
    path: str,
    user_id: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    query_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create request context for logging.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        user_id: User ID if available
        client_ip: Client IP address
        user_agent: User agent string
        query_params: Query parameters

    Returns:
        Dictionary with request context
    """
    context = {
        "request_id": request_id,
        "method": method,
        "path": path,
    }

    if user_id:
        context["user_id"] = user_id
    if client_ip:
        context["client_ip"] = client_ip
    if user_agent:
        context["user_agent"] = user_agent
    if query_params:
        context["query_params"] = query_params

    return context


def create_response_context(
    request_id: str,
    status_code: int,
    duration_ms: float,
    response_size: int | None = None,
) -> dict[str, Any]:
    """
    Create response context for logging.

    Args:
        request_id: Unique request identifier
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        response_size: Response size in bytes

    Returns:
        Dictionary with response context
    """
    context = {
        "request_id": request_id,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }

    if response_size is not None:
        context["response_size"] = response_size

    return context


def create_error_context(
    request_id: str,
    error_type: str,
    error_message: str,
    stack_trace: str | None = None,
    additional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create error context for logging.

    Args:
        request_id: Unique request identifier
        error_type: Type of error
        error_message: Error message
        stack_trace: Stack trace if available
        additional_context: Additional context information

    Returns:
        Dictionary with error context
    """
    context = {
        "request_id": request_id,
        "error_type": error_type,
        "error_message": error_message,
    }

    if stack_trace:
        context["stack_trace"] = stack_trace
    if additional_context:
        context.update(additional_context)

    return context

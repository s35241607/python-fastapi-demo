"""
Error response schemas for structured error handling.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class ErrorResponse(BaseModel):
    """Structured error response model."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Error timestamp")
    request_id: str | None = Field(default=None, description="Request ID for tracking")

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any | None = Field(default=None, description="Invalid value")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with detailed field errors."""

    error: str = Field(default="VALIDATION_ERROR")
    validation_errors: list[ValidationErrorDetail] = Field(default_factory=list, description="List of validation errors")

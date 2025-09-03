"""
Test routes for demonstrating error handling functionality.
These routes are for testing purposes and should be removed in production.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.exceptions import (
    BusinessLogicException,
    DatabaseException,
    ExternalServiceException,
    ResourceNotFoundException,
    ValidationException,
)
from app.middleware.jwt_parser import get_current_user, get_current_user_id

router = APIRouter(prefix="/test-errors", tags=["Test Errors"])


class TestModel(BaseModel):
    """Test model for validation errors."""

    name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    age: int = Field(..., ge=0, le=150)


@router.get("/app-exception")
async def test_app_exception():
    """Test custom application exception."""
    raise ValidationException(
        message="This is a test validation error",
        details={"field": "test_field", "value": "invalid_value"},
    )


@router.get("/http-exception")
async def test_http_exception():
    """Test FastAPI HTTP exception."""
    raise HTTPException(status_code=404, detail="Test resource not found")


@router.get("/business-logic-error")
async def test_business_logic_error():
    """Test business logic exception."""
    raise BusinessLogicException(
        message="Business rule violation",
        details={"rule": "test_rule", "violation": "test_violation"},
    )


@router.get("/resource-not-found")
async def test_resource_not_found():
    """Test resource not found exception."""
    raise ResourceNotFoundException(
        message="Test resource not found",
        details={"resource_id": "test_123", "resource_type": "test"},
    )


@router.get("/database-error")
async def test_database_error():
    """Test database exception."""
    raise DatabaseException(
        message="Database connection failed",
        details={"operation": "select", "table": "test_table"},
    )


@router.get("/external-service-error")
async def test_external_service_error():
    """Test external service exception."""
    raise ExternalServiceException(
        message="External API is unavailable",
        details={"service": "test_api", "endpoint": "/test"},
    )


@router.get("/unexpected-error")
async def test_unexpected_error():
    """Test unexpected exception."""
    # This will raise a ZeroDivisionError
    result = 1 / 0
    return {"result": result}


@router.post("/validation-error")
async def test_validation_error(data: TestModel):
    """Test request validation error."""
    return {"message": "Validation passed", "data": data}


@router.get("/multiple-errors")
async def test_multiple_errors(error_type: str = "validation"):
    """Test different error types based on parameter."""
    if error_type == "validation":
        raise ValidationException("Multiple validation errors occurred")
    elif error_type == "business":
        raise BusinessLogicException("Business logic failed")
    elif error_type == "database":
        raise DatabaseException("Database operation failed")
    elif error_type == "http":
        raise HTTPException(status_code=400, detail="Bad request")
    else:
        raise ValueError("Unknown error type")


@router.get("/middleware-chain")
async def test_middleware_chain(request: Request):
    """Test middleware chain functionality."""
    try:
        # Get user context from JWT parser middleware
        user_context = get_current_user(request)
        user_id = get_current_user_id(request)

        # Get request ID from logging middleware
        request_id = getattr(request.state, "request_id", None)

        return {
            "message": "Middleware chain test",
            "request_id": request_id,
            "user_authenticated": user_context.is_authenticated(),
            "user_id": user_id,
            "username": user_context.username,
            "user_roles": user_context.roles,
            "user_permissions": user_context.permissions,
            "middleware_data": {
                "has_user_context": hasattr(request.state, "user_context"),
                "has_request_id": hasattr(request.state, "request_id"),
                "has_user_id": hasattr(request.state, "user_id"),
                "has_username": hasattr(request.state, "username"),
            },
        }
    except Exception as e:
        return {
            "error": f"Error in middleware chain test: {str(e)}",
            "error_type": type(e).__name__,
            "request_state_attrs": [attr for attr in dir(request.state) if not attr.startswith("_")],
        }

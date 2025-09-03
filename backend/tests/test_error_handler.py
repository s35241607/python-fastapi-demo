"""
Unit tests for error handling middleware.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    BusinessLogicException,
    DatabaseException,
    ResourceNotFoundException,
    ValidationException,
)
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.schemas.error import ErrorResponse, ValidationErrorResponse


class TestErrorHandlerMiddleware:
    """Test cases for ErrorHandlerMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        return ErrorHandlerMiddleware(app=MagicMock())

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "http://test.com/api/test"
        request.headers = {"content-type": "application/json", "user-agent": "test"}
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request):
        """Test middleware with successful request."""
        # Mock successful response
        mock_response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        # Process request
        response = await middleware.dispatch(mock_request, call_next)

        # Verify response
        assert response == mock_response
        assert hasattr(mock_request.state, "request_id")
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_base_app_exception(self, middleware, mock_request):
        """Test that BaseAppException is re-raised for exception handlers."""
        # Create test exception
        test_exception = ValidationException(
            message="Test validation error",
            details={"field": "test", "value": "invalid"},
        )

        # Mock call_next to raise exception
        call_next = AsyncMock(side_effect=test_exception)

        # The middleware should re-raise BaseAppException for exception handlers
        with pytest.raises(ValidationException):
            await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_http_exception(self, middleware, mock_request):
        """Test that HTTPException is re-raised for exception handlers."""
        # Create test exception
        test_exception = HTTPException(status_code=404, detail="Not found")

        # Mock call_next to raise exception
        call_next = AsyncMock(side_effect=test_exception)

        # The middleware should re-raise HTTPException for exception handlers
        with pytest.raises(HTTPException):
            await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_request_validation_error(self, middleware, mock_request):
        """Test that RequestValidationError is re-raised for exception handlers."""
        # Create test validation error
        validation_errors = [
            {
                "loc": ("body", "email"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": None,
            },
            {
                "loc": ("body", "age"),
                "msg": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt",
                "input": -1,
            },
        ]

        test_exception = RequestValidationError(validation_errors)

        # Mock call_next to raise exception
        call_next = AsyncMock(side_effect=test_exception)

        # The middleware should re-raise RequestValidationError for exception handlers
        with pytest.raises(RequestValidationError):
            await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, middleware, mock_request):
        """Test handling of unexpected exceptions."""
        # Create unexpected exception
        test_exception = ValueError("Unexpected error")

        # Mock call_next to raise exception
        call_next = AsyncMock(side_effect=test_exception)

        with patch.object(middleware, "_log_exception", new_callable=AsyncMock) as mock_log:
            response = await middleware.dispatch(mock_request, call_next)

            # Verify response
            assert response.status_code == 500
            response_data = json.loads(response.body)

            assert response_data["error"] == "INTERNAL_SERVER_ERROR"
            assert response_data["message"] == "An unexpected error occurred"
            assert response_data["details"]["type"] == "ValueError"
            assert "request_id" in response_data

            # Verify logging was called
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_app_exceptions(self, middleware, mock_request):
        """Test that different application exception types are re-raised for exception handlers."""
        exceptions_to_test = [
            BusinessLogicException("Business error", {"rule": "test"}),
            ResourceNotFoundException("Resource not found", {"id": "123"}),
            DatabaseException("DB error", {"table": "users"}),
        ]

        for exception in exceptions_to_test:
            call_next = AsyncMock(side_effect=exception)

            # The middleware should re-raise BaseAppException subclasses for exception handlers
            with pytest.raises(type(exception)):
                await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_log_exception_with_sensitive_headers(self, middleware, mock_request):
        """Test that sensitive headers are redacted in logs."""
        # Add sensitive headers
        mock_request.headers = {
            "authorization": "Bearer secret-token",
            "cookie": "session=secret",
            "x-api-key": "secret-key",
            "content-type": "application/json",
        }

        test_exception = ValueError("Test error")

        with patch("app.middleware.error_handler.logger") as mock_logger:
            await middleware._log_exception(mock_request, test_exception, "test-id")

            # Verify logger was called
            mock_logger.error.assert_called_once()

            # Get the logged context
            call_args = mock_logger.error.call_args
            log_context = call_args[1]["extra"]

            # Verify sensitive headers are redacted
            headers = log_context["headers"]
            assert headers["authorization"] == "[REDACTED]"
            assert headers["cookie"] == "[REDACTED]"
            assert headers["x-api-key"] == "[REDACTED]"
            assert headers["content-type"] == "application/json"  # Not sensitive

    @pytest.mark.asyncio
    async def test_request_id_generation(self, middleware, mock_request):
        """Test that request ID is properly generated and used."""
        test_exception = ValueError("Test error")
        call_next = AsyncMock(side_effect=test_exception)

        response = await middleware.dispatch(mock_request, call_next)

        # Verify request ID was set
        assert hasattr(mock_request.state, "request_id")
        request_id = mock_request.state.request_id

        # Verify request ID is a valid UUID
        uuid.UUID(request_id)  # This will raise if not valid UUID

        # Verify request ID is in response
        response_data = json.loads(response.body)
        assert response_data["request_id"] == request_id


class TestErrorResponseModels:
    """Test cases for error response models."""

    def test_error_response_model(self):
        """Test ErrorResponse model."""
        error_response = ErrorResponse(
            error="TEST_ERROR",
            message="Test error message",
            details={"key": "value"},
            request_id="test-123",
        )

        assert error_response.error == "TEST_ERROR"
        assert error_response.message == "Test error message"
        assert error_response.details == {"key": "value"}
        assert error_response.request_id == "test-123"
        assert isinstance(error_response.timestamp, datetime)

    def test_validation_error_response_model(self):
        """Test ValidationErrorResponse model."""
        from app.schemas.error import ValidationErrorDetail

        validation_errors = [
            ValidationErrorDetail(field="email", message="Invalid email format", value="invalid-email"),
            ValidationErrorDetail(field="age", message="Must be positive", value=-1),
        ]

        error_response = ValidationErrorResponse(
            message="Validation failed",
            validation_errors=validation_errors,
            request_id="test-123",
        )

        assert error_response.error == "VALIDATION_ERROR"
        assert error_response.message == "Validation failed"
        assert len(error_response.validation_errors) == 2
        assert error_response.validation_errors[0].field == "email"
        assert error_response.validation_errors[1].value == -1

    def test_error_response_serialization(self):
        """Test error response JSON serialization."""
        error_response = ErrorResponse(
            error="TEST_ERROR",
            message="Test message",
            details={"test": True},
            request_id="test-123",
        )

        # Test model_dump
        data = error_response.model_dump()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)  # Now serialized as string

        # Test JSON serialization
        json_str = error_response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["error"] == "TEST_ERROR"
        assert "timestamp" in parsed
        assert isinstance(parsed["timestamp"], str)


class TestExceptionHandlers:
    """Test cases for exception handler functions."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "http://test.com/api/test"
        request.headers = {"content-type": "application/json", "user-agent": "test"}
        request.state = MagicMock()
        request.state.request_id = "test-123"
        return request

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_request):
        """Test HTTP exception handler."""
        from app.middleware.error_handler import handle_http_exception

        exc = HTTPException(status_code=404, detail="Not found")

        with patch("app.middleware.error_handler._log_http_exception", new_callable=AsyncMock) as mock_log:
            response = await handle_http_exception(mock_request, exc)

            assert response.status_code == 404
            response_data = json.loads(response.body)

            assert response_data["error"] == "HTTP_ERROR"
            assert response_data["message"] == "Not found"
            assert response_data["details"]["status_code"] == 404
            assert response_data["request_id"] == "test-123"

            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_validation_exception(self, mock_request):
        """Test validation exception handler."""
        from app.middleware.error_handler import handle_validation_exception

        validation_errors = [
            {
                "loc": ("body", "email"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": None,
            }
        ]

        exc = RequestValidationError(validation_errors)

        with patch("app.middleware.error_handler._log_validation_exception", new_callable=AsyncMock) as mock_log:
            response = await handle_validation_exception(mock_request, exc)

            assert response.status_code == 422
            response_data = json.loads(response.body)

            assert response_data["error"] == "VALIDATION_ERROR"
            assert response_data["message"] == "Request validation failed"
            assert len(response_data["validation_errors"]) == 1
            assert response_data["validation_errors"][0]["field"] == "body -> email"
            assert response_data["request_id"] == "test-123"

            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_app_exception(self, mock_request):
        """Test application exception handler."""
        from app.middleware.error_handler import handle_app_exception

        exc = ValidationException(
            message="Test validation error",
            details={"field": "test", "value": "invalid"},
        )

        with patch("app.middleware.error_handler._log_app_exception", new_callable=AsyncMock) as mock_log:
            response = await handle_app_exception(mock_request, exc)

            assert response.status_code == 422
            response_data = json.loads(response.body)

            assert response_data["error"] == "VALIDATION_ERROR"
            assert response_data["message"] == "Test validation error"
            assert response_data["details"]["field"] == "test"
            assert response_data["request_id"] == "test-123"

            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_exception(self, mock_request):
        """Test Pydantic validation exception handler."""
        from pydantic import BaseModel, Field, ValidationError

        from app.middleware.error_handler import handle_pydantic_validation_exception

        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)

        try:
            TestModel(name="")
        except ValidationError as exc:
            with patch("app.middleware.error_handler._log_validation_exception", new_callable=AsyncMock) as mock_log:
                response = await handle_pydantic_validation_exception(mock_request, exc)

                assert response.status_code == 422
                response_data = json.loads(response.body)

                assert response_data["error"] == "VALIDATION_ERROR"
                assert response_data["message"] == "Data validation failed"
                assert len(response_data["validation_errors"]) == 1
                assert response_data["validation_errors"][0]["field"] == "name"
                assert response_data["request_id"] == "test-123"

                mock_log.assert_called_once()

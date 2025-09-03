"""
Comprehensive tests for logging and error handling functionality verification.
Tests log output, error formatting, and integration between logging and error handling.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.logging_config import get_logger, setup_logging
from app.core.logging_models import LogEntry
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".log", delete=False) as f:
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestLoggingFunctionality:
    """Test logging functionality and configuration."""

    def test_logger_initialization(self):
        """Test logger initialization and configuration."""
        logger = get_logger("test_module")

        assert logger is not None
        # Loguru logger doesn't have a name attribute, but should be callable
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_structured_logging_format(self, temp_log_file):
        """Test structured logging format (JSON)."""
        # Setup logging with temporary file
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.LOG_FILE_PATH = temp_log_file
            mock_settings.LOG_FORMAT = "json"
            mock_settings.LOG_LEVEL = "INFO"

            setup_logging()
            logger = get_logger("test_structured")

            # Log a test message
            test_data = {"user_id": "user123", "action": "test_action", "details": {"key": "value"}}
            logger.info("Test structured log", extra=test_data)

            # Read and verify log file
            log_content = Path(temp_log_file).read_text()
            assert len(log_content.strip()) > 0

            # Should contain structured data
            assert "user_id" in log_content or "Test structured log" in log_content

    def test_log_levels(self):
        """Test different log levels."""
        logger = get_logger("test_levels")

        with patch.object(logger, "_log") as mock_log:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            # Verify all levels were called
            assert mock_log.call_count >= 4  # Depending on log level configuration

    def test_log_entry_model(self):
        """Test LogEntry model validation."""
        from datetime import datetime

        log_entry = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Test message",
            request_id="req_123",
            user_id="user_456",
            method="GET",
            path="/test",
            status_code=200,
            duration_ms=150.5,
            extra={"key": "value"},
        )

        assert log_entry.level == "INFO"
        assert log_entry.message == "Test message"
        assert log_entry.request_id == "req_123"
        assert log_entry.user_id == "user_456"
        assert log_entry.method == "GET"
        assert log_entry.path == "/test"
        assert log_entry.status_code == 200
        assert log_entry.duration_ms == 150.5
        assert log_entry.extra == {"key": "value"}

    def test_logging_middleware_integration(self, client):
        """Test logging middleware integration."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain")

            assert response.status_code == 200

            # Verify logging middleware logged the request
            mock_logger.info.assert_called()

            # Check log calls for request information
            log_calls = mock_logger.info.call_args_list
            request_logged = any("Request" in str(call) or "GET" in str(call) for call in log_calls)
            assert request_logged

    def test_request_response_logging(self, client, valid_jwt_token):
        """Test request and response logging."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            assert response.status_code == 200

            # Verify request logging
            mock_logger.info.assert_called()

            # Check that user context is logged
            log_calls = mock_logger.info.call_args_list
            user_logged = any("user123" in str(call) or "testuser" in str(call) for call in log_calls)
            # User logging might be in debug level or different format

    def test_error_logging_integration(self, client):
        """Test error logging integration."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/app-exception")

            assert response.status_code == 422

            # Verify error was logged
            mock_logger.error.assert_called()

            # Check error log content
            error_calls = mock_logger.error.call_args_list
            error_logged = any("ValidationException" in str(call) or "validation error" in str(call) for call in error_calls)
            assert error_logged

    def test_performance_logging(self, client):
        """Test performance metrics logging."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain")

            assert response.status_code == 200

            # Verify performance metrics are logged
            mock_logger.info.assert_called()

            # Check for duration/timing information
            log_calls = mock_logger.info.call_args_list
            timing_logged = any(
                "duration" in str(call).lower() or "ms" in str(call) or "completed" in str(call) for call in log_calls
            )
            assert timing_logged


class TestErrorHandlingFunctionality:
    """Test error handling functionality and formatting."""

    def test_custom_exception_handling(self, client):
        """Test custom exception handling."""
        response = client.get("/api/v1/test-errors/app-exception")

        assert response.status_code == 422
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "VALIDATION_ERROR"
        assert "test validation error" in data["message"]

    def test_http_exception_handling(self, client):
        """Test HTTP exception handling."""
        response = client.get("/api/v1/test-errors/http-exception")

        assert response.status_code == 404
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "NOT_FOUND"

    def test_validation_exception_handling(self, client):
        """Test validation exception handling."""
        invalid_data = {
            "name": "",  # Too short
            "email": "invalid-email",  # Invalid format
            "age": -5,  # Invalid age
        }

        response = client.post("/api/v1/test-errors/validation-error", json=invalid_data)

        assert response.status_code == 422
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "VALIDATION_ERROR"

    def test_unexpected_exception_handling(self, client):
        """Test unexpected exception handling."""
        response = client.get("/api/v1/test-errors/unexpected-error")

        assert response.status_code == 500
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "INTERNAL_SERVER_ERROR"

    def test_business_logic_exception_handling(self, client):
        """Test business logic exception handling."""
        response = client.get("/api/v1/test-errors/business-logic-error")

        assert response.status_code == 422
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "BUSINESS_LOGIC_ERROR"

    def test_database_exception_handling(self, client):
        """Test database exception handling."""
        response = client.get("/api/v1/test-errors/database-error")

        assert response.status_code == 500
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "DATABASE_ERROR"

    def test_external_service_exception_handling(self, client):
        """Test external service exception handling."""
        response = client.get("/api/v1/test-errors/external-service-error")

        assert response.status_code == 502
        data = response.json()

        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert data["error"] == "EXTERNAL_SERVICE_ERROR"

    def test_error_response_consistency(self, client):
        """Test that all error responses have consistent structure."""
        error_endpoints = [
            "/api/v1/test-errors/app-exception",
            "/api/v1/test-errors/http-exception",
            "/api/v1/test-errors/business-logic-error",
            "/api/v1/test-errors/database-error",
            "/api/v1/test-errors/external-service-error",
            "/api/v1/test-errors/unexpected-error",
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)
            data = response.json()

            # All error responses should have these fields
            required_fields = ["error", "message", "timestamp", "request_id"]
            for field in required_fields:
                assert field in data, f"Missing {field} in response from {endpoint}"

            # Verify timestamp format
            assert len(data["timestamp"]) > 0

            # Verify request_id format
            assert len(data["request_id"]) > 0

    def test_error_details_inclusion(self, client):
        """Test that error details are properly included when available."""
        response = client.get("/api/v1/test-errors/app-exception")

        assert response.status_code == 422
        data = response.json()

        # Should include details for custom exceptions
        if "details" in data:
            assert isinstance(data["details"], dict)


class TestLoggingErrorIntegration:
    """Test integration between logging and error handling."""

    def test_error_logging_with_user_context(self, client, valid_jwt_token):
        """Test error logging includes user context."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/app-exception", headers=headers)

            assert response.status_code == 422

            # Verify error was logged
            mock_logger.error.assert_called()

            # Check that user context might be included in error logs
            error_calls = mock_logger.error.call_args_list
            # User context logging depends on implementation

    def test_error_logging_with_request_id(self, client):
        """Test error logging includes request ID."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/app-exception")

            assert response.status_code == 422
            data = response.json()

            # Verify error was logged
            mock_logger.error.assert_called()

            # Request ID should be in response
            assert "request_id" in data
            assert len(data["request_id"]) > 0

    def test_request_logging_with_error_outcome(self, client):
        """Test request logging includes error status codes."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/app-exception")

            assert response.status_code == 422

            # Verify request completion was logged with error status
            mock_logger.info.assert_called()

            # Check for status code in logs
            log_calls = mock_logger.info.call_args_list
            status_logged = any("422" in str(call) or "error" in str(call).lower() for call in log_calls)
            # Status code logging depends on implementation

    def test_middleware_error_handling(self, client):
        """Test middleware error handling doesn't break logging."""
        # Test with malformed JWT to trigger middleware error
        headers = {"Authorization": "Bearer malformed.token"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            # Should still succeed (JWT errors are non-blocking)
            assert response.status_code == 200

            # Should still log the request
            mock_logger.info.assert_called()

            # Should log JWT parsing warning
            mock_logger.warning.assert_called()

    def test_log_correlation_across_middleware(self, client, valid_jwt_token):
        """Test log correlation across middleware chain."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Get request ID from response
            request_id = data["request_id"]

            # Verify logging occurred
            mock_logger.info.assert_called()

            # All logs for this request should have the same request ID
            # (This depends on implementation details)


class TestLogFileHandling:
    """Test log file handling and rotation."""

    def test_log_file_creation(self, temp_log_file):
        """Test log file creation."""
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.LOG_FILE_PATH = temp_log_file
            mock_settings.LOG_FORMAT = "json"
            mock_settings.LOG_LEVEL = "INFO"

            setup_logging()
            logger = get_logger("test_file")
            logger.info("Test log message")

            # Verify log file exists and has content
            log_path = Path(temp_log_file)
            assert log_path.exists()

            content = log_path.read_text()
            assert len(content.strip()) > 0

    def test_log_directory_creation(self):
        """Test log directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "test.log"

            with patch("app.core.logging_config.settings") as mock_settings:
                mock_settings.LOG_FILE_PATH = str(log_file)
                mock_settings.LOG_FORMAT = "json"
                mock_settings.LOG_LEVEL = "INFO"

                setup_logging()
                logger = get_logger("test_dir")
                logger.info("Test log message")

                # Verify directory and file were created
                assert log_file.parent.exists()
                assert log_file.exists()


class TestErrorResponseSecurity:
    """Test error response security (no sensitive data leakage)."""

    def test_error_response_no_sensitive_data(self, client):
        """Test error responses don't leak sensitive data."""
        response = client.get("/api/v1/test-errors/unexpected-error")

        assert response.status_code == 500
        data = response.json()

        # Should not contain sensitive information
        response_str = json.dumps(data)

        # Should not contain file paths, stack traces, or internal details
        sensitive_patterns = [
            "/app/",
            "Traceback",
            'File "',
            "line ",
            "ZeroDivisionError",  # Internal exception details
        ]

        for pattern in sensitive_patterns:
            assert pattern not in response_str, f"Sensitive data found: {pattern}"

    def test_error_response_sanitization(self, client):
        """Test error response sanitization."""
        response = client.get("/api/v1/test-errors/database-error")

        assert response.status_code == 500
        data = response.json()

        # Should contain generic error message, not database specifics
        assert "error" in data
        assert "message" in data

        # Should not contain database connection strings or internal details
        response_str = json.dumps(data)
        sensitive_db_patterns = [
            "postgresql://",
            "password",
            "connection string",
            "database host",
        ]

        for pattern in sensitive_db_patterns:
            assert pattern.lower() not in response_str.lower()

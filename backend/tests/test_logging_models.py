"""
Tests for logging models and formatters.
"""

import json
from datetime import datetime
from unittest.mock import Mock

from app.core.logging_models import (
    ErrorLogEntry,
    LogEntry,
    RequestLogEntry,
    ResponseLogEntry,
    create_error_context,
    create_request_context,
    create_response_context,
    format_log_record,
)


class TestLogEntry:
    """Test LogEntry model"""

    def test_log_entry_creation(self):
        """Test basic log entry creation"""
        entry = LogEntry(
            level="INFO",
            message="Test message",
            request_id="req_123",
            user_id="user_456",
        )

        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.request_id == "req_123"
        assert entry.user_id == "user_456"
        assert isinstance(entry.timestamp, datetime)

    def test_log_entry_with_extra(self):
        """Test log entry with extra fields"""
        extra_data = {"custom_field": "custom_value", "number": 42}
        entry = LogEntry(
            level="DEBUG",
            message="Debug message",
            extra=extra_data,
        )

        assert entry.extra == extra_data

    def test_log_entry_defaults(self):
        """Test log entry with default values"""
        entry = LogEntry(level="INFO", message="Test")

        assert entry.request_id is None
        assert entry.user_id is None
        assert entry.method is None
        assert entry.path is None
        assert entry.status_code is None
        assert entry.duration_ms is None
        assert entry.extra is None


class TestRequestLogEntry:
    """Test RequestLogEntry model"""

    def test_request_log_entry_creation(self):
        """Test request log entry creation"""
        entry = RequestLogEntry(
            level="INFO",
            message="Request started",
            method="GET",
            path="/api/test",
            query_params={"param1": "value1"},
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert entry.method == "GET"
        assert entry.path == "/api/test"
        assert entry.query_params == {"param1": "value1"}
        assert entry.client_ip == "192.168.1.1"
        assert entry.user_agent == "TestAgent/1.0"


class TestResponseLogEntry:
    """Test ResponseLogEntry model"""

    def test_response_log_entry_creation(self):
        """Test response log entry creation"""
        entry = ResponseLogEntry(
            level="INFO",
            message="Request completed",
            status_code=200,
            duration_ms=123.45,
            response_size=1024,
        )

        assert entry.status_code == 200
        assert entry.duration_ms == 123.45
        assert entry.response_size == 1024


class TestErrorLogEntry:
    """Test ErrorLogEntry model"""

    def test_error_log_entry_creation(self):
        """Test error log entry creation"""
        entry = ErrorLogEntry(
            level="ERROR",
            message="Error occurred",
            error_type="ValueError",
            error_message="Invalid value",
            stack_trace="Traceback...",
            context={"additional": "info"},
        )

        assert entry.error_type == "ValueError"
        assert entry.error_message == "Invalid value"
        assert entry.stack_trace == "Traceback..."
        assert entry.context == {"additional": "info"}


class TestFormatLogRecord:
    """Test format_log_record function"""

    def test_format_basic_record(self):
        """Test formatting basic log record"""
        mock_time = Mock()
        mock_time.isoformat.return_value = "2024-01-01T12:00:00Z"

        mock_level = Mock()
        mock_level.name = "INFO"

        record = {
            "time": mock_time,
            "level": mock_level,
            "message": "Test message",
            "name": "test_module",
            "function": "test_function",
            "line": 42,
        }

        result = format_log_record(record)
        data = json.loads(result)

        assert data["timestamp"] == "2024-01-01T12:00:00Z"
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["module"] == "test_module"
        assert data["function"] == "test_function"
        assert data["line"] == 42

    def test_format_record_with_extra(self):
        """Test formatting record with extra fields"""
        mock_time = Mock()
        mock_time.isoformat.return_value = "2024-01-01T12:00:00Z"

        mock_level = Mock()
        mock_level.name = "INFO"

        record = {
            "time": mock_time,
            "level": mock_level,
            "message": "Test message",
            "name": "test_module",
            "function": "test_function",
            "line": 42,
            "extra": {
                "request_id": "req_123",
                "user_id": "user_456",
            },
        }

        result = format_log_record(record)
        data = json.loads(result)

        assert data["request_id"] == "req_123"
        assert data["user_id"] == "user_456"

    def test_format_record_with_exception(self):
        """Test formatting record with exception"""
        mock_time = Mock()
        mock_time.isoformat.return_value = "2024-01-01T12:00:00Z"

        mock_exception_type = Mock()
        mock_exception_type.__name__ = "ValueError"

        mock_level = Mock()
        mock_level.name = "ERROR"

        record = {
            "time": mock_time,
            "level": mock_level,
            "message": "Error occurred",
            "name": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": {
                "type": mock_exception_type,
                "value": "Invalid value",
                "traceback": "Traceback...",
            },
        }

        result = format_log_record(record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["value"] == "Invalid value"
        assert data["exception"]["traceback"] == "Traceback..."


class TestContextCreators:
    """Test context creation functions"""

    def test_create_request_context(self):
        """Test create_request_context function"""
        context = create_request_context(
            request_id="req_123",
            method="POST",
            path="/api/test",
            user_id="user_456",
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            query_params={"param": "value"},
        )

        expected = {
            "request_id": "req_123",
            "method": "POST",
            "path": "/api/test",
            "user_id": "user_456",
            "client_ip": "192.168.1.1",
            "user_agent": "TestAgent/1.0",
            "query_params": {"param": "value"},
        }

        assert context == expected

    def test_create_request_context_minimal(self):
        """Test create_request_context with minimal parameters"""
        context = create_request_context(
            request_id="req_123",
            method="GET",
            path="/api/test",
        )

        expected = {
            "request_id": "req_123",
            "method": "GET",
            "path": "/api/test",
        }

        assert context == expected

    def test_create_response_context(self):
        """Test create_response_context function"""
        context = create_response_context(
            request_id="req_123",
            status_code=200,
            duration_ms=123.45,
            response_size=1024,
        )

        expected = {
            "request_id": "req_123",
            "status_code": 200,
            "duration_ms": 123.45,
            "response_size": 1024,
        }

        assert context == expected

    def test_create_response_context_minimal(self):
        """Test create_response_context with minimal parameters"""
        context = create_response_context(
            request_id="req_123",
            status_code=404,
            duration_ms=50.0,
        )

        expected = {
            "request_id": "req_123",
            "status_code": 404,
            "duration_ms": 50.0,
        }

        assert context == expected

    def test_create_error_context(self):
        """Test create_error_context function"""
        context = create_error_context(
            request_id="req_123",
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace="Traceback...",
            additional_context={"field": "email"},
        )

        expected = {
            "request_id": "req_123",
            "error_type": "ValueError",
            "error_message": "Invalid input",
            "stack_trace": "Traceback...",
            "field": "email",
        }

        assert context == expected

    def test_create_error_context_minimal(self):
        """Test create_error_context with minimal parameters"""
        context = create_error_context(
            request_id="req_123",
            error_type="RuntimeError",
            error_message="Something went wrong",
        )

        expected = {
            "request_id": "req_123",
            "error_type": "RuntimeError",
            "error_message": "Something went wrong",
        }

        assert context == expected

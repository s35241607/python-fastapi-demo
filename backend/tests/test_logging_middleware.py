"""
Tests for logging middleware.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from app.middleware.logging_middleware import (
    LoggingMiddleware,
    add_log_context,
    get_log_context,
    get_request_id,
)


class TestLoggingMiddleware:
    """Test LoggingMiddleware class"""

    def setup_method(self):
        """Setup test method"""
        self.app = FastAPI()
        self.middleware = LoggingMiddleware(
            self.app,
            skip_paths=["/health"],
            log_request_body=True,
            log_response_body=False,
        )

    @pytest.mark.asyncio
    async def test_middleware_skips_configured_paths(self):
        """Test that middleware skips configured paths"""
        request = Mock(spec=Request)
        request.url.path = "/health"

        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        call_next.return_value = mock_response

        with patch("app.middleware.logging_middleware.log_request") as mock_log_request:
            result = await self.middleware.dispatch(request, call_next)

            assert result == mock_response
            call_next.assert_called_once_with(request)
            mock_log_request.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.logging_middleware.log_request")
    @patch("app.middleware.logging_middleware.log_response")
    @patch("app.middleware.logging_middleware.time.time")
    @patch("uuid.uuid4")
    async def test_middleware_logs_successful_request(self, mock_uuid, mock_time, mock_log_response, mock_log_request):
        """Test middleware logs successful request"""
        # Setup mocks
        mock_uuid.return_value = "test-request-id"
        mock_time.side_effect = [1000.0, 1000.123, 1000.123]  # start and end times (extra for error case)

        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.query_params = {}
        request.headers = {"user-agent": "TestAgent/1.0"}
        request.client.host = "192.168.1.1"
        request.state = Mock()
        request.state.user_id = None

        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "1024"}
        call_next.return_value = mock_response

        # Execute
        result = await self.middleware.dispatch(request, call_next)

        # Verify
        assert result == mock_response
        assert request.state.request_id == "test-request-id"
        assert mock_response.headers["X-Request-ID"] == "test-request-id"

        mock_log_request.assert_called_once_with(
            method="GET",
            path="/api/test",
            request_id="test-request-id",
            user_id=None,
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            query_params=None,
        )

        # Verify response logging (allow for floating point precision differences)
        mock_log_response.assert_called_once()
        call_args = mock_log_response.call_args
        assert call_args[1]["request_id"] == "test-request-id"
        assert call_args[1]["status_code"] == 200
        assert abs(call_args[1]["duration_ms"] - 123.0) < 1.0
        assert call_args[1]["response_size"] == 1024

    @pytest.mark.asyncio
    @patch("app.middleware.logging_middleware.log_request")
    @patch("app.middleware.logging_middleware.log_error")
    @patch("app.middleware.logging_middleware.time.time")
    @patch("uuid.uuid4")
    async def test_middleware_logs_error(self, mock_uuid, mock_time, mock_log_error, mock_log_request):
        """Test middleware logs errors"""
        # Setup mocks
        mock_uuid.return_value = "test-request-id"
        mock_time.side_effect = [1000.0, 1000.456]  # start and end times

        request = Mock(spec=Request)
        request.url.path = "/api/error"
        request.method = "POST"
        request.query_params = {}
        request.headers = {}
        request.client.host = "192.168.1.1"
        request.state = Mock()
        request.state.user_id = None

        call_next = AsyncMock()
        test_exception = ValueError("Test error")
        call_next.side_effect = test_exception

        # Execute and expect exception
        with pytest.raises(ValueError):
            await self.middleware.dispatch(request, call_next)

        # Verify error logging (allow for floating point precision differences)
        mock_log_error.assert_called_once()
        call_args = mock_log_error.call_args
        assert call_args[1]["request_id"] == "test-request-id"
        assert call_args[1]["error_type"] == "ValueError"
        assert call_args[1]["error_message"] == "Test error"
        assert call_args[1]["additional_context"]["method"] == "POST"
        assert call_args[1]["additional_context"]["path"] == "/api/error"
        assert abs(call_args[1]["additional_context"]["duration_ms"] - 456.0) < 1.0

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test _get_client_ip with X-Forwarded-For header"""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.1, 192.168.1.1"}

        result = self.middleware._get_client_ip(request)

        assert result == "203.0.113.1"

    def test_get_client_ip_from_x_real_ip(self):
        """Test _get_client_ip with X-Real-IP header"""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.2"}

        result = self.middleware._get_client_ip(request)

        assert result == "203.0.113.2"

    def test_get_client_ip_from_client_host(self):
        """Test _get_client_ip from client host"""
        request = Mock(spec=Request)
        request.headers = {}
        request.client.host = "192.168.1.100"

        result = self.middleware._get_client_ip(request)

        assert result == "192.168.1.100"

    def test_get_client_ip_unknown(self):
        """Test _get_client_ip when no client info available"""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        result = self.middleware._get_client_ip(request)

        assert result == "unknown"

    @pytest.mark.asyncio
    async def test_log_request_body_json(self):
        """Test _log_request_body with JSON content"""
        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b'{"key": "value"}')
        request.headers = {"content-type": "application/json"}

        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            await self.middleware._log_request_body(request, "req_123")

            mock_logger.debug.assert_called_once_with(
                "Request body",
                extra={
                    "request_id": "req_123",
                    "content_type": "application/json",
                    "body": '{"key": "value"}',
                },
            )

    @pytest.mark.asyncio
    async def test_log_request_body_binary(self):
        """Test _log_request_body with binary content"""
        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n")
        request.headers = {"content-type": "image/png"}

        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            await self.middleware._log_request_body(request, "req_123")

            # Binary content types are not logged, so no debug call should be made
            mock_logger.debug.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_request_body_too_large(self):
        """Test _log_request_body with large content"""
        request = Mock(spec=Request)
        large_body = b"x" * 20000  # 20KB
        request.body = AsyncMock(return_value=large_body)
        request.headers = {"content-type": "application/json"}

        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            await self.middleware._log_request_body(request, "req_123")

            # Should not log large bodies
            mock_logger.debug.assert_not_called()


class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_request_id_from_state(self):
        """Test get_request_id when request has ID in state"""
        request = Mock(spec=Request)
        request.state.request_id = "existing-id"

        result = get_request_id(request)

        assert result == "existing-id"

    @patch("uuid.uuid4")
    def test_get_request_id_generate_new(self, mock_uuid):
        """Test get_request_id generates new ID when not in state"""
        mock_uuid.return_value = "new-generated-id"

        request = Mock(spec=Request)
        request.state = Mock()
        # Simulate missing request_id attribute
        del request.state.request_id

        result = get_request_id(request)

        assert result == "new-generated-id"

    def test_add_log_context_new(self):
        """Test add_log_context creates new context"""
        request = Mock(spec=Request)
        request.state = Mock()
        # Simulate missing log_context attribute initially
        del request.state.log_context

        add_log_context(request, key1="value1", key2="value2")

        assert request.state.log_context == {"key1": "value1", "key2": "value2"}

    def test_add_log_context_existing(self):
        """Test add_log_context updates existing context"""
        request = Mock(spec=Request)
        request.state.log_context = {"existing": "value"}

        add_log_context(request, key1="value1", key2="value2")

        expected = {"existing": "value", "key1": "value1", "key2": "value2"}
        assert request.state.log_context == expected

    def test_get_log_context_existing(self):
        """Test get_log_context returns existing context"""
        request = Mock(spec=Request)
        request.state.log_context = {"key": "value"}

        result = get_log_context(request)

        assert result == {"key": "value"}

    def test_get_log_context_missing(self):
        """Test get_log_context returns empty dict when no context"""
        request = Mock(spec=Request)
        request.state = Mock()
        # Simulate missing log_context attribute
        del request.state.log_context

        result = get_log_context(request)

        assert result == {}


class TestLoggingMiddlewareIntegration:
    """Integration tests for LoggingMiddleware"""

    def test_middleware_integration(self):
        """Test middleware integration with FastAPI"""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware, skip_paths=["/health"])

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        with patch("app.middleware.logging_middleware.log_request") as mock_log_request:
            with patch("app.middleware.logging_middleware.log_response") as mock_log_response:
                # Test normal endpoint (should be logged)
                response = client.get("/test")
                assert response.status_code == 200
                assert "X-Request-ID" in response.headers

                mock_log_request.assert_called()
                mock_log_response.assert_called()

                # Reset mocks
                mock_log_request.reset_mock()
                mock_log_response.reset_mock()

                # Test health endpoint (should be skipped)
                response = client.get("/health")
                assert response.status_code == 200

                mock_log_request.assert_not_called()
                mock_log_response.assert_not_called()

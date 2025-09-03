"""
Tests for logging configuration.
"""

from unittest.mock import Mock, patch

from app.core.logging_config import (
    get_logger,
    log_error,
    log_performance,
    log_request,
    log_response,
    log_with_context,
    setup_logging,
)


class TestSetupLogging:
    """Test setup_logging function"""

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_config.settings")
    def test_setup_logging_creates_log_directory(self, mock_settings, mock_logger):
        """Test that setup_logging creates logs directory"""
        mock_settings.is_development.return_value = True
        mock_settings.is_production.return_value = False
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.get_log_file_path.return_value = "logs/test.log"

        with patch("app.core.logging_config.Path") as mock_path:
            mock_log_dir = Mock()
            mock_log_file_path = Mock()
            mock_log_file_path.parent = Mock()
            mock_error_log_path = Mock()

            # Mock the parent / "error.log" operation
            mock_log_file_path.parent.__truediv__ = Mock(return_value=mock_error_log_path)

            def path_side_effect(path):
                if path == "logs":
                    return mock_log_dir
                else:
                    return mock_log_file_path

            mock_path.side_effect = path_side_effect

            setup_logging()

            mock_log_dir.mkdir.assert_called_once_with(exist_ok=True)

    @patch("app.core.logging_config.settings")
    @patch("app.core.logging_config.logger")
    def test_setup_logging_development_format(self, mock_logger, mock_settings):
        """Test setup_logging with development environment"""
        mock_settings.is_development.return_value = True
        mock_settings.is_production.return_value = False
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.LOG_FILE_PATH = "logs/test.log"

        setup_logging()

        # Verify logger.add was called multiple times (console, file, error file)
        assert mock_logger.add.call_count >= 3
        assert mock_logger.remove.called

    @patch("app.core.logging_config.settings")
    @patch("app.core.logging_config.logger")
    def test_setup_logging_production_format(self, mock_logger, mock_settings):
        """Test setup_logging with production environment"""
        mock_settings.is_development.return_value = False
        mock_settings.is_production.return_value = True
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_FILE_PATH = "logs/test.log"

        setup_logging()

        # Verify logger.add was called multiple times
        assert mock_logger.add.call_count >= 4  # console, file, error file, stderr
        assert mock_logger.remove.called


class TestGetLogger:
    """Test get_logger function"""

    @patch("app.core.logging_config.logger")
    def test_get_logger_without_name(self, mock_logger):
        """Test get_logger without name parameter"""
        result = get_logger()

        assert result == mock_logger
        mock_logger.bind.assert_not_called()

    @patch("app.core.logging_config.logger")
    def test_get_logger_with_name(self, mock_logger):
        """Test get_logger with name parameter"""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        result = get_logger("test_module")

        assert result == mock_bound_logger
        mock_logger.bind.assert_called_once_with(logger_name="test_module")


class TestLogWithContext:
    """Test log_with_context function"""

    @patch("app.core.logging_config.logger")
    def test_log_with_context_basic(self, mock_logger):
        """Test log_with_context with basic parameters"""
        mock_opt_logger = Mock()
        mock_logger.opt.return_value = mock_opt_logger

        log_with_context("INFO", "Test message")

        mock_logger.opt.assert_called_once_with(depth=1)
        mock_opt_logger.log.assert_called_once_with("INFO", "Test message", extra={})

    @patch("app.core.logging_config.logger")
    def test_log_with_context_with_context(self, mock_logger):
        """Test log_with_context with context"""
        mock_opt_logger = Mock()
        mock_logger.opt.return_value = mock_opt_logger

        context = {"request_id": "req_123", "user_id": "user_456"}
        log_with_context("ERROR", "Error message", context=context)

        mock_logger.opt.assert_called_once_with(depth=1)
        mock_opt_logger.log.assert_called_once_with("ERROR", "Error message", extra=context)

    @patch("app.core.logging_config.logger")
    def test_log_with_context_with_kwargs(self, mock_logger):
        """Test log_with_context with kwargs"""
        mock_opt_logger = Mock()
        mock_logger.opt.return_value = mock_opt_logger

        log_with_context("WARNING", "Warning message", custom_field="custom_value")

        expected_extra = {"custom_field": "custom_value"}
        mock_opt_logger.log.assert_called_once_with("WARNING", "Warning message", extra=expected_extra)


class TestLogRequest:
    """Test log_request function"""

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_request_context")
    def test_log_request_basic(self, mock_create_context, mock_logger):
        """Test log_request with basic parameters"""
        mock_context = {"request_id": "req_123", "method": "GET", "path": "/test"}
        mock_create_context.return_value = mock_context

        log_request(
            method="GET",
            path="/test",
            request_id="req_123",
        )

        mock_create_context.assert_called_once_with(
            request_id="req_123",
            method="GET",
            path="/test",
            user_id=None,
            client_ip=None,
            user_agent=None,
            query_params=None,
        )

        mock_logger.info.assert_called_once_with("Request started: GET /test", extra=mock_context)

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_request_context")
    def test_log_request_full(self, mock_create_context, mock_logger):
        """Test log_request with all parameters"""
        mock_context = {
            "request_id": "req_123",
            "method": "POST",
            "path": "/api/test",
            "user_id": "user_456",
            "client_ip": "192.168.1.1",
            "user_agent": "TestAgent/1.0",
            "query_params": {"param": "value"},
        }
        mock_create_context.return_value = mock_context

        log_request(
            method="POST",
            path="/api/test",
            request_id="req_123",
            user_id="user_456",
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            query_params={"param": "value"},
        )

        mock_create_context.assert_called_once_with(
            request_id="req_123",
            method="POST",
            path="/api/test",
            user_id="user_456",
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            query_params={"param": "value"},
        )


class TestLogResponse:
    """Test log_response function"""

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_response_context")
    def test_log_response_success(self, mock_create_context, mock_logger):
        """Test log_response with success status"""
        mock_context = {
            "request_id": "req_123",
            "status_code": 200,
            "duration_ms": 123.45,
        }
        mock_create_context.return_value = mock_context

        log_response(
            request_id="req_123",
            status_code=200,
            duration_ms=123.45,
        )

        mock_logger.log.assert_called_once_with("INFO", "Request completed: 200 (123.45ms)", extra=mock_context)

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_response_context")
    def test_log_response_client_error(self, mock_create_context, mock_logger):
        """Test log_response with client error status"""
        mock_context = {
            "request_id": "req_123",
            "status_code": 404,
            "duration_ms": 50.0,
        }
        mock_create_context.return_value = mock_context

        log_response(
            request_id="req_123",
            status_code=404,
            duration_ms=50.0,
        )

        mock_logger.log.assert_called_once_with("WARNING", "Request completed: 404 (50.00ms)", extra=mock_context)

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_response_context")
    def test_log_response_server_error(self, mock_create_context, mock_logger):
        """Test log_response with server error status"""
        mock_context = {
            "request_id": "req_123",
            "status_code": 500,
            "duration_ms": 1000.0,
        }
        mock_create_context.return_value = mock_context

        log_response(
            request_id="req_123",
            status_code=500,
            duration_ms=1000.0,
        )

        mock_logger.log.assert_called_once_with("ERROR", "Request completed: 500 (1000.00ms)", extra=mock_context)


class TestLogError:
    """Test log_error function"""

    @patch("app.core.logging_config.logger")
    @patch("app.core.logging_models.create_error_context")
    def test_log_error_basic(self, mock_create_context, mock_logger):
        """Test log_error with basic parameters"""
        mock_context = {
            "request_id": "req_123",
            "error_type": "ValueError",
            "error_message": "Invalid input",
        }
        mock_create_context.return_value = mock_context

        log_error(
            request_id="req_123",
            error_type="ValueError",
            error_message="Invalid input",
        )

        mock_create_context.assert_called_once_with(
            request_id="req_123",
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace=None,
            additional_context=None,
        )

        mock_logger.error.assert_called_once_with("Error occurred: ValueError - Invalid input", extra=mock_context)


class TestLogPerformance:
    """Test log_performance function"""

    @patch("app.core.logging_config.logger")
    def test_log_performance_fast(self, mock_logger):
        """Test log_performance with fast operation"""
        log_performance("database_query", 50.0)

        expected_extra = {
            "operation": "database_query",
            "duration_ms": 50.0,
            "performance": True,
        }

        mock_logger.log.assert_called_once_with(
            "INFO", "Performance: database_query completed in 50.00ms", extra=expected_extra
        )

    @patch("app.core.logging_config.logger")
    def test_log_performance_slow(self, mock_logger):
        """Test log_performance with slow operation"""
        log_performance("slow_operation", 1500.0)

        expected_extra = {
            "operation": "slow_operation",
            "duration_ms": 1500.0,
            "performance": True,
        }

        mock_logger.log.assert_called_once_with(
            "WARNING", "Performance: slow_operation completed in 1500.00ms", extra=expected_extra
        )

    @patch("app.core.logging_config.logger")
    def test_log_performance_with_context(self, mock_logger):
        """Test log_performance with additional context"""
        context = {"query": "SELECT * FROM users", "rows": 100}
        log_performance("database_query", 75.0, context=context)

        expected_extra = {
            "operation": "database_query",
            "duration_ms": 75.0,
            "performance": True,
            "query": "SELECT * FROM users",
            "rows": 100,
        }

        mock_logger.log.assert_called_once_with(
            "INFO", "Performance: database_query completed in 75.00ms", extra=expected_extra
        )

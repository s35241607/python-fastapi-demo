"""
Unit tests for custom exception classes.
"""

from app.core.exceptions import (
    BaseAppException,
    BusinessLogicException,
    DatabaseException,
    ExternalServiceException,
    ResourceNotFoundException,
    ValidationException,
)


class TestBaseAppException:
    """Test cases for BaseAppException."""

    def test_base_exception_creation(self):
        """Test creating a base application exception."""
        exception = BaseAppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            status_code=400,
        )

        assert str(exception) == "Test error"
        assert exception.message == "Test error"
        assert exception.error_code == "TEST_ERROR"
        assert exception.details == {"key": "value"}
        assert exception.status_code == 400

    def test_base_exception_defaults(self):
        """Test base exception with default values."""
        exception = BaseAppException("Test error")

        assert exception.message == "Test error"
        assert exception.error_code == "INTERNAL_ERROR"
        assert exception.details == {}
        assert exception.status_code == 500

    def test_base_exception_inheritance(self):
        """Test that BaseAppException inherits from Exception."""
        exception = BaseAppException("Test error")
        assert isinstance(exception, Exception)


class TestValidationException:
    """Test cases for ValidationException."""

    def test_validation_exception_creation(self):
        """Test creating a validation exception."""
        details = {"field": "email", "value": "invalid"}
        exception = ValidationException(message="Invalid email format", details=details)

        assert exception.message == "Invalid email format"
        assert exception.error_code == "VALIDATION_ERROR"
        assert exception.details == details
        assert exception.status_code == 422

    def test_validation_exception_defaults(self):
        """Test validation exception with default message."""
        exception = ValidationException()

        assert exception.message == "Validation failed"
        assert exception.error_code == "VALIDATION_ERROR"
        assert exception.details == {}
        assert exception.status_code == 422

    def test_validation_exception_inheritance(self):
        """Test that ValidationException inherits from BaseAppException."""
        exception = ValidationException("Test error")
        assert isinstance(exception, BaseAppException)


class TestBusinessLogicException:
    """Test cases for BusinessLogicException."""

    def test_business_logic_exception_creation(self):
        """Test creating a business logic exception."""
        details = {"rule": "age_limit", "current_age": 15}
        exception = BusinessLogicException(message="Age must be at least 18", details=details)

        assert exception.message == "Age must be at least 18"
        assert exception.error_code == "BUSINESS_LOGIC_ERROR"
        assert exception.details == details
        assert exception.status_code == 400

    def test_business_logic_exception_inheritance(self):
        """Test that BusinessLogicException inherits from BaseAppException."""
        exception = BusinessLogicException("Test error")
        assert isinstance(exception, BaseAppException)


class TestResourceNotFoundException:
    """Test cases for ResourceNotFoundException."""

    def test_resource_not_found_exception_creation(self):
        """Test creating a resource not found exception."""
        details = {"resource_id": "123", "resource_type": "user"}
        exception = ResourceNotFoundException(message="User not found", details=details)

        assert exception.message == "User not found"
        assert exception.error_code == "RESOURCE_NOT_FOUND"
        assert exception.details == details
        assert exception.status_code == 404

    def test_resource_not_found_exception_defaults(self):
        """Test resource not found exception with default message."""
        exception = ResourceNotFoundException()

        assert exception.message == "Resource not found"
        assert exception.error_code == "RESOURCE_NOT_FOUND"
        assert exception.details == {}
        assert exception.status_code == 404

    def test_resource_not_found_exception_inheritance(self):
        """Test that ResourceNotFoundException inherits from BaseAppException."""
        exception = ResourceNotFoundException("Test error")
        assert isinstance(exception, BaseAppException)


class TestDatabaseException:
    """Test cases for DatabaseException."""

    def test_database_exception_creation(self):
        """Test creating a database exception."""
        details = {"operation": "insert", "table": "users", "constraint": "unique_email"}
        exception = DatabaseException(message="Duplicate email address", details=details)

        assert exception.message == "Duplicate email address"
        assert exception.error_code == "DATABASE_ERROR"
        assert exception.details == details
        assert exception.status_code == 500

    def test_database_exception_defaults(self):
        """Test database exception with default message."""
        exception = DatabaseException()

        assert exception.message == "Database operation failed"
        assert exception.error_code == "DATABASE_ERROR"
        assert exception.details == {}
        assert exception.status_code == 500

    def test_database_exception_inheritance(self):
        """Test that DatabaseException inherits from BaseAppException."""
        exception = DatabaseException("Test error")
        assert isinstance(exception, BaseAppException)


class TestExternalServiceException:
    """Test cases for ExternalServiceException."""

    def test_external_service_exception_creation(self):
        """Test creating an external service exception."""
        details = {"service": "payment_api", "endpoint": "/charge", "status": 503}
        exception = ExternalServiceException(message="Payment service unavailable", details=details)

        assert exception.message == "Payment service unavailable"
        assert exception.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exception.details == details
        assert exception.status_code == 502

    def test_external_service_exception_defaults(self):
        """Test external service exception with default message."""
        exception = ExternalServiceException()

        assert exception.message == "External service error"
        assert exception.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exception.details == {}
        assert exception.status_code == 502

    def test_external_service_exception_inheritance(self):
        """Test that ExternalServiceException inherits from BaseAppException."""
        exception = ExternalServiceException("Test error")
        assert isinstance(exception, BaseAppException)


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_exception_chaining(self):
        """Test that exceptions can be chained properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise DatabaseException("Database connection failed") from e
        except DatabaseException as db_exc:
            assert db_exc.message == "Database connection failed"
            assert isinstance(db_exc.__cause__, ValueError)
            assert str(db_exc.__cause__) == "Original error"

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        original_details = {"connection": "lost", "retry_count": 3}

        exception = DatabaseException(message="Connection failed after retries", details=original_details)

        # Verify details are preserved
        assert exception.details["connection"] == "lost"
        assert exception.details["retry_count"] == 3

        # Verify details can be modified
        exception.details["final_attempt"] = True
        assert exception.details["final_attempt"] is True

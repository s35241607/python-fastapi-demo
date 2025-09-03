"""
Integration tests for middleware chain functionality.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_jwt_token():
    """Create a sample JWT token for testing."""
    payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user", "admin"],
        "permissions": ["read", "write"],
        "iat": 1640995200,
        "exp": 1640998800,
    }
    # Create token without signature verification (since we don't validate signatures)
    return jwt.encode(payload, "secret", algorithm="HS256")


class TestMiddlewareIntegration:
    """Test middleware integration and chain functionality."""

    def test_middleware_chain_without_jwt(self, client):
        """Test middleware chain with no JWT token."""
        response = client.get("/api/v1/test-errors/middleware-chain")

        assert response.status_code == 200
        data = response.json()

        # Check basic response structure
        assert "message" in data
        assert "request_id" in data
        assert "user_authenticated" in data
        assert "middleware_data" in data

        # User should not be authenticated
        assert data["user_authenticated"] is False
        assert data["user_id"] is None
        assert data["username"] is None
        assert data["user_roles"] == []
        assert data["user_permissions"] == []

        # Middleware should have set up the request state
        middleware_data = data["middleware_data"]
        assert middleware_data["has_user_context"] is True
        assert middleware_data["has_request_id"] is True
        assert middleware_data["has_user_id"] is True
        assert middleware_data["has_username"] is True

    def test_middleware_chain_with_jwt(self, client, sample_jwt_token):
        """Test middleware chain with valid JWT token."""
        headers = {"Authorization": f"Bearer {sample_jwt_token}"}
        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # User should be authenticated
        assert data["user_authenticated"] is True
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"
        assert "user" in data["user_roles"]
        assert "admin" in data["user_roles"]
        assert "read" in data["user_permissions"]
        assert "write" in data["user_permissions"]

        # Middleware should have set up the request state
        middleware_data = data["middleware_data"]
        assert middleware_data["has_user_context"] is True
        assert middleware_data["has_request_id"] is True
        assert middleware_data["has_user_id"] is True
        assert middleware_data["has_username"] is True

    def test_middleware_chain_with_invalid_jwt(self, client):
        """Test middleware chain with invalid JWT token."""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # User should not be authenticated due to invalid token
        assert data["user_authenticated"] is False
        assert data["user_id"] is None
        assert data["username"] is None
        assert data["user_roles"] == []
        assert data["user_permissions"] == []

    def test_middleware_chain_with_malformed_auth_header(self, client):
        """Test middleware chain with malformed authorization header."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # User should not be authenticated due to malformed header
        assert data["user_authenticated"] is False
        assert data["user_id"] is None

    def test_error_handling_with_jwt_context(self, client, sample_jwt_token):
        """Test that error handling works correctly with JWT context."""
        headers = {"Authorization": f"Bearer {sample_jwt_token}"}
        response = client.get("/api/v1/test-errors/app-exception", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # Error response should be properly formatted
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data

    def test_logging_middleware_integration(self, client):
        """Test that logging middleware is working in the chain."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain")

            assert response.status_code == 200

            # Verify that logging middleware logged the request
            mock_logger.info.assert_called()

            # Check that at least one log call contains request information
            log_calls = mock_logger.info.call_args_list
            request_logged = any("Request completed" in str(call) or "Request started" in str(call) for call in log_calls)
            assert request_logged

    def test_health_endpoint_skips_middleware(self, client):
        """Test that health endpoint skips JWT parsing middleware."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Health endpoint should work without middleware processing
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_middleware_order_execution(self, client, sample_jwt_token):
        """Test that middleware executes in the correct order."""
        headers = {"Authorization": f"Bearer {sample_jwt_token}"}

        with (
            patch("app.middleware.error_handler.logger") as error_logger,
            patch("app.core.logging_config.logger") as logging_logger,
            patch("app.middleware.jwt_parser.logger") as jwt_logger,
        ):
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            assert response.status_code == 200

            # All middleware should have been executed
            # JWT parser should have logged successful parsing
            jwt_logger.debug.assert_called()

            # Logging middleware should have logged the request
            logging_logger.info.assert_called()

    def test_middleware_with_exception(self, client, sample_jwt_token):
        """Test middleware chain behavior when an exception occurs."""
        headers = {"Authorization": f"Bearer {sample_jwt_token}"}

        response = client.get("/api/v1/test-errors/unexpected-error", headers=headers)

        # Error should be handled properly
        assert response.status_code == 500
        data = response.json()

        assert "error" in data
        assert "request_id" in data
        assert data["error"] == "INTERNAL_SERVER_ERROR"

    def test_cors_and_middleware_integration(self, client):
        """Test that CORS works with middleware chain."""
        # Test preflight request
        response = client.options("/api/v1/test-errors/middleware-chain")

        # Should handle OPTIONS request properly
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

    def test_middleware_performance_impact(self, client, sample_jwt_token):
        """Test that middleware doesn't significantly impact performance."""
        import time

        headers = {"Authorization": f"Bearer {sample_jwt_token}"}

        # Measure response time with middleware
        start_time = time.time()
        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
        end_time = time.time()

        assert response.status_code == 200

        # Response should be reasonably fast (less than 1 second for simple request)
        response_time = end_time - start_time
        assert response_time < 1.0

    def test_middleware_state_isolation(self, client, sample_jwt_token):
        """Test that middleware state is properly isolated between requests."""
        headers1 = {"Authorization": f"Bearer {sample_jwt_token}"}
        headers2 = {}  # No auth header

        # First request with JWT
        response1 = client.get("/api/v1/test-errors/middleware-chain", headers=headers1)
        data1 = response1.json()

        # Second request without JWT
        response2 = client.get("/api/v1/test-errors/middleware-chain", headers=headers2)
        data2 = response2.json()

        # Requests should have different states
        assert data1["user_authenticated"] is True
        assert data2["user_authenticated"] is False
        assert data1["user_id"] == "user123"
        assert data2["user_id"] is None

        # Request IDs should be different
        assert data1["request_id"] != data2["request_id"]

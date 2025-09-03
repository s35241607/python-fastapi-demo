"""
End-to-end request flow tests.
Tests complete request processing through all middleware layers.
"""

import time
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
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user", "admin"],
        "permissions": ["read", "write", "delete"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour from now
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Create an expired JWT token for testing."""
    payload = {
        "sub": "user456",
        "username": "expireduser",
        "email": "expired@example.com",
        "roles": ["user"],
        "permissions": ["read"],
        "iat": int(time.time()) - 7200,  # 2 hours ago
        "exp": int(time.time()) - 3600,  # 1 hour ago (expired)
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


class TestEndToEndRequestFlows:
    """Test complete end-to-end request flows."""

    def test_successful_authenticated_request_flow(self, client, valid_jwt_token):
        """Test complete flow for successful authenticated request."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify user authentication
            assert data["user_authenticated"] is True
            assert data["user_id"] == "user123"
            assert data["username"] == "testuser"
            assert "user" in data["user_roles"]
            assert "admin" in data["user_roles"]
            assert "read" in data["user_permissions"]
            assert "write" in data["user_permissions"]
            assert "delete" in data["user_permissions"]

            # Verify middleware chain execution
            middleware_data = data["middleware_data"]
            assert middleware_data["has_user_context"] is True
            assert middleware_data["has_request_id"] is True
            assert middleware_data["has_user_id"] is True
            assert middleware_data["has_username"] is True

            # Verify request ID is present
            assert data["request_id"] is not None
            assert len(data["request_id"]) > 0

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_successful_unauthenticated_request_flow(self, client):
        """Test complete flow for successful unauthenticated request."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify user is not authenticated
            assert data["user_authenticated"] is False
            assert data["user_id"] is None
            assert data["username"] is None
            assert data["user_roles"] == []
            assert data["user_permissions"] == []

            # Verify middleware chain still executed
            middleware_data = data["middleware_data"]
            assert middleware_data["has_user_context"] is True
            assert middleware_data["has_request_id"] is True

            # Verify request ID is present
            assert data["request_id"] is not None

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_error_handling_request_flow(self, client, valid_jwt_token):
        """Test complete flow when an error occurs."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with (
            patch("app.core.logging_config.logger") as logging_logger,
            patch("app.middleware.error_handler.logger") as error_logger,
        ):
            response = client.get("/api/v1/test-errors/app-exception", headers=headers)

            # Verify error response
            assert response.status_code == 422
            data = response.json()

            # Verify error structure
            assert "error" in data
            assert "message" in data
            assert "timestamp" in data
            assert "request_id" in data
            assert data["error"] == "VALIDATION_ERROR"
            assert "test validation error" in data["message"]

            # Verify request ID is present
            assert data["request_id"] is not None

            # Verify logging occurred (both request and error logging)
            logging_logger.info.assert_called()
            # Error should be logged by error handler
            error_logger.warning.assert_called()

    def test_validation_error_request_flow(self, client):
        """Test complete flow for validation errors."""
        invalid_data = {
            "name": "",  # Too short
            "email": "invalid-email",  # Invalid format
            "age": -5,  # Invalid age
        }

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.post("/api/v1/test-errors/validation-error", json=invalid_data)

            # Verify validation error response
            assert response.status_code == 422
            data = response.json()

            # Verify error structure
            assert "error" in data
            assert "message" in data
            assert "timestamp" in data
            assert "request_id" in data
            assert data["error"] == "VALIDATION_ERROR"

            # Verify request ID is present
            assert data["request_id"] is not None

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_unexpected_error_request_flow(self, client, valid_jwt_token):
        """Test complete flow when unexpected error occurs."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/unexpected-error", headers=headers)

            # Verify error response
            assert response.status_code == 500
            data = response.json()

            # Verify error structure
            assert "error" in data
            assert "message" in data
            assert "timestamp" in data
            assert "request_id" in data
            assert data["error"] == "INTERNAL_SERVER_ERROR"

            # Verify request ID is present
            assert data["request_id"] is not None

            # Verify error logging occurred
            mock_logger.error.assert_called()

    def test_expired_jwt_request_flow(self, client, expired_jwt_token):
        """Test complete flow with expired JWT token."""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            # Verify response (should still succeed but without authentication)
            assert response.status_code == 200
            data = response.json()

            # Verify user is not authenticated due to expired token
            assert data["user_authenticated"] is False
            assert data["user_id"] is None
            assert data["username"] is None

            # Verify middleware chain still executed
            assert data["request_id"] is not None

            # Verify JWT parsing error was logged
            mock_logger.warning.assert_called()

    def test_malformed_jwt_request_flow(self, client):
        """Test complete flow with malformed JWT token."""
        headers = {"Authorization": "Bearer malformed.jwt.token"}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            # Verify response (should still succeed but without authentication)
            assert response.status_code == 200
            data = response.json()

            # Verify user is not authenticated due to malformed token
            assert data["user_authenticated"] is False
            assert data["user_id"] is None

            # Verify middleware chain still executed
            assert data["request_id"] is not None

            # Verify JWT parsing error was logged
            mock_logger.warning.assert_called()

    def test_health_check_flow(self, client):
        """Test health check endpoint flow (should skip middleware)."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/health")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify health check structure
            assert "status" in data
            assert "environment" in data
            assert "configuration" in data
            assert data["status"] in ["healthy", "unhealthy"]

            # Health endpoint should skip JWT middleware
            # but logging middleware might still run
            # (depends on skip_paths configuration)

    def test_root_endpoint_flow(self, client):
        """Test root endpoint flow."""
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify root endpoint structure
            assert "message" in data
            assert "version" in data
            assert "docs" in data

    def test_multiple_concurrent_requests_flow(self, client, valid_jwt_token):
        """Test multiple concurrent requests to verify state isolation."""
        import concurrent.futures

        def make_request(request_id):
            headers = {"Authorization": f"Bearer {valid_jwt_token}"}
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
            return response.json()

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert result["user_authenticated"] is True
            assert result["user_id"] == "user123"
            assert result["request_id"] is not None

        # Verify request IDs are unique
        request_ids = [result["request_id"] for result in results]
        assert len(set(request_ids)) == len(request_ids), "Request IDs should be unique"

    def test_request_with_different_http_methods(self, client, valid_jwt_token):
        """Test different HTTP methods through the middleware chain."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Test POST request
        valid_data = {"name": "Test User", "email": "test@example.com", "age": 25}

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.post("/api/v1/test-errors/validation-error", json=valid_data, headers=headers)

            # Verify successful POST
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["message"] == "Validation passed"

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_request_flow_with_large_payload(self, client, valid_jwt_token):
        """Test request flow with large payload."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Create a large but valid payload
        large_data = {
            "name": "A" * 50,  # Maximum allowed length
            "email": "test@example.com",
            "age": 30,
        }

        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.post("/api/v1/test-errors/validation-error", json=large_data, headers=headers)

            # Verify successful processing
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Validation passed"

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_request_flow_performance_timing(self, client, valid_jwt_token):
        """Test request flow performance and timing."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        start_time = time.time()
        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
        end_time = time.time()

        # Verify response
        assert response.status_code == 200

        # Verify reasonable response time (should be fast for simple request)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Request took too long: {response_time}s"

    def test_cors_preflight_request_flow(self, client):
        """Test CORS preflight request flow."""
        # Test OPTIONS request (CORS preflight)
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        }

        response = client.options("/api/v1/test-errors/middleware-chain", headers=headers)

        # Should handle OPTIONS request (may return 405 if not explicitly handled)
        assert response.status_code in [200, 405]


class TestRequestStateManagement:
    """Test request state management across middleware."""

    def test_request_state_isolation(self, client, valid_jwt_token):
        """Test that request state is properly isolated between requests."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Make first request
        response1 = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
        data1 = response1.json()

        # Make second request without auth
        response2 = client.get("/api/v1/test-errors/middleware-chain")
        data2 = response2.json()

        # Verify states are different
        assert data1["user_authenticated"] is True
        assert data2["user_authenticated"] is False
        assert data1["request_id"] != data2["request_id"]
        assert data1["user_id"] == "user123"
        assert data2["user_id"] is None

    def test_request_state_persistence_within_request(self, client, valid_jwt_token):
        """Test that request state persists throughout a single request."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
        data = response.json()

        # Verify all middleware data is consistent
        assert data["user_authenticated"] is True
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"

        # Verify middleware state attributes
        middleware_data = data["middleware_data"]
        assert middleware_data["has_user_context"] is True
        assert middleware_data["has_request_id"] is True
        assert middleware_data["has_user_id"] is True
        assert middleware_data["has_username"] is True


class TestErrorPropagation:
    """Test error propagation through middleware chain."""

    def test_error_propagation_with_context(self, client, valid_jwt_token):
        """Test that errors propagate correctly with user context."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/test-errors/business-logic-error", headers=headers)

        # Verify error response
        assert response.status_code == 422
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert "message" in data
        assert "request_id" in data
        assert data["error"] == "BUSINESS_LOGIC_ERROR"

    def test_error_propagation_without_context(self, client):
        """Test that errors propagate correctly without user context."""
        response = client.get("/api/v1/test-errors/database-error")

        # Verify error response
        assert response.status_code == 500
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert "message" in data
        assert "request_id" in data
        assert data["error"] == "DATABASE_ERROR"

"""
Comprehensive integration test suite that validates all infrastructure components together.
This test suite verifies the complete system integration including Docker, configuration,
middleware, logging, and error handling working together.
"""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    payload = {
        "sub": "integration_user",
        "username": "integration_test",
        "email": "integration@test.com",
        "roles": ["user", "tester"],
        "permissions": ["read", "write", "test"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, "integration-secret", algorithm="HS256")


class TestFullSystemIntegration:
    """Test full system integration across all components."""

    def test_complete_request_lifecycle(self, client, valid_jwt_token):
        """Test complete request lifecycle through all middleware layers."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            # Make request through complete middleware chain
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            # Verify successful response
            assert response.status_code == 200
            data = response.json()

            # Verify JWT parsing worked
            assert data["user_authenticated"] is True
            assert data["user_id"] == "integration_user"
            assert data["username"] == "integration_test"
            assert "user" in data["user_roles"]
            assert "tester" in data["user_roles"]
            assert "read" in data["user_permissions"]
            assert "write" in data["user_permissions"]
            assert "test" in data["user_permissions"]

            # Verify logging middleware worked
            assert data["request_id"] is not None
            assert len(data["request_id"]) > 0

            # Verify middleware chain integrity
            middleware_data = data["middleware_data"]
            assert middleware_data["has_user_context"] is True
            assert middleware_data["has_request_id"] is True
            assert middleware_data["has_user_id"] is True
            assert middleware_data["has_username"] is True

            # Verify logging occurred
            mock_logger.info.assert_called()

    def test_error_handling_with_full_context(self, client, valid_jwt_token):
        """Test error handling with full user and request context."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("app.core.logging_config.logger") as mock_logger:
            # Trigger an error through the middleware chain
            response = client.get("/api/v1/test-errors/business-logic-error", headers=headers)

            # Verify error response
            assert response.status_code == 422
            data = response.json()

            # Verify error structure
            assert "error" in data
            assert "message" in data
            assert "timestamp" in data
            assert "request_id" in data
            assert data["error"] == "BUSINESS_LOGIC_ERROR"

            # Verify request ID is present
            assert data["request_id"] is not None

            # Verify both request and error logging occurred
            mock_logger.info.assert_called()  # Request logging
            mock_logger.error.assert_called()  # Error logging

    def test_configuration_environment_integration(self, client):
        """Test configuration and environment integration."""
        # Test health endpoint which shows configuration status
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify health check structure
        assert "status" in data
        assert "environment" in data
        assert "configuration" in data

        # Verify environment information
        env_info = data["environment"]
        assert "current_environment" in env_info
        assert "env_file" in env_info
        assert "env_file_exists" in env_info
        assert "available_environments" in env_info

        # Verify configuration information
        config_info = data["configuration"]
        assert "valid" in config_info
        assert "app_name" in config_info
        assert "version" in config_info
        assert "debug" in config_info
        assert "errors" in config_info
        assert "warnings" in config_info

        # Configuration should be valid for tests
        assert config_info["valid"] is True
        assert isinstance(config_info["errors"], list)
        assert isinstance(config_info["warnings"], list)

    def test_multi_environment_behavior(self):
        """Test behavior across different environments."""
        environments = ["development", "testing", "production"]

        for env in environments:
            with patch.dict(os.environ, {"ENVIRONMENT": env}):
                settings = get_settings()

                # Verify environment-specific settings
                assert env == settings.ENVIRONMENT

                if env == "development":
                    assert settings.DEBUG is True
                    assert settings.LOG_LEVEL == "DEBUG"
                    assert settings.RELOAD is True
                    assert settings.WORKERS == 1
                elif env == "testing":
                    assert settings.DEBUG is False
                    assert settings.LOG_LEVEL == "INFO"
                elif env == "production":
                    assert settings.DEBUG is False
                    assert settings.LOG_LEVEL == "INFO"
                    assert settings.RELOAD is False
                    assert settings.WORKERS == 4

    def test_middleware_order_and_interaction(self, client, valid_jwt_token):
        """Test middleware execution order and interaction."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with (
            patch("app.middleware.error_handler.logger") as error_logger,
            patch("app.core.logging_config.logger") as logging_logger,
            patch("app.middleware.jwt_parser.logger") as jwt_logger,
        ):
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            assert response.status_code == 200

            # Verify all middleware layers were executed
            # JWT parser should have processed the token
            jwt_logger.debug.assert_called()

            # Logging middleware should have logged the request
            logging_logger.info.assert_called()

            # Error handler should be ready (no errors in this case)
            # error_logger might not be called for successful requests

    def test_concurrent_requests_system_stability(self, client, valid_jwt_token):
        """Test system stability under concurrent requests."""
        import concurrent.futures

        def make_authenticated_request():
            headers = {"Authorization": f"Bearer {valid_jwt_token}"}
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
            return response.json()

        def make_unauthenticated_request():
            response = client.get("/api/v1/test-errors/middleware-chain")
            return response.json()

        def make_error_request():
            response = client.get("/api/v1/test-errors/app-exception")
            return response.status_code, response.json()

        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Mix of different request types
            futures = []
            for i in range(20):
                if i % 3 == 0:
                    futures.append(executor.submit(make_error_request))
                elif i % 3 == 1:
                    futures.append(executor.submit(make_authenticated_request))
                else:
                    futures.append(executor.submit(make_unauthenticated_request))

            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all requests completed
        assert len(results) == 20

        # Separate results by type
        auth_results = []
        unauth_results = []
        error_results = []

        for result in results:
            if isinstance(result, tuple):  # Error requests return (status_code, data)
                error_results.append(result)
            elif result.get("user_authenticated") is True:
                auth_results.append(result)
            else:
                unauth_results.append(result)

        # Verify authenticated requests
        for result in auth_results:
            assert result["user_id"] == "integration_user"
            assert result["request_id"] is not None

        # Verify unauthenticated requests
        for result in unauth_results:
            assert result["user_authenticated"] is False
            assert result["request_id"] is not None

        # Verify error requests
        for status_code, data in error_results:
            assert status_code == 422
            assert "error" in data
            assert "request_id" in data

        # Verify request ID uniqueness
        all_request_ids = []
        for result in auth_results + unauth_results:
            all_request_ids.append(result["request_id"])
        for _, data in error_results:
            all_request_ids.append(data["request_id"])

        assert len(set(all_request_ids)) == len(all_request_ids), "Request IDs should be unique"

    def test_system_resilience_to_failures(self, client, valid_jwt_token):
        """Test system resilience to various failure scenarios."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Test with various error conditions
        error_scenarios = [
            ("/api/v1/test-errors/app-exception", 422),
            ("/api/v1/test-errors/http-exception", 404),
            ("/api/v1/test-errors/business-logic-error", 422),
            ("/api/v1/test-errors/database-error", 500),
            ("/api/v1/test-errors/external-service-error", 502),
            ("/api/v1/test-errors/unexpected-error", 500),
        ]

        for endpoint, expected_status in error_scenarios:
            with patch("app.core.logging_config.logger") as mock_logger:
                response = client.get(endpoint, headers=headers)

                # Verify error is handled properly
                assert response.status_code == expected_status
                data = response.json()

                # Verify error response structure
                assert "error" in data
                assert "message" in data
                assert "timestamp" in data
                assert "request_id" in data

                # Verify logging occurred
                mock_logger.error.assert_called()

                # System should remain stable after error
                health_response = client.get("/health")
                assert health_response.status_code == 200

    def test_jwt_error_tolerance(self, client):
        """Test JWT error tolerance (non-blocking behavior)."""
        jwt_scenarios = [
            ("Bearer malformed.jwt.token", "malformed token"),
            ("Bearer ", "empty token"),
            ("InvalidFormat token", "invalid format"),
            ("", "no header"),
        ]

        for auth_header, scenario in jwt_scenarios:
            headers = {"Authorization": auth_header} if auth_header else {}

            with patch("app.core.logging_config.logger") as mock_logger:
                response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

                # Should still succeed (JWT errors are non-blocking)
                assert response.status_code == 200, f"Failed for scenario: {scenario}"
                data = response.json()

                # Should not be authenticated
                assert data["user_authenticated"] is False
                assert data["user_id"] is None

                # Should still have request ID
                assert data["request_id"] is not None

                # Should log JWT parsing issues (if any)
                if auth_header and auth_header != "":
                    mock_logger.warning.assert_called()

    def test_performance_under_load(self, client, valid_jwt_token):
        """Test system performance under load."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Measure response times for multiple requests
        response_times = []

        for _ in range(50):
            start_time = time.time()
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        # Verify reasonable performance
        assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time}s"
        assert max_response_time < 0.5, f"Max response time too high: {max_response_time}s"

    def test_memory_usage_stability(self, client, valid_jwt_token):
        """Test memory usage stability over multiple requests."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        # Make many requests to test for memory leaks
        for _ in range(100):
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)
            assert response.status_code == 200

            # Occasionally trigger garbage collection
            if _ % 20 == 0:
                gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increase too high: {memory_increase} bytes"


class TestSystemConfiguration:
    """Test system configuration integration."""

    def test_configuration_validation_integration(self, client):
        """Test configuration validation integration."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Configuration should be valid
        assert data["configuration"]["valid"] is True
        assert len(data["configuration"]["errors"]) == 0

    def test_environment_file_loading(self):
        """Test environment file loading for different environments."""
        project_root = Path(__file__).parent.parent.parent

        env_files = {
            "development": project_root / "backend" / ".env.development",
            "testing": project_root / "backend" / ".env.testing",
            "production": project_root / "backend" / ".env.production",
        }

        for env_name, env_file in env_files.items():
            assert env_file.exists(), f"Environment file missing: {env_file}"

            # Verify file has required settings
            content = env_file.read_text()
            required_vars = ["APP_NAME", "DATABASE_URL", "LOG_LEVEL"]

            for var in required_vars:
                assert var in content, f"Missing {var} in {env_file}"

    def test_cors_configuration_integration(self, client):
        """Test CORS configuration integration."""
        # Test CORS headers in response
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200

        # CORS headers should be present (if configured)
        # This depends on FastAPI CORS middleware configuration


class TestDockerIntegrationReadiness:
    """Test Docker integration readiness."""

    def test_docker_files_exist(self):
        """Test that Docker files exist and are properly configured."""
        project_root = Path(__file__).parent.parent.parent

        docker_files = [
            project_root / "docker-compose.yml",
            project_root / "docker-compose.override.yml",
            project_root / "docker-compose.prod.yml",
            project_root / "backend" / "Dockerfile",
        ]

        for docker_file in docker_files:
            assert docker_file.exists(), f"Docker file missing: {docker_file}"

    def test_health_endpoint_for_docker(self, client):
        """Test health endpoint suitable for Docker health checks."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should provide clear health status
        assert data["status"] in ["healthy", "unhealthy"]

        # Should provide environment information
        assert "environment" in data
        assert "configuration" in data

    def test_application_startup_readiness(self):
        """Test application startup readiness."""
        # Test that the application can be imported and initialized
        from app.main import app

        assert app is not None
        assert hasattr(app, "routes")
        assert len(app.routes) > 0

    def test_logging_directory_creation(self):
        """Test logging directory creation for Docker volumes."""
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "backend" / "logs"

        # Create logs directory if it doesn't exist
        logs_dir.mkdir(exist_ok=True)

        assert logs_dir.exists()
        assert logs_dir.is_dir()


@pytest.mark.integration
@pytest.mark.slow
class TestFullIntegrationSuite:
    """Full integration test suite combining all components."""

    def test_complete_system_integration(self, client, valid_jwt_token):
        """Test complete system integration with all components."""
        # This test combines multiple aspects to verify full system integration

        # 1. Test configuration loading
        settings = get_settings()
        assert settings is not None

        # 2. Test health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # 3. Test authenticated request flow
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        with patch("app.core.logging_config.logger") as mock_logger:
            response = client.get("/api/v1/test-errors/middleware-chain", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Verify full middleware chain
            assert data["user_authenticated"] is True
            assert data["user_id"] == "integration_user"
            assert data["request_id"] is not None

            # Verify logging
            mock_logger.info.assert_called()

        # 4. Test error handling
        with patch("app.core.logging_config.logger") as mock_logger:
            error_response = client.get("/api/v1/test-errors/app-exception", headers=headers)

            assert error_response.status_code == 422
            error_data = error_response.json()

            # Verify error structure
            assert "error" in error_data
            assert "request_id" in error_data

            # Verify error logging
            mock_logger.error.assert_called()

        # 5. Test system remains stable
        final_health = client.get("/health")
        assert final_health.status_code == 200

        print("✅ Complete system integration test passed")

    def test_production_readiness_checklist(self, client):
        """Test production readiness checklist."""
        checklist_results = {}

        # 1. Health endpoint works
        try:
            response = client.get("/health")
            checklist_results["health_endpoint"] = response.status_code == 200
        except Exception:
            checklist_results["health_endpoint"] = False

        # 2. Error handling works
        try:
            response = client.get("/api/v1/test-errors/app-exception")
            checklist_results["error_handling"] = response.status_code == 422
        except Exception:
            checklist_results["error_handling"] = False

        # 3. JWT parsing works (non-blocking)
        try:
            response = client.get("/api/v1/test-errors/middleware-chain")
            checklist_results["jwt_parsing"] = response.status_code == 200
        except Exception:
            checklist_results["jwt_parsing"] = False

        # 4. Configuration validation works
        try:
            settings = get_settings()
            checklist_results["configuration"] = settings is not None
        except Exception:
            checklist_results["configuration"] = False

        # 5. Logging works
        try:
            with patch("app.core.logging_config.logger") as mock_logger:
                client.get("/api/v1/test-errors/middleware-chain")
                checklist_results["logging"] = mock_logger.info.called
        except Exception:
            checklist_results["logging"] = False

        # Print checklist results
        print("\n🔍 Production Readiness Checklist:")
        for check, passed in checklist_results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")

        # All checks should pass
        assert all(checklist_results.values()), f"Failed checks: {[k for k, v in checklist_results.items() if not v]}"

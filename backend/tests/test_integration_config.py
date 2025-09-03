"""
Integration tests for multi-environment configuration system
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.environment import Environment, get_current_environment
from app.main import app


class TestMultiEnvironmentIntegration:
    """Integration tests for multi-environment configuration"""

    def test_development_environment_loading(self):
        """Test loading development environment configuration"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = get_settings()
            assert settings.ENVIRONMENT == "development"
            assert settings.DEBUG is True
            assert "Development" in settings.APP_NAME

    def test_testing_environment_loading(self):
        """Test loading testing environment configuration"""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            settings = get_settings()
            assert settings.ENVIRONMENT == "testing"
            assert settings.DEBUG is False
            assert "Testing" in settings.APP_NAME

    def test_production_environment_loading(self):
        """Test loading production environment configuration"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = get_settings()
            assert settings.ENVIRONMENT == "production"
            assert settings.DEBUG is False
            assert settings.APP_NAME == "Ticket System API"

    def test_health_endpoint_works(self):
        """Test health endpoint works with current environment"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "current_environment" in data["environment"]
        assert data["configuration"]["valid"] is True

    def test_cors_origins_environment_specific(self):
        """Test CORS origins are environment-specific"""
        # Development should have localhost origins
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            dev_settings = get_settings()
            assert any("localhost" in origin for origin in dev_settings.BACKEND_CORS_ORIGINS)

        # Production should not have localhost origins
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            prod_settings = get_settings()
            assert not any("localhost" in origin for origin in prod_settings.BACKEND_CORS_ORIGINS)

    def test_database_url_environment_specific(self):
        """Test database URLs are environment-specific"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            dev_settings = get_settings()
            assert "ticket_system_dev" in dev_settings.DATABASE_URL

        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            test_settings = get_settings()
            assert "ticket_system_test" in test_settings.DATABASE_URL

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            prod_settings = get_settings()
            assert "ticket_system_prod" in prod_settings.DATABASE_URL

    def test_log_level_environment_specific(self):
        """Test log levels are environment-specific"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            dev_settings = get_settings()
            assert dev_settings.LOG_LEVEL == "DEBUG"

        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            test_settings = get_settings()
            assert test_settings.LOG_LEVEL == "INFO"

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            prod_settings = get_settings()
            assert prod_settings.LOG_LEVEL == "INFO"

    def test_server_settings_environment_specific(self):
        """Test server settings are environment-specific"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            dev_settings = get_settings()
            assert dev_settings.RELOAD is True
            assert dev_settings.WORKERS == 1

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            prod_settings = get_settings()
            assert prod_settings.RELOAD is False
            assert prod_settings.WORKERS == 4

    def test_environment_helper_methods_integration(self):
        """Test environment helper methods work with actual settings"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = get_settings()
            assert settings.is_development() is True
            assert settings.is_testing() is False
            assert settings.is_production() is False

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = get_settings()
            assert settings.is_development() is False
            assert settings.is_testing() is False
            assert settings.is_production() is True


class TestConfigurationValidationIntegration:
    """Integration tests for configuration validation"""

    def test_health_endpoint_returns_configuration_status(self):
        """Test health endpoint returns configuration validation status"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "status" in data
        assert "environment" in data
        assert "configuration" in data

        # Check environment info
        env_info = data["environment"]
        assert "current_environment" in env_info
        assert "env_file" in env_info
        assert "env_file_exists" in env_info
        assert "available_environments" in env_info

        # Check configuration info
        config_info = data["configuration"]
        assert "valid" in config_info
        assert "app_name" in config_info
        assert "version" in config_info
        assert "debug" in config_info
        assert "errors" in config_info
        assert "warnings" in config_info

    def test_configuration_validation_with_current_environment(self):
        """Test configuration validation works with current environment"""
        client = TestClient(app)
        response = client.get("/health")

        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["configuration"]["valid"], bool)
        assert isinstance(data["configuration"]["errors"], list)
        assert isinstance(data["configuration"]["warnings"], list)


class TestEnvironmentSwitching:
    """Test environment switching functionality"""

    def test_get_settings_respects_environment_variable(self):
        """Test that get_settings respects ENVIRONMENT variable"""
        # Test development
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            dev_settings = get_settings()
            assert dev_settings.is_development()
            assert dev_settings.DEBUG is True

        # Test production
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            prod_settings = get_settings()
            assert prod_settings.is_production()
            assert prod_settings.DEBUG is False

    def test_environment_detection_functions(self):
        """Test environment detection utility functions"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert get_current_environment() == Environment.DEVELOPMENT

        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            assert get_current_environment() == Environment.TESTING

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert get_current_environment() == Environment.PRODUCTION

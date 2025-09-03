"""
Tests for configuration management system
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.config_validator import ConfigurationError, ConfigValidator
from app.core.environment import Environment, get_current_environment, get_environment_info


class TestSettings:
    """Test Settings class"""

    def test_default_settings(self):
        """Test default settings values"""
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.APP_NAME == "FastAPI Demo"
        assert settings.DEBUG is True
        assert settings.VERSION == "0.1.0"

    def test_environment_validation(self):
        """Test environment validation"""
        # Valid environments
        for env in ["development", "testing", "production"]:
            settings = Settings(ENVIRONMENT=env)
            assert env == settings.ENVIRONMENT

        # Invalid environment
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="invalid")

    def test_cors_origins_validation(self):
        """Test CORS origins validation"""
        # List format
        settings = Settings(BACKEND_CORS_ORIGINS=["http://localhost:3000", "https://example.com"])
        assert len(settings.BACKEND_CORS_ORIGINS) == 2

        # String format (comma-separated)
        settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,https://example.com")
        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS

    def test_environment_helper_methods(self):
        """Test environment helper methods"""
        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.is_development() is True
        assert dev_settings.is_testing() is False
        assert dev_settings.is_production() is False

        prod_settings = Settings(ENVIRONMENT="production")
        assert prod_settings.is_development() is False
        assert prod_settings.is_testing() is False
        assert prod_settings.is_production() is True


class TestConfigValidator:
    """Test ConfigValidator class"""

    def test_validate_database_config_valid(self):
        """Test valid database configuration"""
        settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db")
        validator = ConfigValidator(settings)
        assert validator.validate_database_config() is True
        assert len(validator.errors) == 0

    def test_validate_database_config_missing_url(self):
        """Test missing database URL"""
        settings = Settings(DATABASE_URL="")
        validator = ConfigValidator(settings)
        assert validator.validate_database_config() is False
        assert "DATABASE_URL is required" in validator.errors

    def test_validate_database_config_production_sqlite_warning(self):
        """Test SQLite warning in production"""
        settings = Settings(ENVIRONMENT="production", DATABASE_URL="sqlite+aiosqlite:///./test.db")
        validator = ConfigValidator(settings)
        validator.validate_database_config()
        assert "SQLite is not recommended for production" in validator.warnings

    def test_validate_security_config_valid(self):
        """Test valid security configuration"""
        settings = Settings(SECRET_KEY="secure-secret-key", ACCESS_TOKEN_EXPIRE_MINUTES=30)
        validator = ConfigValidator(settings)
        assert validator.validate_security_config() is True
        assert len(validator.errors) == 0

    def test_validate_security_config_missing_secret(self):
        """Test missing secret key"""
        settings = Settings(SECRET_KEY="")
        validator = ConfigValidator(settings)
        assert validator.validate_security_config() is False
        assert "SECRET_KEY is required" in validator.errors

    def test_validate_security_config_production_default_secret(self):
        """Test default secret key in production"""
        settings = Settings(ENVIRONMENT="production", SECRET_KEY="your-secret-key-here")
        validator = ConfigValidator(settings)
        assert validator.validate_security_config() is False
        assert "Production SECRET_KEY must not use default/development values" in validator.errors

    def test_validate_cors_config_production_localhost(self):
        """Test localhost CORS in production"""
        settings = Settings(ENVIRONMENT="production", BACKEND_CORS_ORIGINS=["http://localhost:3000", "https://example.com"])
        validator = ConfigValidator(settings)
        assert validator.validate_cors_config() is False
        assert any("localhost" in error for error in validator.errors)

    def test_validate_logging_config_valid(self):
        """Test valid logging configuration"""
        settings = Settings(LOG_LEVEL="INFO", LOG_FILE_PATH="logs/app.log")
        validator = ConfigValidator(settings)
        assert validator.validate_logging_config() is True

    def test_validate_logging_config_invalid_level(self):
        """Test invalid log level"""
        settings = Settings(LOG_LEVEL="INVALID")
        validator = ConfigValidator(settings)
        assert validator.validate_logging_config() is False
        assert "LOG_LEVEL must be one of" in validator.errors[0]

    def test_validate_environment_specific_production(self):
        """Test production-specific validations"""
        settings = Settings(
            ENVIRONMENT="production",
            DEBUG=True,  # Should be False in production
            RELOAD=True,  # Should be False in production
        )
        validator = ConfigValidator(settings)
        assert validator.validate_environment_specific() is False
        assert "DEBUG must be False in production" in validator.errors
        assert "RELOAD must be False in production" in validator.errors

    def test_validate_all_success(self):
        """Test successful validation of all checks"""
        settings = Settings(
            ENVIRONMENT="development",
            DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db",
            SECRET_KEY="secure-secret-key",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            BACKEND_CORS_ORIGINS=["http://localhost:3000"],
            LOG_LEVEL="INFO",
            LOG_FILE_PATH="logs/app.log",
        )
        validator = ConfigValidator(settings)
        assert validator.validate_all() is True

    def test_get_validation_report(self):
        """Test validation report generation"""
        settings = Settings()
        validator = ConfigValidator(settings)
        report = validator.get_validation_report()

        assert "valid" in report
        assert "environment" in report
        assert "errors" in report
        assert "warnings" in report
        assert "config_summary" in report
        assert report["environment"] == "development"

    def test_raise_on_errors(self):
        """Test raising ConfigurationError on validation failure"""
        settings = Settings(SECRET_KEY="")  # Invalid config
        validator = ConfigValidator(settings)

        with pytest.raises(ConfigurationError):
            validator.raise_on_errors()


class TestEnvironmentUtils:
    """Test environment utility functions"""

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_get_current_environment_from_env_var(self):
        """Test getting environment from environment variable"""
        env = get_current_environment()
        assert env == Environment.PRODUCTION

    @patch.dict(os.environ, {}, clear=True)
    def test_get_current_environment_default(self):
        """Test default environment when no env var set"""
        env = get_current_environment()
        assert env == Environment.DEVELOPMENT

    @patch.dict(os.environ, {"ENVIRONMENT": "invalid"})
    def test_get_current_environment_invalid(self):
        """Test invalid environment defaults to development"""
        env = get_current_environment()
        assert env == Environment.DEVELOPMENT

    def test_get_environment_info(self):
        """Test environment info gathering"""
        info = get_environment_info()

        assert "current_environment" in info
        assert "env_file" in info
        assert "env_file_exists" in info
        assert "environment_variable" in info
        assert "available_environments" in info

        assert info["current_environment"] in ["development", "testing", "production"]
        assert len(info["available_environments"]) == 3


class TestGetSettings:
    """Test get_settings function"""

    @patch("os.path.exists")
    @patch("app.core.config.Settings")
    def test_get_settings_with_env_file(self, mock_settings, mock_exists):
        """Test get_settings with environment-specific file"""
        mock_exists.return_value = True

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            get_settings()
            mock_settings.assert_called_with(_env_file=".env.production")

    @patch("os.path.exists")
    @patch("app.core.config.Settings")
    def test_get_settings_fallback_to_default(self, mock_settings, mock_exists):
        """Test get_settings fallback to default .env file"""
        mock_exists.return_value = False

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            get_settings()
            mock_settings.assert_called_with(_env_file=".env")

"""
Configuration validation utilities for multi-environment setup
"""

import os
from typing import Any

from .config import Settings


class ConfigurationError(Exception):
    """Raised when configuration validation fails"""

    pass


class ConfigValidator:
    """Validates configuration settings for different environments"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_database_config(self) -> bool:
        """Validate database configuration"""
        if not self.settings.DATABASE_URL:
            self.errors.append("DATABASE_URL is required")
            return False

        # Check database URL format
        if self.settings.is_production():
            if "sqlite" in self.settings.DATABASE_URL.lower():
                self.warnings.append("SQLite is not recommended for production")

            # Check for placeholder values in production
            if "${" in self.settings.DATABASE_URL:
                self.errors.append("Production DATABASE_URL contains unresolved placeholders")
                return False

        return True

    def validate_security_config(self) -> bool:
        """Validate security configuration"""
        valid = True

        # Check SECRET_KEY
        if not self.settings.SECRET_KEY:
            self.errors.append("SECRET_KEY is required")
            valid = False
        elif self.settings.SECRET_KEY in ["your-secret-key-here", "dev-secret-key-change-in-production"]:
            if self.settings.is_production():
                self.errors.append("Production SECRET_KEY must not use default/development values")
                valid = False
            else:
                self.warnings.append("Using default SECRET_KEY - change for production")

        # Check for placeholder values in production
        if self.settings.is_production() and "${" in self.settings.SECRET_KEY:
            self.errors.append("Production SECRET_KEY contains unresolved placeholders")
            valid = False

        # Validate token expiration
        if self.settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            self.errors.append("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
            valid = False

        return valid

    def validate_cors_config(self) -> bool:
        """Validate CORS configuration"""
        if not self.settings.BACKEND_CORS_ORIGINS:
            self.warnings.append("No CORS origins configured")
            return True

        # Check for wildcard in production
        if self.settings.is_production():
            for origin in self.settings.BACKEND_CORS_ORIGINS:
                if origin == "*" or "localhost" in origin or "127.0.0.1" in origin:
                    self.errors.append(f"Production CORS origin '{origin}' is not secure")
                    return False

        return True

    def validate_logging_config(self) -> bool:
        """Validate logging configuration"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if self.settings.LOG_LEVEL not in valid_levels:
            self.errors.append(f"LOG_LEVEL must be one of: {valid_levels}")
            return False

        # Check log file path
        log_dir = os.path.dirname(self.settings.LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError as e:
                self.errors.append(f"Cannot create log directory '{log_dir}': {e}")
                return False

        return True

    def validate_environment_specific(self) -> bool:
        """Validate environment-specific configurations"""
        valid = True

        if self.settings.is_development():
            # Development-specific validations
            if not self.settings.DEBUG:
                self.warnings.append("DEBUG is typically True in development")

            if self.settings.WORKERS > 1:
                self.warnings.append("Multiple workers not recommended in development")

        elif self.settings.is_production():
            # Production-specific validations
            if self.settings.DEBUG:
                self.errors.append("DEBUG must be False in production")
                valid = False

            if self.settings.RELOAD:
                self.errors.append("RELOAD must be False in production")
                valid = False

            if self.settings.LOG_LEVEL == "DEBUG":
                self.warnings.append("DEBUG log level not recommended in production")

        return valid

    def validate_all(self) -> bool:
        """Run all validation checks"""
        self.errors.clear()
        self.warnings.clear()

        validations = [
            self.validate_database_config(),
            self.validate_security_config(),
            self.validate_cors_config(),
            self.validate_logging_config(),
            self.validate_environment_specific(),
        ]

        return all(validations)

    def get_validation_report(self) -> dict[str, Any]:
        """Get detailed validation report"""
        is_valid = self.validate_all()

        return {
            "valid": is_valid,
            "environment": self.settings.ENVIRONMENT,
            "errors": self.errors,
            "warnings": self.warnings,
            "config_summary": {
                "app_name": self.settings.APP_NAME,
                "debug": self.settings.DEBUG,
                "database_type": "postgresql" if "postgresql" in self.settings.DATABASE_URL else "sqlite",
                "cors_origins_count": len(self.settings.BACKEND_CORS_ORIGINS),
                "log_level": self.settings.LOG_LEVEL,
            },
        }

    def raise_on_errors(self):
        """Raise ConfigurationError if validation fails"""
        if not self.validate_all():
            error_msg = f"Configuration validation failed for environment '{self.settings.ENVIRONMENT}':\n"
            error_msg += "\n".join(f"  - {error}" for error in self.errors)
            raise ConfigurationError(error_msg)


def validate_configuration(settings: Settings) -> dict[str, Any]:
    """Validate configuration and return report"""
    validator = ConfigValidator(settings)
    return validator.get_validation_report()


def ensure_valid_configuration(settings: Settings):
    """Ensure configuration is valid, raise exception if not"""
    validator = ConfigValidator(settings)
    validator.raise_on_errors()

    # Print warnings if any
    if validator.warnings:
        print("Configuration warnings:")
        for warning in validator.warnings:
            print(f"  - {warning}")

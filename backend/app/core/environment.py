"""
Environment detection and management utilities
"""

import os
from enum import Enum


class Environment(str, Enum):
    """Supported environments"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


def get_current_environment() -> Environment:
    """Get current environment from environment variable"""
    env_str = os.getenv("ENVIRONMENT", Environment.DEVELOPMENT.value).lower()

    try:
        return Environment(env_str)
    except ValueError:
        # Default to development if invalid environment specified
        return Environment.DEVELOPMENT


def set_environment(environment: Environment):
    """Set environment variable"""
    os.environ["ENVIRONMENT"] = environment.value


def get_env_file_path(environment: Environment | None = None) -> str:
    """Get the path to the environment file"""
    if environment is None:
        environment = get_current_environment()

    return f".env.{environment.value}"


def is_development() -> bool:
    """Check if running in development environment"""
    return get_current_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_current_environment() == Environment.TESTING


def is_production() -> bool:
    """Check if running in production environment"""
    return get_current_environment() == Environment.PRODUCTION


def get_environment_info() -> dict:
    """Get comprehensive environment information"""
    current_env = get_current_environment()
    env_file = get_env_file_path(current_env)
    env_file_exists = os.path.exists(env_file)

    return {
        "current_environment": current_env.value,
        "env_file": env_file,
        "env_file_exists": env_file_exists,
        "environment_variable": os.getenv("ENVIRONMENT"),
        "available_environments": [env.value for env in Environment],
    }

import os

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Current environment")

    # Application settings
    APP_NAME: str = "FastAPI Demo"
    DEBUG: bool = True
    VERSION: str = "0.1.0"

    # Database settings (async)
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FORMAT: str = "json"

    def get_log_file_path(self) -> str:
        """Get environment-specific log file path"""
        if self.is_development():
            return "logs/app-dev.log"
        elif self.is_testing():
            return "logs/app-test.log"
        else:
            return "logs/app.log"

    # Server settings
    RELOAD: bool = False
    WORKERS: int = 1

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("CORS origins must be a list or comma-separated string")

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed_environments = ["development", "testing", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v

    def is_development(self) -> bool:
        """Check if current environment is development"""
        return self.ENVIRONMENT == "development"

    def is_testing(self) -> bool:
        """Check if current environment is testing"""
        return self.ENVIRONMENT == "testing"

    def is_production(self) -> bool:
        """Check if current environment is production"""
        return self.ENVIRONMENT == "production"

    model_config = ConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


def get_settings() -> Settings:
    """Factory function to create settings instance with proper environment detection"""
    environment = os.getenv("ENVIRONMENT", "development")
    env_file = f".env.{environment}"

    # Check if environment-specific file exists
    if os.path.exists(env_file):
        return Settings(_env_file=env_file)
    else:
        # Fallback to default .env file
        return Settings(_env_file=".env")


# Create settings instance
settings = get_settings()

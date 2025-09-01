from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FastAPI Demo"
    DEBUG: bool = True
    
    # Database settings (example)
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Security settings (example)
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
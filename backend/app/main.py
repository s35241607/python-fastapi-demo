from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.v1.routers import api_router
from app.core.config import settings
from app.core.config_validator import ensure_valid_configuration, validate_configuration
from app.core.environment import get_environment_info
from app.core.exceptions import BaseAppException
from app.core.logging_config import get_logger
from app.db.base import engine
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.jwt_parser import JWTParserMiddleware
from app.middleware.logging_middleware import LoggingMiddleware

# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    logger.info("🚀 Starting up application...")

    # Validate configuration on startup
    try:
        ensure_valid_configuration(settings)
        logger.info(f"✅ Configuration validated for environment: {settings.ENVIRONMENT}")
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise

    # Print environment info
    env_info = get_environment_info()
    logger.info(
        "Environment information",
        extra={
            "environment": env_info["current_environment"],
            "config_file": env_info["env_file"],
            "config_file_exists": env_info["env_file_exists"],
        },
    )

    # 這裡可以初始化資料庫連線池等
    yield

    # 關閉時執行
    logger.info("🛑 Shutting down application...")
    await engine.dispose()


def configure_middleware(app: FastAPI) -> None:
    """Configure middleware in the correct order."""
    # Add middleware in correct order (outer to inner)
    # 1. Error handling middleware (outermost - catches all errors)
    app.add_middleware(ErrorHandlerMiddleware)

    # 2. Logging middleware (logs requests/responses)
    app.add_middleware(
        LoggingMiddleware,
        skip_paths=["/health", "/metrics", "/favicon.ico"],
        log_request_body=settings.is_development(),  # Only log request body in development
        log_response_body=False,  # Generally avoid logging response body
    )

    # 3. JWT parser middleware (innermost - parses user information)
    app.add_middleware(
        JWTParserMiddleware,
        skip_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/favicon.ico"],
        header_name="authorization",
        token_prefix="Bearer ",
    )


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="A clean async FastAPI application",
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Configure middleware
    configure_middleware(app)

    # Add exception handlers for specific exception types
    from app.middleware.error_handler import (
        handle_app_exception,
        handle_http_exception,
        handle_pydantic_validation_exception,
        handle_validation_exception,
    )

    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(ValidationError, handle_pydantic_validation_exception)
    app.add_exception_handler(BaseAppException, handle_app_exception)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": f"Welcome to {settings.APP_NAME}!", "version": settings.VERSION, "docs": "/docs"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint with environment info"""
        env_info = get_environment_info()
        config_report = validate_configuration(settings)

        return {
            "status": "healthy" if config_report["valid"] else "unhealthy",
            "environment": env_info,
            "configuration": {
                "valid": config_report["valid"],
                "app_name": settings.APP_NAME,
                "version": settings.VERSION,
                "debug": settings.DEBUG,
                "errors": config_report["errors"] if not config_report["valid"] else [],
                "warnings": config_report["warnings"],
            },
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
    )

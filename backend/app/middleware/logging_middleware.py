"""
Logging middleware for FastAPI to capture request/response information.
"""

import contextlib
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger, log_error, log_request, log_response

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses with structured logging.

    Features:
    - Generates unique request IDs
    - Logs request start with method, path, and client info
    - Logs response with status code and duration
    - Captures user information if available
    - Handles errors gracefully
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: list[str] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """
        Initialize logging middleware.

        Args:
            app: ASGI application
            skip_paths: List of paths to skip logging (e.g., health checks)
            log_request_body: Whether to log request body (be careful with sensitive data)
            log_response_body: Whether to log response body (be careful with large responses)
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics", "/favicon.ico"]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for use in other parts of the application
        request.state.request_id = request_id

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Extract user information if available (from JWT middleware)
        user_id = getattr(request.state, "user_id", None)

        # Extract query parameters
        query_params = dict(request.query_params) if request.query_params else None

        # Log request start
        start_time = time.time()

        try:
            log_request(
                method=request.method,
                path=request.url.path,
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
                query_params=query_params,
            )

            # Log request body if enabled (be careful with sensitive data)
            if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
                await self._log_request_body(request, request_id)

            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Get response size if possible
            response_size = None
            if hasattr(response, "headers") and "content-length" in response.headers:
                with contextlib.suppress(ValueError, TypeError):
                    response_size = int(response.headers["content-length"])

            # Log response
            log_response(
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=response_size,
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            log_error(
                request_id=request_id,
                error_type=type(e).__name__,
                error_message=str(e),
                additional_context={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )

            # Re-raise the exception to be handled by error middleware
            raise

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded headers (common in reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    async def _log_request_body(self, request: Request, request_id: str) -> None:
        """
        Log request body if enabled.

        Args:
            request: FastAPI request object
            request_id: Unique request identifier
        """
        try:
            # Read body
            body = await request.body()

            # Only log if body is not empty and not too large
            if body and len(body) < 10000:  # Limit to 10KB
                content_type = request.headers.get("content-type", "")

                # Only log text-based content types
                if any(ct in content_type for ct in ["application/json", "application/xml", "text/"]):
                    try:
                        body_str = body.decode("utf-8")
                        logger.debug(
                            "Request body",
                            extra={
                                "request_id": request_id,
                                "content_type": content_type,
                                "body": body_str,
                            },
                        )
                    except UnicodeDecodeError:
                        logger.debug(
                            "Request body (binary)",
                            extra={
                                "request_id": request_id,
                                "content_type": content_type,
                                "body_size": len(body),
                            },
                        )
        except Exception as e:
            logger.warning(
                "Failed to log request body",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
            )


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID or generated UUID if not found
    """
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def add_log_context(request: Request, **context) -> None:
    """
    Add additional context to request for logging.

    Args:
        request: FastAPI request object
        **context: Additional context to add
    """
    if not hasattr(request.state, "log_context"):
        request.state.log_context = {}

    request.state.log_context.update(context)


def get_log_context(request: Request) -> dict:
    """
    Get log context from request state.

    Args:
        request: FastAPI request object

    Returns:
        Log context dictionary
    """
    return getattr(request.state, "log_context", {})

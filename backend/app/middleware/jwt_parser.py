"""
JWT parsing middleware for extracting user information from JWT tokens.

This middleware parses JWT tokens and extracts user information without validating
the token signature, as validation is handled by Kong API Gateway.
"""

from typing import Any

from fastapi import Request
from jose import JWTError, jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.schemas.user import JWTParseResult, UserContext


class JWTParserMiddleware(BaseHTTPMiddleware):
    """
    Middleware to parse JWT tokens and extract user information.

    Features:
    - Parses JWT tokens from Authorization header
    - Extracts user information without signature validation
    - Injects user context into request state
    - Error-tolerant (doesn't block requests on parsing failures)
    - Logs parsing errors for debugging
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: list[str] = None,
        header_name: str = "authorization",
        token_prefix: str = "Bearer ",
    ):
        """
        Initialize JWT parser middleware.

        Args:
            app: ASGI application
            skip_paths: List of paths to skip JWT parsing (e.g., health checks, public endpoints)
            header_name: Header name to look for JWT token (default: "authorization")
            token_prefix: Token prefix to strip from header value (default: "Bearer ")
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        self.header_name = header_name.lower()
        self.token_prefix = token_prefix

    async def dispatch(self, request: Request, call_next):
        """
        Process request and parse JWT token if present.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        # Skip JWT parsing for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Get request ID for logging (should be set by logging middleware)
        request_id = getattr(request.state, "request_id", "unknown")

        # Parse JWT token and extract user information
        parse_result = await self._parse_jwt_from_request(request, request_id)

        # Inject user context into request state
        if parse_result.success and parse_result.user_context:
            request.state.user_context = parse_result.user_context
            request.state.user_id = parse_result.user_context.user_id
            request.state.username = parse_result.user_context.username
            request.state.user_roles = parse_result.user_context.roles
            request.state.user_permissions = parse_result.user_context.permissions

            logger.debug(
                "JWT parsed successfully",
                extra={
                    "request_id": request_id,
                    "user_id": parse_result.user_context.user_id,
                    "username": parse_result.user_context.username,
                    "roles": parse_result.user_context.roles,
                },
            )
        else:
            # Set empty user context for unauthenticated requests
            request.state.user_context = UserContext()
            request.state.user_id = None
            request.state.username = None
            request.state.user_roles = []
            request.state.user_permissions = []

            if parse_result.error:
                logger.debug(
                    "JWT parsing failed",
                    extra={
                        "request_id": request_id,
                        "error": parse_result.error,
                        "error_type": parse_result.error_type,
                    },
                )

        # Continue with request processing
        return await call_next(request)

    async def _parse_jwt_from_request(self, request: Request, request_id: str) -> JWTParseResult:
        """
        Parse JWT token from request headers.

        Args:
            request: FastAPI request object
            request_id: Request ID for logging

        Returns:
            JWTParseResult with parsing outcome
        """
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get(self.header_name)
            if not auth_header:
                return JWTParseResult(
                    success=False,
                    error="No authorization header found",
                    error_type="MISSING_HEADER",
                )

            # Remove token prefix (e.g., "Bearer ")
            if not auth_header.startswith(self.token_prefix):
                return JWTParseResult(
                    success=False,
                    error=f"Authorization header does not start with '{self.token_prefix}'",
                    error_type="INVALID_HEADER_FORMAT",
                )

            token = auth_header[len(self.token_prefix) :].strip()
            if not token:
                return JWTParseResult(
                    success=False,
                    error="Empty token after removing prefix",
                    error_type="EMPTY_TOKEN",
                )

            # Parse JWT token without signature verification
            # Since Kong handles validation, we only need to extract claims
            try:
                # Decode without verification to extract claims
                claims = jwt.get_unverified_claims(token)
            except JWTError as e:
                return JWTParseResult(
                    success=False,
                    error=f"Failed to decode JWT token: {str(e)}",
                    error_type="JWT_DECODE_ERROR",
                )

            # Extract user information from claims
            user_context = await self._extract_user_context(claims, request_id)

            return JWTParseResult(
                success=True,
                user_context=user_context,
            )

        except Exception as e:
            logger.error(
                "Unexpected error during JWT parsing",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return JWTParseResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_type="UNEXPECTED_ERROR",
            )

    async def _extract_user_context(self, claims: dict[str, Any], request_id: str) -> UserContext:
        """
        Extract user context from JWT claims.

        Args:
            claims: JWT claims dictionary
            request_id: Request ID for logging

        Returns:
            UserContext with extracted information
        """
        try:
            # Extract standard JWT claims
            user_id = claims.get("sub")  # Subject (user ID)
            username = claims.get("preferred_username") or claims.get("username")
            email = claims.get("email")
            issued_at = claims.get("iat")
            expires_at = claims.get("exp")
            token_type = claims.get("typ") or claims.get("token_type")

            # Extract roles and permissions
            roles = []
            permissions = []

            # Try different common claim names for roles
            if "roles" in claims:
                roles = self._extract_list_claim(claims["roles"])
            elif "realm_access" in claims and "roles" in claims["realm_access"]:
                # Keycloak format
                roles = self._extract_list_claim(claims["realm_access"]["roles"])
            elif "groups" in claims:
                # Some systems use groups as roles
                roles = self._extract_list_claim(claims["groups"])

            # Try different common claim names for permissions
            if "permissions" in claims:
                permissions = self._extract_list_claim(claims["permissions"])
            elif "scope" in claims:
                # OAuth2 scopes as permissions
                scope_str = claims["scope"]
                if isinstance(scope_str, str):
                    permissions = scope_str.split()
                else:
                    permissions = self._extract_list_claim(scope_str)

            return UserContext(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles,
                permissions=permissions,
                token_type=token_type,
                issued_at=issued_at,
                expires_at=expires_at,
                raw_claims=claims,
            )

        except Exception as e:
            logger.warning(
                "Error extracting user context from JWT claims",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "claims_keys": list(claims.keys()) if claims else [],
                },
            )
            # Return minimal user context with available information
            return UserContext(
                user_id=claims.get("sub"),
                raw_claims=claims,
            )

    def _extract_list_claim(self, claim_value: Any) -> list[str]:
        """
        Extract list of strings from a claim value.

        Args:
            claim_value: Claim value that might be a list, string, or other type

        Returns:
            List of strings
        """
        if isinstance(claim_value, list):
            return [str(item) for item in claim_value if item is not None]
        elif isinstance(claim_value, str):
            # Handle comma-separated or space-separated values
            if "," in claim_value:
                return [item.strip() for item in claim_value.split(",") if item.strip()]
            elif " " in claim_value:
                return [item.strip() for item in claim_value.split() if item.strip()]
            else:
                return [claim_value]
        elif claim_value is not None:
            return [str(claim_value)]
        else:
            return []


def get_current_user(request: Request) -> UserContext:
    """
    Get current user context from request state.

    Args:
        request: FastAPI request object

    Returns:
        UserContext object (empty if no user authenticated)
    """
    return getattr(request.state, "user_context", UserContext())


def get_current_user_id(request: Request) -> str | None:
    """
    Get current user ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        User ID or None if not authenticated
    """
    return getattr(request.state, "user_id", None)


def require_authentication(request: Request) -> UserContext:
    """
    Get current user context and raise exception if not authenticated.

    Args:
        request: FastAPI request object

    Returns:
        UserContext object

    Raises:
        HTTPException: If user is not authenticated
    """
    from fastapi import HTTPException, status

    user_context = get_current_user(request)
    if not user_context.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_context


def require_role(request: Request, required_role: str) -> UserContext:
    """
    Get current user context and check for required role.

    Args:
        request: FastAPI request object
        required_role: Required role name

    Returns:
        UserContext object

    Raises:
        HTTPException: If user is not authenticated or doesn't have required role
    """
    from fastapi import HTTPException, status

    user_context = require_authentication(request)
    if not user_context.has_role(required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{required_role}' required",
        )
    return user_context


def require_permission(request: Request, required_permission: str) -> UserContext:
    """
    Get current user context and check for required permission.

    Args:
        request: FastAPI request object
        required_permission: Required permission name

    Returns:
        UserContext object

    Raises:
        HTTPException: If user is not authenticated or doesn't have required permission
    """
    from fastapi import HTTPException, status

    user_context = require_authentication(request)
    if not user_context.has_permission(required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{required_permission}' required",
        )
    return user_context

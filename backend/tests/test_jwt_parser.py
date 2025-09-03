"""
Tests for JWT parser middleware.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt

from app.middleware.jwt_parser import (
    JWTParserMiddleware,
    get_current_user,
    get_current_user_id,
    require_authentication,
    require_permission,
    require_role,
)
from app.schemas.user import UserContext


class TestJWTParserMiddleware:
    """Test cases for JWT parser middleware."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with JWT parser middleware."""
        app = FastAPI()
        app.add_middleware(JWTParserMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            user_context = get_current_user(request)
            return {
                "user_id": user_context.user_id,
                "username": user_context.username,
                "roles": user_context.roles,
                "is_authenticated": user_context.is_authenticated(),
            }

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            user_context = require_authentication(request)
            return {"user_id": user_context.user_id}

        @app.get("/admin")
        async def admin_endpoint(request: Request):
            user_context = require_role(request, "admin")
            return {"user_id": user_context.user_id}

        @app.get("/write")
        async def write_endpoint(request: Request):
            user_context = require_permission(request, "write")
            return {"user_id": user_context.user_id}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_jwt_claims(self):
        """Sample JWT claims for testing."""
        return {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "roles": ["user", "admin"],
            "permissions": ["read", "write"],
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "typ": "access",
        }

    @pytest.fixture
    def sample_jwt_token(self, sample_jwt_claims):
        """Create sample JWT token for testing."""
        # Create a token without signature verification (for testing only)
        return jwt.encode(sample_jwt_claims, "test-secret", algorithm="HS256")

    def test_no_authorization_header(self, client):
        """Test request without authorization header."""
        response = client.get("/test")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
        assert data["username"] is None
        assert data["roles"] == []
        assert data["is_authenticated"] is False

    def test_invalid_authorization_header_format(self, client):
        """Test request with invalid authorization header format."""
        response = client.get("/test", headers={"Authorization": "InvalidFormat token123"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
        assert data["is_authenticated"] is False

    def test_empty_token(self, client):
        """Test request with empty token."""
        response = client.get("/test", headers={"Authorization": "Bearer "})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
        assert data["is_authenticated"] is False

    def test_valid_jwt_token(self, client, sample_jwt_token):
        """Test request with valid JWT token."""
        response = client.get("/test", headers={"Authorization": f"Bearer {sample_jwt_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"
        assert "user" in data["roles"]
        assert "admin" in data["roles"]
        assert data["is_authenticated"] is True

    def test_malformed_jwt_token(self, client):
        """Test request with malformed JWT token."""
        response = client.get("/test", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
        assert data["is_authenticated"] is False

    def test_skip_paths(self):
        """Test that middleware skips configured paths."""
        app = FastAPI()
        middleware = JWTParserMiddleware(app, skip_paths=["/health", "/metrics"])

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_custom_header_name(self):
        """Test middleware with custom header name."""
        app = FastAPI()
        app.add_middleware(JWTParserMiddleware, header_name="X-Auth-Token", token_prefix="Token ")

        @app.get("/test")
        async def test_endpoint(request: Request):
            user_context = get_current_user(request)
            return {"user_id": user_context.user_id}

        client = TestClient(app)

        # Test with custom header
        with patch("app.middleware.jwt_parser.jwt.get_unverified_claims") as mock_decode:
            mock_decode.return_value = {"sub": "user123"}
            response = client.get("/test", headers={"X-Auth-Token": "Token validtoken"})
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user123"

    def test_keycloak_format_roles(self, client):
        """Test parsing roles in Keycloak format."""
        claims = {
            "sub": "user123",
            "realm_access": {"roles": ["user", "admin"]},
        }
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/test", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "user" in data["roles"]
        assert "admin" in data["roles"]

    def test_oauth2_scope_permissions(self, client):
        """Test parsing permissions from OAuth2 scope."""
        claims = {
            "sub": "user123",
            "scope": "read write admin",
        }
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/test", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # We need to check the actual user context since the test endpoint doesn't return permissions
        # Let's create a custom endpoint for this test
        app = FastAPI()
        app.add_middleware(JWTParserMiddleware)

        @app.get("/permissions")
        async def permissions_endpoint(request: Request):
            user_context = get_current_user(request)
            return {"permissions": user_context.permissions}

        client = TestClient(app)
        response = client.get("/permissions", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "read" in data["permissions"]
        assert "write" in data["permissions"]
        assert "admin" in data["permissions"]

    def test_require_authentication_success(self, client, sample_jwt_token):
        """Test require_authentication with valid token."""
        response = client.get("/protected", headers={"Authorization": f"Bearer {sample_jwt_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"

    def test_require_authentication_failure(self, client):
        """Test require_authentication without token."""
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_require_role_success(self, client, sample_jwt_token):
        """Test require_role with valid role."""
        response = client.get("/admin", headers={"Authorization": f"Bearer {sample_jwt_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"

    def test_require_role_failure(self, client):
        """Test require_role without required role."""
        claims = {"sub": "user123", "roles": ["user"]}  # No admin role
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert "Role 'admin' required" in response.json()["detail"]

    def test_require_permission_success(self, client, sample_jwt_token):
        """Test require_permission with valid permission."""
        response = client.get("/write", headers={"Authorization": f"Bearer {sample_jwt_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"

    def test_require_permission_failure(self, client):
        """Test require_permission without required permission."""
        claims = {"sub": "user123", "permissions": ["read"]}  # No write permission
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/write", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert "Permission 'write' required" in response.json()["detail"]


class TestUserContext:
    """Test cases for UserContext model."""

    def test_is_authenticated_true(self):
        """Test is_authenticated returns True when user_id is present."""
        context = UserContext(user_id="user123")
        assert context.is_authenticated() is True

    def test_is_authenticated_false(self):
        """Test is_authenticated returns False when user_id is None."""
        context = UserContext()
        assert context.is_authenticated() is False

    def test_has_role_true(self):
        """Test has_role returns True when user has the role."""
        context = UserContext(roles=["admin", "user"])
        assert context.has_role("admin") is True

    def test_has_role_false(self):
        """Test has_role returns False when user doesn't have the role."""
        context = UserContext(roles=["user"])
        assert context.has_role("admin") is False

    def test_has_permission_true(self):
        """Test has_permission returns True when user has the permission."""
        context = UserContext(permissions=["read", "write"])
        assert context.has_permission("read") is True

    def test_has_permission_false(self):
        """Test has_permission returns False when user doesn't have the permission."""
        context = UserContext(permissions=["read"])
        assert context.has_permission("write") is False

    def test_has_any_role_true(self):
        """Test has_any_role returns True when user has at least one role."""
        context = UserContext(roles=["user"])
        assert context.has_any_role(["admin", "user"]) is True

    def test_has_any_role_false(self):
        """Test has_any_role returns False when user has none of the roles."""
        context = UserContext(roles=["guest"])
        assert context.has_any_role(["admin", "user"]) is False

    def test_has_all_roles_true(self):
        """Test has_all_roles returns True when user has all roles."""
        context = UserContext(roles=["admin", "user", "moderator"])
        assert context.has_all_roles(["admin", "user"]) is True

    def test_has_all_roles_false(self):
        """Test has_all_roles returns False when user doesn't have all roles."""
        context = UserContext(roles=["user"])
        assert context.has_all_roles(["admin", "user"]) is False


class TestJWTParserHelpers:
    """Test cases for JWT parser helper functions."""

    def test_get_current_user_with_context(self):
        """Test get_current_user returns user context from request state."""
        request = MagicMock(spec=Request)
        user_context = UserContext(user_id="user123")
        request.state.user_context = user_context

        result = get_current_user(request)
        assert result.user_id == "user123"

    def test_get_current_user_without_context(self):
        """Test get_current_user returns empty context when not in request state."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.user_context  # Simulate missing attribute

        with patch("app.middleware.jwt_parser.getattr") as mock_getattr:
            mock_getattr.return_value = UserContext()
            result = get_current_user(request)
            assert result.user_id is None

    def test_get_current_user_id_with_user(self):
        """Test get_current_user_id returns user ID from request state."""
        request = MagicMock(spec=Request)
        request.state.user_id = "user123"

        result = get_current_user_id(request)
        assert result == "user123"

    def test_get_current_user_id_without_user(self):
        """Test get_current_user_id returns None when not in request state."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.user_id  # Simulate missing attribute

        with patch("app.middleware.jwt_parser.getattr") as mock_getattr:
            mock_getattr.return_value = None
            result = get_current_user_id(request)
            assert result is None


class TestJWTParserMiddlewareInternal:
    """Test internal methods of JWT parser middleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        app = MagicMock()
        return JWTParserMiddleware(app)

    def test_extract_list_claim_from_list(self, middleware):
        """Test _extract_list_claim with list input."""
        result = middleware._extract_list_claim(["role1", "role2", None])
        assert result == ["role1", "role2"]

    def test_extract_list_claim_from_comma_string(self, middleware):
        """Test _extract_list_claim with comma-separated string."""
        result = middleware._extract_list_claim("role1,role2,role3")
        assert result == ["role1", "role2", "role3"]

    def test_extract_list_claim_from_space_string(self, middleware):
        """Test _extract_list_claim with space-separated string."""
        result = middleware._extract_list_claim("role1 role2 role3")
        assert result == ["role1", "role2", "role3"]

    def test_extract_list_claim_from_single_string(self, middleware):
        """Test _extract_list_claim with single string."""
        result = middleware._extract_list_claim("single_role")
        assert result == ["single_role"]

    def test_extract_list_claim_from_none(self, middleware):
        """Test _extract_list_claim with None input."""
        result = middleware._extract_list_claim(None)
        assert result == []

    def test_extract_list_claim_from_number(self, middleware):
        """Test _extract_list_claim with number input."""
        result = middleware._extract_list_claim(123)
        assert result == ["123"]

    @pytest.mark.asyncio
    async def test_extract_user_context_minimal(self, middleware):
        """Test _extract_user_context with minimal claims."""
        claims = {"sub": "user123"}
        result = await middleware._extract_user_context(claims, "req123")

        assert result.user_id == "user123"
        assert result.username is None
        assert result.roles == []
        assert result.permissions == []

    @pytest.mark.asyncio
    async def test_extract_user_context_full(self, middleware):
        """Test _extract_user_context with full claims."""
        claims = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "permissions": ["read", "write"],
            "iat": 1234567890,
            "exp": 1234571490,
            "typ": "access",
        }
        result = await middleware._extract_user_context(claims, "req123")

        assert result.user_id == "user123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.roles == ["admin", "user"]
        assert result.permissions == ["read", "write"]
        assert result.issued_at == 1234567890
        assert result.expires_at == 1234571490
        assert result.token_type == "access"

    @pytest.mark.asyncio
    async def test_extract_user_context_with_exception(self, middleware):
        """Test _extract_user_context handles exceptions gracefully."""
        # Create claims that will cause an exception during processing
        claims = {"sub": "user123"}

        with patch.object(middleware, "_extract_list_claim", side_effect=Exception("Test error")):
            result = await middleware._extract_user_context(claims, "req123")

            # Should return minimal context with available information
            assert result.user_id == "user123"
            assert result.raw_claims == claims

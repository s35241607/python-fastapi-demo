"""
Integration tests for JWT parser middleware with other components.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt

from app.middleware import JWTParserMiddleware
from app.schemas import UserContext


class TestJWTIntegration:
    """Integration tests for JWT parser middleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with JWT parser middleware."""
        app = FastAPI()

        # Add JWT parser middleware
        app.add_middleware(JWTParserMiddleware)

        @app.get("/user-info")
        async def get_user_info(request: Request):
            """Endpoint to test user context extraction."""
            from app.middleware.jwt_parser import get_current_user

            user_context = get_current_user(request)
            return {
                "authenticated": user_context.is_authenticated(),
                "user_id": user_context.user_id,
                "username": user_context.username,
                "roles": user_context.roles,
                "permissions": user_context.permissions,
            }

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            """Protected endpoint requiring authentication."""
            from app.middleware.jwt_parser import require_authentication

            user_context = require_authentication(request)
            return {"message": f"Hello, {user_context.username or user_context.user_id}!"}

        @app.get("/admin-only")
        async def admin_endpoint(request: Request):
            """Admin-only endpoint."""
            from app.middleware.jwt_parser import require_role

            user_context = require_role(request, "admin")
            return {"message": "Admin access granted"}

        return app

    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)

    def test_middleware_import(self):
        """Test that middleware can be imported correctly."""
        from app.middleware import JWTParserMiddleware
        from app.schemas import JWTParseResult, UserContext

        assert JWTParserMiddleware is not None
        assert UserContext is not None
        assert JWTParseResult is not None

    def test_unauthenticated_request(self, client):
        """Test request without JWT token."""
        response = client.get("/user-info")
        assert response.status_code == 200

        data = response.json()
        assert data["authenticated"] is False
        assert data["user_id"] is None
        assert data["username"] is None
        assert data["roles"] == []
        assert data["permissions"] == []

    def test_authenticated_request(self, client):
        """Test request with valid JWT token."""
        # Create a test JWT token
        claims = {
            "sub": "user123",
            "preferred_username": "testuser",
            "roles": ["user", "admin"],
            "permissions": ["read", "write"],
        }
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"
        assert "user" in data["roles"]
        assert "admin" in data["roles"]
        assert "read" in data["permissions"]
        assert "write" in data["permissions"]

    def test_protected_endpoint_success(self, client):
        """Test protected endpoint with valid token."""
        claims = {"sub": "user123", "preferred_username": "testuser"}
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "Hello, testuser!" in response.json()["message"]

    def test_protected_endpoint_failure(self, client):
        """Test protected endpoint without token."""
        response = client.get("/protected")
        assert response.status_code == 401

    def test_admin_endpoint_success(self, client):
        """Test admin endpoint with admin role."""
        claims = {"sub": "admin123", "roles": ["admin", "user"]}
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "Admin access granted" in response.json()["message"]

    def test_admin_endpoint_failure(self, client):
        """Test admin endpoint without admin role."""
        claims = {"sub": "user123", "roles": ["user"]}
        token = jwt.encode(claims, "test-secret", algorithm="HS256")

        response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_user_context_methods(self):
        """Test UserContext helper methods."""
        context = UserContext(
            user_id="user123",
            username="testuser",
            roles=["admin", "user"],
            permissions=["read", "write", "delete"],
        )

        # Test authentication
        assert context.is_authenticated() is True

        # Test role checking
        assert context.has_role("admin") is True
        assert context.has_role("moderator") is False
        assert context.has_any_role(["admin", "moderator"]) is True
        assert context.has_all_roles(["admin", "user"]) is True
        assert context.has_all_roles(["admin", "moderator"]) is False

        # Test permission checking
        assert context.has_permission("read") is True
        assert context.has_permission("execute") is False

    def test_middleware_with_different_jwt_formats(self, client):
        """Test middleware with different JWT claim formats."""
        # Test Keycloak format
        keycloak_claims = {
            "sub": "user123",
            "realm_access": {"roles": ["admin", "user"]},
        }
        token = jwt.encode(keycloak_claims, "test-secret", algorithm="HS256")

        response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "admin" in data["roles"]
        assert "user" in data["roles"]

        # Test OAuth2 scope format
        oauth2_claims = {
            "sub": "user456",
            "scope": "read write admin",
        }
        token = jwt.encode(oauth2_claims, "test-secret", algorithm="HS256")

        response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "read" in data["permissions"]
        assert "write" in data["permissions"]
        assert "admin" in data["permissions"]

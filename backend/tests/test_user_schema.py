"""
Tests for user schema models.
"""

from app.schemas.user import JWTParseResult, UserContext


class TestUserContext:
    """Test cases for UserContext model."""

    def test_user_context_creation_minimal(self):
        """Test creating UserContext with minimal data."""
        context = UserContext()

        assert context.user_id is None
        assert context.username is None
        assert context.email is None
        assert context.roles == []
        assert context.permissions == []
        assert context.token_type is None
        assert context.issued_at is None
        assert context.expires_at is None
        assert context.raw_claims is None

    def test_user_context_creation_full(self):
        """Test creating UserContext with full data."""
        raw_claims = {"sub": "user123", "custom": "value"}
        context = UserContext(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["admin", "user"],
            permissions=["read", "write", "delete"],
            token_type="access",
            issued_at=1234567890,
            expires_at=1234571490,
            raw_claims=raw_claims,
        )

        assert context.user_id == "user123"
        assert context.username == "testuser"
        assert context.email == "test@example.com"
        assert context.roles == ["admin", "user"]
        assert context.permissions == ["read", "write", "delete"]
        assert context.token_type == "access"
        assert context.issued_at == 1234567890
        assert context.expires_at == 1234571490
        assert context.raw_claims == raw_claims

    def test_is_authenticated_with_user_id(self):
        """Test is_authenticated returns True when user_id is present."""
        context = UserContext(user_id="user123")
        assert context.is_authenticated() is True

    def test_is_authenticated_without_user_id(self):
        """Test is_authenticated returns False when user_id is None."""
        context = UserContext()
        assert context.is_authenticated() is False

    def test_is_authenticated_with_empty_user_id(self):
        """Test is_authenticated returns False when user_id is empty string."""
        context = UserContext(user_id="")
        assert context.is_authenticated() is False

    def test_has_role_existing(self):
        """Test has_role returns True for existing role."""
        context = UserContext(roles=["admin", "user", "moderator"])
        assert context.has_role("admin") is True
        assert context.has_role("user") is True
        assert context.has_role("moderator") is True

    def test_has_role_non_existing(self):
        """Test has_role returns False for non-existing role."""
        context = UserContext(roles=["user"])
        assert context.has_role("admin") is False
        assert context.has_role("moderator") is False

    def test_has_role_empty_roles(self):
        """Test has_role returns False when roles list is empty."""
        context = UserContext(roles=[])
        assert context.has_role("admin") is False

    def test_has_role_case_sensitive(self):
        """Test has_role is case sensitive."""
        context = UserContext(roles=["Admin"])
        assert context.has_role("admin") is False
        assert context.has_role("Admin") is True

    def test_has_permission_existing(self):
        """Test has_permission returns True for existing permission."""
        context = UserContext(permissions=["read", "write", "delete"])
        assert context.has_permission("read") is True
        assert context.has_permission("write") is True
        assert context.has_permission("delete") is True

    def test_has_permission_non_existing(self):
        """Test has_permission returns False for non-existing permission."""
        context = UserContext(permissions=["read"])
        assert context.has_permission("write") is False
        assert context.has_permission("delete") is False

    def test_has_permission_empty_permissions(self):
        """Test has_permission returns False when permissions list is empty."""
        context = UserContext(permissions=[])
        assert context.has_permission("read") is False

    def test_has_permission_case_sensitive(self):
        """Test has_permission is case sensitive."""
        context = UserContext(permissions=["Read"])
        assert context.has_permission("read") is False
        assert context.has_permission("Read") is True

    def test_has_any_role_with_match(self):
        """Test has_any_role returns True when user has at least one role."""
        context = UserContext(roles=["user", "guest"])
        assert context.has_any_role(["admin", "user"]) is True
        assert context.has_any_role(["guest", "moderator"]) is True

    def test_has_any_role_without_match(self):
        """Test has_any_role returns False when user has none of the roles."""
        context = UserContext(roles=["guest"])
        assert context.has_any_role(["admin", "user"]) is False
        assert context.has_any_role(["moderator", "editor"]) is False

    def test_has_any_role_empty_user_roles(self):
        """Test has_any_role returns False when user has no roles."""
        context = UserContext(roles=[])
        assert context.has_any_role(["admin", "user"]) is False

    def test_has_any_role_empty_required_roles(self):
        """Test has_any_role returns False when required roles list is empty."""
        context = UserContext(roles=["admin", "user"])
        assert context.has_any_role([]) is False

    def test_has_all_roles_with_all_roles(self):
        """Test has_all_roles returns True when user has all required roles."""
        context = UserContext(roles=["admin", "user", "moderator"])
        assert context.has_all_roles(["admin", "user"]) is True
        assert context.has_all_roles(["user"]) is True
        assert context.has_all_roles(["admin", "user", "moderator"]) is True

    def test_has_all_roles_without_all_roles(self):
        """Test has_all_roles returns False when user doesn't have all required roles."""
        context = UserContext(roles=["user"])
        assert context.has_all_roles(["admin", "user"]) is False
        assert context.has_all_roles(["admin", "moderator"]) is False

    def test_has_all_roles_empty_user_roles(self):
        """Test has_all_roles returns False when user has no roles."""
        context = UserContext(roles=[])
        assert context.has_all_roles(["admin"]) is False

    def test_has_all_roles_empty_required_roles(self):
        """Test has_all_roles returns True when required roles list is empty."""
        context = UserContext(roles=["admin", "user"])
        assert context.has_all_roles([]) is True

    def test_user_context_serialization(self):
        """Test UserContext can be serialized to dict."""
        context = UserContext(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["admin"],
            permissions=["read"],
        )

        data = context.model_dump()
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["roles"] == ["admin"]
        assert data["permissions"] == ["read"]

    def test_user_context_from_dict(self):
        """Test UserContext can be created from dict."""
        data = {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["admin"],
            "permissions": ["read"],
        }

        context = UserContext(**data)
        assert context.user_id == "user123"
        assert context.username == "testuser"
        assert context.email == "test@example.com"
        assert context.roles == ["admin"]
        assert context.permissions == ["read"]


class TestJWTParseResult:
    """Test cases for JWTParseResult model."""

    def test_jwt_parse_result_success(self):
        """Test creating successful JWTParseResult."""
        user_context = UserContext(user_id="user123")
        result = JWTParseResult(
            success=True,
            user_context=user_context,
        )

        assert result.success is True
        assert result.user_context == user_context
        assert result.error is None
        assert result.error_type is None

    def test_jwt_parse_result_failure(self):
        """Test creating failed JWTParseResult."""
        result = JWTParseResult(
            success=False,
            error="Invalid token format",
            error_type="INVALID_FORMAT",
        )

        assert result.success is False
        assert result.user_context is None
        assert result.error == "Invalid token format"
        assert result.error_type == "INVALID_FORMAT"

    def test_jwt_parse_result_minimal(self):
        """Test creating JWTParseResult with minimal data."""
        result = JWTParseResult(success=True)

        assert result.success is True
        assert result.user_context is None
        assert result.error is None
        assert result.error_type is None

    def test_jwt_parse_result_serialization(self):
        """Test JWTParseResult can be serialized to dict."""
        user_context = UserContext(user_id="user123")
        result = JWTParseResult(
            success=True,
            user_context=user_context,
        )

        data = result.model_dump()
        assert data["success"] is True
        assert data["user_context"]["user_id"] == "user123"
        assert data["error"] is None
        assert data["error_type"] is None

    def test_jwt_parse_result_from_dict(self):
        """Test JWTParseResult can be created from dict."""
        data = {
            "success": False,
            "error": "Token expired",
            "error_type": "EXPIRED_TOKEN",
        }

        result = JWTParseResult(**data)
        assert result.success is False
        assert result.user_context is None
        assert result.error == "Token expired"
        assert result.error_type == "EXPIRED_TOKEN"


class TestUserContextEdgeCases:
    """Test edge cases for UserContext model."""

    def test_user_context_with_none_values(self):
        """Test UserContext handles None values correctly."""
        context = UserContext(
            user_id=None,
            username=None,
            email=None,
            # Don't pass None for roles and permissions as they have default_factory
        )

        # Default values should be applied
        assert context.user_id is None
        assert context.username is None
        assert context.email is None
        assert context.roles == []  # Should default to empty list
        assert context.permissions == []  # Should default to empty list

    def test_user_context_with_duplicate_roles(self):
        """Test UserContext with duplicate roles."""
        context = UserContext(roles=["admin", "user", "admin", "user"])

        # Should preserve duplicates (no deduplication)
        assert context.roles == ["admin", "user", "admin", "user"]
        assert context.has_role("admin") is True
        assert context.has_role("user") is True

    def test_user_context_with_duplicate_permissions(self):
        """Test UserContext with duplicate permissions."""
        context = UserContext(permissions=["read", "write", "read", "write"])

        # Should preserve duplicates (no deduplication)
        assert context.permissions == ["read", "write", "read", "write"]
        assert context.has_permission("read") is True
        assert context.has_permission("write") is True

    def test_user_context_with_special_characters(self):
        """Test UserContext with special characters in fields."""
        context = UserContext(
            user_id="user@123#$%",
            username="test.user+special",
            email="test+user@example.com",
            roles=["admin-role", "user_role", "role:special"],
            permissions=["read:all", "write-data", "delete_item"],
        )

        assert context.user_id == "user@123#$%"
        assert context.username == "test.user+special"
        assert context.email == "test+user@example.com"
        assert context.has_role("admin-role") is True
        assert context.has_role("user_role") is True
        assert context.has_role("role:special") is True
        assert context.has_permission("read:all") is True
        assert context.has_permission("write-data") is True
        assert context.has_permission("delete_item") is True

    def test_user_context_with_unicode_characters(self):
        """Test UserContext with Unicode characters."""
        context = UserContext(
            user_id="用戶123",
            username="測試用戶",
            email="測試@example.com",
            roles=["管理員", "用戶"],
            permissions=["讀取", "寫入"],
        )

        assert context.user_id == "用戶123"
        assert context.username == "測試用戶"
        assert context.email == "測試@example.com"
        assert context.has_role("管理員") is True
        assert context.has_role("用戶") is True
        assert context.has_permission("讀取") is True
        assert context.has_permission("寫入") is True

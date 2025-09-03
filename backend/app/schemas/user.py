"""
User context schemas for JWT parsing and user information.
"""

from typing import Any

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User context model for storing parsed JWT information."""

    user_id: str | None = Field(default=None, description="User ID from JWT token")
    username: str | None = Field(default=None, description="Username from JWT token")
    email: str | None = Field(default=None, description="Email from JWT token")
    roles: list[str] = Field(default_factory=list, description="User roles from JWT token")
    permissions: list[str] = Field(default_factory=list, description="User permissions from JWT token")
    token_type: str | None = Field(default=None, description="Type of JWT token (e.g., 'access', 'refresh')")
    issued_at: int | None = Field(default=None, description="Token issued at timestamp")
    expires_at: int | None = Field(default=None, description="Token expiration timestamp")
    raw_claims: dict[str, Any] | None = Field(default=None, description="Raw JWT claims for additional data")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has valid user_id)."""
        return self.user_id is not None and self.user_id != ""

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.roles for role in roles)


class JWTParseResult(BaseModel):
    """Result of JWT parsing operation."""

    success: bool = Field(..., description="Whether JWT parsing was successful")
    user_context: UserContext | None = Field(default=None, description="Parsed user context if successful")
    error: str | None = Field(default=None, description="Error message if parsing failed")
    error_type: str | None = Field(default=None, description="Type of error that occurred")

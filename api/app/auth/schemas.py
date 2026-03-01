"""Pydantic request/response schemas for authentication."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# --- Request schemas ---


class RegisterRequest(BaseModel):
    """Account registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class CreateAPIKeyRequest(BaseModel):
    """API key creation request."""

    name: str = Field(min_length=1, max_length=255)
    is_test: bool = False


class OAuthCallbackRequest(BaseModel):
    """OAuth callback with authorization code."""

    code: str
    state: str | None = None


# --- Response schemas ---


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    display_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyResponse(BaseModel):
    """API key creation response (includes the raw key only once)."""

    id: str
    name: str
    key_prefix: str
    raw_key: str
    is_test: bool
    created_at: datetime


class APIKeyListItem(BaseModel):
    """API key listing (no raw key)."""

    id: str
    name: str
    key_prefix: str
    is_test: bool
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class OAuthRedirectResponse(BaseModel):
    """OAuth authorization URL redirect."""

    authorization_url: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str

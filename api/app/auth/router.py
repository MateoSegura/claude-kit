"""Auth endpoints for registration, login, OAuth, and API keys."""

import hashlib
import secrets

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_keys import generate_api_key
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.auth.models import APIKey, OAuthConnection, RefreshToken, User
from app.auth.providers.base import AuthProvider
from app.auth.providers.github import GitHubProvider
from app.auth.providers.google import GoogleProvider
from app.auth.schemas import (
    APIKeyResponse,
    CreateAPIKeyRequest,
    LoginRequest,
    MessageResponse,
    OAuthCallbackRequest,
    OAuthRedirectResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.dependencies import get_current_user, get_db

router = APIRouter()

OAUTH_PROVIDERS: dict[str, AuthProvider] = {
    "github": GitHubProvider(),
    "google": GoogleProvider(),
}


def _hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _issue_tokens(user_id: str, db: AsyncSession) -> TokenResponse:
    """Create access + refresh tokens and persist the refresh token."""
    access_token, expires_in = create_access_token(user_id)
    refresh_token_str, refresh_expires = create_refresh_token(user_id)

    db_refresh = RefreshToken(
        user_id=user_id,
        token_hash=_hash_refresh_token(refresh_token_str),
        expires_at=refresh_expires,
    )
    db.add(db_refresh)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=expires_in,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account with email and password."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=bcrypt.hashpw(
            body.password.encode(), bcrypt.gensalt()
        ).decode(),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()

    return await _issue_tokens(user.id, db)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password, return JWT tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not bcrypt.checkpw(body.password.encode(), user.hashed_password.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return await _issue_tokens(user.id, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an expired access token using a valid refresh token."""
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_hash = _hash_refresh_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    stored_token.is_revoked = True
    await db.flush()

    user_id = payload["sub"]
    return await _issue_tokens(user_id, db)


@router.get("/oauth/{provider}/authorize", response_model=OAuthRedirectResponse)
async def oauth_authorize(provider: str):
    """Get the OAuth authorization redirect URL for a provider."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    oauth_provider = OAUTH_PROVIDERS[provider]
    state = secrets.token_urlsafe(32)
    redirect_uri = f"/api/v1/auth/oauth/{provider}/callback"
    url = oauth_provider.get_authorization_url(redirect_uri, state)

    return OAuthRedirectResponse(authorization_url=url)


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback, create or link account, return tokens."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    oauth_provider = OAUTH_PROVIDERS[provider]
    redirect_uri = f"/api/v1/auth/oauth/{provider}/callback"
    user_info = await oauth_provider.exchange_code(body.code, redirect_uri)

    result = await db.execute(
        select(OAuthConnection).where(
            OAuthConnection.provider == provider,
            OAuthConnection.provider_user_id == user_info.provider_user_id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is not None:
        return await _issue_tokens(connection.user_id, db)

    user_result = await db.execute(select(User).where(User.email == user_info.email))
    user = user_result.scalar_one_or_none()

    if user is None:
        user = User(
            email=user_info.email,
            display_name=user_info.display_name,
        )
        db.add(user)
        await db.flush()

    new_connection = OAuthConnection(
        user_id=user.id,
        provider=provider,
        provider_user_id=user_info.provider_user_id,
        provider_email=user_info.email,
    )
    db.add(new_connection)
    await db.flush()

    return await _issue_tokens(user.id, db)


@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    body: CreateAPIKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new API key for the authenticated user."""
    raw_key, prefix_display, key_hash = generate_api_key(is_test=body.is_test)

    api_key = APIKey(
        user_id=user.id,
        name=body.name,
        key_prefix=prefix_display,
        key_hash=key_hash,
        is_test=body.is_test,
    )
    db.add(api_key)
    await db.flush()

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_key=raw_key,
        is_test=api_key.is_test,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key owned by the authenticated user."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    await db.flush()

    return MessageResponse(message="API key revoked")


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return user

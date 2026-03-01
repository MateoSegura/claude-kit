"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_keys import verify_api_key
from app.auth.jwt import decode_access_token
from app.auth.models import APIKey, User
from app.models.base import async_session_factory

bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT bearer token."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme_optional),
    x_api_key: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via JWT bearer token OR X-API-Key header.

    The ingest endpoint accepts both auth methods so that the CLI can use
    an API key while the dashboard uses JWT.
    """
    # Try JWT first
    if credentials is not None:
        payload = decode_access_token(credentials.credentials)
        if payload is not None:
            user_id = payload.get("sub")
            if user_id:
                user = await db.get(User, user_id)
                if user is not None:
                    return user

    # Try API key
    if x_api_key is not None:
        result = await db.execute(
            select(APIKey).where(
                APIKey.is_active.is_(True),
                APIKey.key_prefix == x_api_key[:16],
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is not None and verify_api_key(x_api_key, api_key.key_hash):
            user = await db.get(User, api_key.user_id)
            if user is not None:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid JWT bearer token or X-API-Key header required",
    )

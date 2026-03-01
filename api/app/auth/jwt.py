"""JWT token creation and validation using HS256."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings


def create_access_token(user_id: str) -> tuple[str, int]:
    """Create a short-lived access token.

    Returns a tuple of (token_string, expires_in_seconds).
    """
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a long-lived refresh token.

    Returns a tuple of (token_string, expiration_datetime).
    """
    settings = get_settings()
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def decode_access_token(token: str) -> dict | None:
    """Decode and validate an access token. Returns payload or None."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    """Decode and validate a refresh token. Returns payload or None."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

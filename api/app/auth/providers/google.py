"""Google OAuth provider implementation."""

from urllib.parse import urlencode

import httpx

from app.auth.providers.base import AuthProvider, OAuthUserInfo
from app.config import get_settings

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleProvider(AuthProvider):
    """Google OAuth 2.0 provider."""

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Build Google authorization URL."""
        settings = get_settings()
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange Google authorization code for user info."""
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            user_resp = await client.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()

            return OAuthUserInfo(
                provider="google",
                provider_user_id=user_data["id"],
                email=user_data.get("email", ""),
                display_name=user_data.get("name"),
            )

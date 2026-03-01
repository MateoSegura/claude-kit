"""GitHub OAuth provider implementation."""

from urllib.parse import urlencode

import httpx

from app.auth.providers.base import AuthProvider, OAuthUserInfo
from app.config import get_settings

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"
EMAILS_URL = "https://api.github.com/user/emails"


class GitHubProvider(AuthProvider):
    """GitHub OAuth 2.0 provider."""

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Build GitHub authorization URL."""
        settings = get_settings()
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange GitHub authorization code for user info."""
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                TOKEN_URL,
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            user_resp = await client.get(USER_URL, headers=headers)
            user_resp.raise_for_status()
            user_data = user_resp.json()

            email = user_data.get("email")
            if not email:
                emails_resp = await client.get(EMAILS_URL, headers=headers)
                emails_resp.raise_for_status()
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break

            return OAuthUserInfo(
                provider="github",
                provider_user_id=str(user_data["id"]),
                email=email or "",
                display_name=user_data.get("name") or user_data.get("login"),
            )

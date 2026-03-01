"""Abstract base class for OAuth providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """Normalized user info returned from an OAuth provider."""

    provider: str
    provider_user_id: str
    email: str
    display_name: str | None = None


class AuthProvider(ABC):
    """Interface for OAuth authentication providers."""

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Return the URL to redirect the user to for authorization."""
        ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange an authorization code for user info."""
        ...

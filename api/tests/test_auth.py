"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a test user and return the response data."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "display_name": "Test User",
        },
    )
    assert resp.status_code == 201
    return resp.json()


class TestHealthChecks:
    """Health endpoint tests."""

    async def test_liveness(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestRegistration:
    """Registration endpoint tests."""

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "securepassword123",
                "display_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "password": "securepassword123",
        }
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "securepassword123"},
        )
        assert resp.status_code == 422


class TestLogin:
    """Login endpoint tests."""

    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "securepassword123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(
        self, client: AsyncClient, registered_user: dict
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "securepassword123"},
        )
        assert resp.status_code == 401


class TestTokenRefresh:
    """Token refresh endpoint tests."""

    async def test_refresh_success(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_reuse_revoked(
        self, client: AsyncClient, registered_user: dict
    ):
        old_refresh = registered_user["refresh_token"]

        resp1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp1.status_code == 200

        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp2.status_code == 401

    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert resp.status_code == 401


class TestMe:
    """Current user profile endpoint tests."""

    async def test_me_authenticated(self, client: AsyncClient, registered_user: dict):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert data["is_active"] is True

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403


class TestAPIKeys:
    """API key management endpoint tests."""

    async def test_create_api_key(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/api-keys",
            json={"name": "My CLI Key", "is_test": False},
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My CLI Key"
        assert data["raw_key"].startswith("ck_live_")
        assert "key_prefix" in data
        assert data["is_test"] is False

    async def test_create_test_api_key(
        self, client: AsyncClient, registered_user: dict
    ):
        resp = await client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Test Key", "is_test": True},
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["raw_key"].startswith("ck_test_")
        assert data["is_test"] is True

    async def test_revoke_api_key(self, client: AsyncClient, registered_user: dict):
        create_resp = await client.post(
            "/api/v1/auth/api-keys",
            json={"name": "To Revoke"},
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        key_id = create_resp.json()["id"]

        revoke_resp = await client.delete(
            f"/api/v1/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["message"] == "API key revoked"

    async def test_revoke_nonexistent_key(
        self, client: AsyncClient, registered_user: dict
    ):
        resp = await client.delete(
            "/api/v1/auth/api-keys/nonexistent-id",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        )
        assert resp.status_code == 404

    async def test_create_api_key_unauthenticated(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Unauthorized Key"},
        )
        assert resp.status_code == 403


class TestOAuth:
    """OAuth endpoint tests."""

    async def test_oauth_authorize_github(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/oauth/github/authorize")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "github.com" in data["authorization_url"]

    async def test_oauth_authorize_google(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/oauth/google/authorize")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]

    async def test_oauth_unsupported_provider(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/oauth/unsupported/authorize")
        assert resp.status_code == 400

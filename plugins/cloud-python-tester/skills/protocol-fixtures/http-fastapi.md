# HTTP/FastAPI Test Fixtures

## AsyncClient with ASGITransport

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app

@pytest.fixture
async def app():
    """Create test application instance."""
    application = create_app()
    yield application

@pytest.fixture
async def client(app):
    """Async HTTP client bound to the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

## Dependency Overrides

```python
from app.dependencies import get_db_session, get_current_user

@pytest.fixture
def override_deps(app, mock_session, test_user):
    """Override FastAPI dependencies for testing."""
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    app.dependency_overrides.clear()
```

## Testing Endpoints

```python
@pytest.mark.asyncio
async def test_create_resource(client, override_deps):
    response = await client.post("/api/v1/resources", json={
        "name": "test-resource",
        "config": {"key": "value"},
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-resource"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_resource_validation_error(client, override_deps):
    response = await client.post("/api/v1/resources", json={})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "name"] for e in errors)
```

## WebSocket Testing

```python
@pytest.mark.asyncio
async def test_websocket_stream(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream("GET", "/ws/events") as response:
            lines = []
            async for line in response.aiter_lines():
                lines.append(line)
                if len(lines) >= 3:
                    break
            assert len(lines) == 3
```

## Authentication Fixtures

```python
@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for testing."""
    from app.auth import create_access_token
    token = create_access_token(data={"sub": "test-user", "scopes": ["read", "write"]})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_protected_endpoint(client, auth_headers, override_deps):
    response = await client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_endpoint_unauthorized(client):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
```

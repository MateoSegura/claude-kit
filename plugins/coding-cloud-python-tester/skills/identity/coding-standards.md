# Test Coding Standards

Complete style guide for test code in the coding-cloud-python-tester plugin. All test code must follow these conventions for consistency across unit, integration, and contract test files.

## File Naming and Placement

### Naming Conventions

| Source File | Test File | Location |
|-------------|-----------|----------|
| `src/services/order.py` | `test_order.py` | `tests/services/test_order.py` |
| `src/repositories/user_repo.py` | `test_user_repo.py` | `tests/repositories/test_user_repo.py` |
| `src/routes/health.py` | `test_health_contract.py` | `tests/contract/test_health_contract.py` |
| `src/models/user.py` | `test_user_model.py` | `tests/models/test_user_model.py` |
| `src/clients/payment.py` | `test_payment_client.py` | `tests/clients/test_payment_client.py` |

### Directory Layout

```
tests/
├── conftest.py              # Root fixtures: event loop, base settings, shared factories
├── unit/
│   ├── conftest.py          # Unit-specific fixtures: fakes, stubs
│   ├── services/
│   │   └── test_order.py
│   └── models/
│       └── test_user_model.py
├── integration/
│   ├── conftest.py          # Integration fixtures: testcontainers, DB sessions
│   ├── repositories/
│   │   └── test_user_repo.py
│   └── workers/
│       └── test_event_consumer.py
├── contract/
│   ├── conftest.py          # Contract fixtures: httpx.AsyncClient, app overrides
│   ├── test_users_api.py
│   └── test_health_api.py
└── factories/
    ├── __init__.py
    ├── user_factory.py       # Typed factory functions for test data
    └── order_factory.py
```

### Placement Rules

- Test files mirror the source layout under the appropriate marker directory (`unit/`, `integration/`, `contract/`).
- `conftest.py` files exist at each directory level. Fixtures cascade: root -> marker-level -> subdirectory-level.
- Factory functions live in `tests/factories/` and are imported by test files. Never inline complex object construction.
- All test files use the `test_` prefix. Never `spec_` or bare module names.

## Test Function Naming

### Pattern

```
test_<module_or_class>_<behavior>_<expected_outcome>
```

### Examples

```python
# Unit tests
def test_calculate_discount_with_valid_coupon_returns_reduced_price(): ...
def test_calculate_discount_with_expired_coupon_raises_value_error(): ...
def test_validate_email_with_empty_string_returns_false(): ...

# Integration tests
async def test_user_repo_create_with_duplicate_email_raises_integrity_error(): ...
async def test_user_repo_get_by_id_with_nonexistent_id_returns_none(): ...

# Contract tests
async def test_create_user_endpoint_with_valid_payload_returns_201(): ...
async def test_create_user_endpoint_with_missing_email_returns_422(): ...
async def test_get_user_endpoint_without_auth_returns_401(): ...
```

### Rules

- Use `snake_case` for all test function names.
- Start with `test_` (pytest collection requirement).
- Include the module or class name being tested.
- Describe the scenario and expected outcome.
- Never use generic names like `test_it_works` or `test_basic`.

## Fixture Conventions

### Type Annotations

Every fixture MUST be fully annotated:

```python
from collections.abc import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite+aiosqlite:///test.db")

@pytest.fixture
async def db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()
```

### Fixture Scope

| Scope | Use For | Example |
|-------|---------|---------|
| `function` (default) | Per-test isolation. Most fixtures. | DB session, HTTP client |
| `module` | Expensive setup shared across a file. | Testcontainer startup |
| `session` | One-time setup for the entire test run. | Docker network, compiled app |

- Default to `function` scope. Only widen scope when startup cost is prohibitive (container boot > 5s).
- Session-scoped fixtures MUST NOT mutate shared state. If they do, use `function` scope instead.

### conftest.py Hierarchy

```python
# tests/conftest.py -- root level
import pytest

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/testdb",
        redis_url="redis://localhost:6379/1",
    )
```

```python
# tests/integration/conftest.py -- integration fixtures
import pytest
from testcontainers.postgres import PostgresContainer
from collections.abc import Generator

@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg
```

```python
# tests/contract/conftest.py -- contract fixtures
import pytest
import httpx
from collections.abc import AsyncGenerator

@pytest.fixture
async def async_client(
    app: FastAPI,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()
```

## Assertion Patterns

### Preferred Patterns

```python
# Status code + body in contract tests
response = await async_client.post("/users", json=payload)
assert response.status_code == 201
data = response.json()
assert data["email"] == "user@example.com"
assert "id" in data

# Exception testing
with pytest.raises(ValueError, match="email is required"):
    validate_user(UserCreate(email="", name="test"))

# Async exception testing
with pytest.raises(httpx.HTTPStatusError):
    await client.get("/nonexistent")

# Approximate numeric comparison
assert result.latency == pytest.approx(0.5, abs=0.1)
```

### Anti-Patterns

```python
# BAD: bare assert with no message context
assert result

# GOOD: specific assertion with clear failure output
assert result.status == "active", f"Expected active, got {result.status}"

# BAD: catching exceptions manually
try:
    do_thing()
    assert False, "Should have raised"
except ValueError:
    pass

# GOOD: pytest.raises
with pytest.raises(ValueError, match="invalid input"):
    do_thing()

# BAD: asserting on dict equality for partial checks
assert response.json() == {"id": 1, "name": "test", "email": "t@t.com", ...}

# GOOD: check only the fields you care about
data = response.json()
assert data["name"] == "test"
assert data["email"] == "t@t.com"
```

## Mock Conventions

### When to Mock

- External HTTP calls: use `httpx.MockTransport` or `respx`.
- Third-party SDKs (Stripe, AWS, etc.): mock at the client boundary.
- Time-dependent logic: use `freezegun` or `time_machine`.
- Randomness: seed or mock `random`/`uuid`.

### When NOT to Mock

- Database queries in integration tests: use testcontainers.
- Pydantic model validation: test with real models.
- The module under test: never mock what you are testing.
- Internal private functions: mock at the public boundary instead.

### Mock Patterns

```python
# Dependency override in FastAPI contract tests
from unittest.mock import AsyncMock

async def mock_user_service() -> UserService:
    service = AsyncMock(spec=UserService)
    service.get_by_id.return_value = User(id=1, name="Test")
    return service

@pytest.fixture
def override_deps(app: FastAPI) -> None:
    app.dependency_overrides[get_user_service] = mock_user_service

# httpx.MockTransport for isolated HTTP client tests
def mock_transport(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/payment":
        return httpx.Response(200, json={"status": "ok"})
    return httpx.Response(404)

client = httpx.AsyncClient(transport=httpx.MockTransport(mock_transport))
```

## Marker Registration

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Pure logic tests with no external dependencies",
    "integration: Tests requiring real infrastructure (Docker/testcontainers)",
    "contract: API boundary tests using httpx.AsyncClient against the app",
]
asyncio_mode = "auto"
```

## Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_also = [
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "@overload",
    "raise NotImplementedError",
    "pass",
]
```

## Ruff Configuration for Test Files

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",     # Allow assert statements in tests
    "PLR2004",  # Allow magic values in tests
    "ARG001",   # Allow unused function arguments (fixtures)
]
```

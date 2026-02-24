# pytest Testing — Complete Reference

Detailed configuration options, pytest-asyncio internals, marker system, parametrize patterns, and plugin configuration.

## pyproject.toml — All Options

```toml
[tool.pytest.ini_options]
# ── Discovery ─────────────────────────────────────────────────────────────────
testpaths = ["tests"]                     # directories to search for tests
python_files = ["test_*.py", "*_test.py"] # filename patterns
python_classes = ["Test*"]                # class name patterns
python_functions = ["test_*"]             # function name patterns

# ── Behavior ──────────────────────────────────────────────────────────────────
addopts = [
    "--strict-markers",                   # fail on unregistered markers (required)
    "-v",                                 # verbose by default
    "--tb=short",                         # shorter tracebacks
    "--no-header",                        # skip the pytest header
]
filterwarnings = [
    "error",                              # turn all warnings into errors
    "ignore::DeprecationWarning:pkg_name",
]
log_cli = true                            # show log output during tests
log_cli_level = "INFO"
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# ── Asyncio ───────────────────────────────────────────────────────────────────
asyncio_mode = "auto"

# ── Coverage ──────────────────────────────────────────────────────────────────
# Coverage flags go in addopts; thresholds go in [tool.coverage.report]

[tool.coverage.run]
branch = true                             # measure branch coverage
source = ["src"]
omit = [
    "*/migrations/*",
    "*/conftest.py",
    "*/__init__.py",
    "*/settings*.py",
    "src/main.py",                        # app entry point
]
parallel = true                           # safe for pytest-xdist

[tool.coverage.report]
fail_under = 80
precision = 1
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",
    "\\.\\.\\.",                          # ellipsis body stubs
]

[tool.coverage.json]
output = "coverage.json"
pretty_print = true
```

## pytest-asyncio Modes

pytest-asyncio 1.x (released May 2025) changes some defaults. Use `asyncio_mode = "auto"` in all new projects.

| Mode | Behavior | When to Use |
|------|----------|-------------|
| `auto` | All `async def test_*` and `async def` fixtures are async automatically | Default for new projects |
| `strict` | Must explicitly mark with `@pytest.mark.asyncio` | Migrating legacy codebases |
| `loose` (removed in 1.x) | Deprecated in 0.21, removed in 1.0 | Do not use |

### Loop Scope

Control the event loop lifetime with `asyncio_default_fixture_loop_scope`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"  # one loop for all tests (faster)
```

Valid scopes: `"function"` (default), `"class"`, `"module"`, `"package"`, `"session"`.

Use `"session"` when you have session-scoped async fixtures (e.g., testcontainer connections).

### Async Fixture Scopes

```python
import pytest

@pytest.fixture(scope="session")
async def db_engine():
    """Session-scoped engine — created once, reused across all tests."""
    engine = create_async_engine(DATABASE_URL)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Function-scoped session — rolled back after each test."""
    async with db_engine.begin() as conn:
        yield AsyncSession(bind=conn)
        await conn.rollback()
```

## Marker System

### Registration (required with --strict-markers)

```toml
[tool.pytest.ini_options]
markers = [
    "unit: fast isolated tests with no external I/O",
    "integration: tests requiring real infrastructure (DB, Redis, etc.)",
    "contract: API schema and contract validation tests",
    "slow: tests taking more than 1 second",
    "smoke: critical path tests for quick confidence checks",
    "e2e: end-to-end tests against a live environment",
]
```

### Using Multiple Markers

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_bulk_import(db_session, large_dataset):
    ...
```

### Marker Selectors

```bash
pytest -m "unit and not slow"
pytest -m "integration or contract"
pytest -m "not (slow or e2e)"
```

### Conditional Markers

```python
import sys
import pytest

@pytest.mark.skipif(sys.platform == "win32", reason="Unix socket not supported on Windows")
def test_unix_socket_connection():
    ...

@pytest.mark.xfail(reason="Known race condition — see GH-1234", strict=False)
async def test_concurrent_writes():
    ...
```

## Parametrize — Advanced Patterns

### With IDs

```python
@pytest.mark.parametrize("status_code,expected_retry", [
    pytest.param(429, True,  id="rate-limited"),
    pytest.param(503, True,  id="service-unavailable"),
    pytest.param(200, False, id="success-no-retry"),
    pytest.param(400, False, id="bad-request-no-retry"),
], ids=str)
async def test_retry_logic(status_code, expected_retry, mock_http):
    mock_http.respond(status_code)
    result = await client.get_with_retry("/endpoint")
    assert result.did_retry == expected_retry
```

### Parametrize + Fixtures (indirect)

```python
@pytest.fixture
def user_with_role(request):
    return User(role=request.param, name="test")

@pytest.mark.parametrize("user_with_role", ["admin", "viewer"], indirect=True)
async def test_access_control(user_with_role, http_client):
    response = await http_client.get("/admin", headers={"X-User-Role": user_with_role.role})
    if user_with_role.role == "admin":
        assert response.status_code == 200
    else:
        assert response.status_code == 403
```

### Matrix Parametrize

```python
@pytest.mark.parametrize("protocol", ["http", "grpc"])
@pytest.mark.parametrize("env", ["staging", "production"])
async def test_health_check(protocol, env):
    # Generates 4 tests: http/staging, http/production, grpc/staging, grpc/production
    ...
```

## Test Discovery

Pytest discovers tests by:
1. Starting from `testpaths` (or current dir)
2. Recursing into directories
3. Finding files matching `python_files`
4. Importing them and finding `python_classes` / `python_functions`

Recommended layout:

```
tests/
├── conftest.py              # session/module fixtures shared across all tests
├── unit/
│   ├── conftest.py          # unit-test-specific fixtures
│   └── test_user_service.py
├── integration/
│   ├── conftest.py          # testcontainer fixtures
│   └── test_user_repository.py
└── contract/
    ├── conftest.py
    └── test_user_api_contract.py
```

## Plugin Configuration

### pytest-mock

```python
# mocker fixture is available automatically after `pip install pytest-mock`
def test_send_email(mocker):
    mock_smtp = mocker.patch("app.email.smtplib.SMTP")
    send_welcome_email("user@example.com")
    mock_smtp.return_value.__enter__.return_value.sendmail.assert_called_once()
```

### pytest-httpx

```python
# pytest-httpx: intercept httpx calls without hitting the network
def test_external_api_call(httpx_mock):
    httpx_mock.add_response(json={"id": 1, "name": "Alice"})
    user = fetch_user(id=1)
    assert user.name == "Alice"
```

### pytest-xdist (parallel)

```bash
pip install pytest-xdist
pytest -n auto          # use all CPU cores
pytest -n 4             # use 4 workers
```

Caution: fixtures scoped above `function` must be thread-safe. Testcontainers with `scope="session"` work correctly with xdist when using `xdist_group` markers.

### time-machine

```python
import time_machine
from datetime import datetime

@time_machine.travel("2025-01-15 12:00:00 UTC")
def test_subscription_expiry():
    subscription = Subscription(expires_at=datetime(2025, 1, 14))
    assert subscription.is_expired() is True
```

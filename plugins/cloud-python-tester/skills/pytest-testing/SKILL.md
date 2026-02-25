---
name: cloud-python-tester:pytest-testing
description: "pytest configuration, async testing with pytest-asyncio, test markers, parametrize, coverage enforcement, and plugin setup for Python cloud service test suites. Covers pyproject.toml configuration, test discovery, and common pytest plugins."
user-invocable: false
---

# pytest Testing — Quick Reference

Core pytest patterns for cloud Python services. Covers pyproject.toml config, async testing, markers, parametrize, and coverage enforcement.

## pyproject.toml Baseline

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"           # pytest-asyncio: mark all async tests automatically
testpaths = ["tests"]
addopts = [
    "--strict-markers",         # fail on unknown markers
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=json:coverage.json",
    "--cov-fail-under=80",
]
markers = [
    "unit: fast isolated tests (no I/O)",
    "integration: tests that use real infrastructure",
    "contract: API contract/schema validation tests",
    "slow: tests taking > 1 second",
]

[tool.coverage.run]
branch = true
source = ["src"]
omit = ["*/migrations/*", "*/conftest.py", "*/__init__.py"]

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",
]
```

## Async Testing (pytest-asyncio 1.x)

`asyncio_mode = "auto"` means all `async def test_*` functions and `async def` fixtures are handled automatically — no `@pytest.mark.asyncio` decorator needed.

```python
# All of these work without any decorator in auto mode
async def test_fetch_user(http_client):
    response = await http_client.get("/users/1")
    assert response.status_code == 200

async def test_publish_event(message_bus):
    await message_bus.publish("user.created", {"id": "abc"})
    msg = await message_bus.consume(timeout=1.0)
    assert msg["id"] == "abc"
```

## Markers

```python
import pytest

@pytest.mark.unit
def test_validate_email():
    assert validate_email("a@b.com") is True

@pytest.mark.integration
async def test_save_user(db_session):
    user = await db_session.save(User(name="Alice"))
    assert user.id is not None

@pytest.mark.contract
async def test_create_user_returns_201(http_client):
    response = await http_client.post("/users", json={"name": "Alice"})
    assert response.status_code == 201
```

Run subsets:

```bash
pytest -m unit                   # fast unit tests only
pytest -m "integration or unit"  # exclude slow contract tests
pytest -m "not slow"             # skip everything marked slow
pytest -k "test_user"            # keyword filter
```

## Parametrize

```python
@pytest.mark.parametrize("email,valid", [
    ("user@example.com", True),
    ("not-an-email", False),
    ("@missing-local.com", False),
    ("missing-domain@", False),
])
def test_email_validation(email, valid):
    assert validate_email(email) == valid

# Indirect parametrize: pass params to fixtures
@pytest.mark.parametrize("user_role", ["admin", "viewer", "editor"], indirect=True)
async def test_role_permissions(user_role, http_client):
    response = await http_client.get("/admin/settings")
    ...
```

## Common Plugins

| Plugin | Install | Purpose |
|--------|---------|---------|
| `pytest-asyncio` | `pip install pytest-asyncio` | async/await support |
| `pytest-cov` | `pip install pytest-cov` | coverage reporting |
| `testcontainers` | `pip install testcontainers[postgres,redis,kafka]` | real service containers |
| `pytest-httpx` | `pip install pytest-httpx` | mock httpx requests |
| `pytest-mock` | `pip install pytest-mock` | `mocker` fixture wrapper |
| `factory-boy` | `pip install factory-boy` | test data factories |
| `faker` | `pip install faker` | realistic fake data |
| `time-machine` | `pip install time-machine` | freeze/travel time |
| `pytest-xdist` | `pip install pytest-xdist` | parallel test execution |

## Coverage Flags

```bash
# Run with coverage
pytest --cov=src --cov-fail-under=80

# Generate HTML report
pytest --cov=src --cov-report=html:htmlcov

# Show only uncovered lines
pytest --cov=src --cov-report=term-missing

# JSON report for CI parsing
pytest --cov=src --cov-report=json:coverage.json

# Use pyproject.toml config file explicitly
pytest --cov-config=pyproject.toml
```

## Additional Resources

- [reference.md](reference.md) — Complete pyproject.toml options, all pytest-asyncio modes, marker registration, parametrize advanced usage, plugin configuration details
- [examples.md](examples.md) — Concrete unit test, integration test with testcontainers, and API contract test examples

---
name: coding-cloud-python-tester:fixture-patterns
description: "pytest fixture patterns for Python cloud services: scope hierarchy, testcontainers (PostgreSQL, Redis, Kafka), async fixtures, conftest organization, factory fixtures, and database rollback patterns for isolated test runs."
user-invocable: false
---

# Fixture Patterns — Quick Reference

Fixture design for cloud service test suites. Core rule: share expensive resources via wide scopes; isolate state changes via narrow scopes.

## Scope Hierarchy

```
session  ─ Created once per test run (most expensive: containers, engines)
  module  ─ Created once per test file (medium: schema setup)
    class  ─ Created once per test class
      function ─ Created per test (cheap: sessions, transactions — ROLLBACK here)
```

```python
# Wide scope: containers and engines
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

# Medium scope: schema migrations
@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    engine = create_async_engine(postgres_container.get_async_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

# Narrow scope: isolated, rolled-back session per test
@pytest.fixture
async def db_session(db_engine):
    async with db_engine.connect() as conn:
        await conn.begin()
        yield AsyncSession(bind=conn, expire_on_commit=False)
        await conn.rollback()   # state never persists to next test
```

## Quick Decision Matrix

| Need | Scope | Pattern |
|------|-------|---------|
| Docker container (DB, Redis, Kafka) | `session` | `with Container() as c: yield c` |
| SQLAlchemy engine | `session` | `create_async_engine(url)`, `dispose()` at teardown |
| Database schema | `session` | `create_all` once after engine creation |
| Database session with isolation | `function` | begin transaction → yield → rollback |
| HTTP client for FastAPI | `function` | `AsyncClient(app=app)` with dependency overrides |
| Redis client | `session` or `function` | flush keys in teardown for isolation |
| Kafka producer/consumer | `session` | dedicated topic per test class |
| Factory fixture (test data) | `function` | return factory callable, not fixed object |

## Testcontainers Extras

```bash
pip install testcontainers[postgres]
pip install testcontainers[redis]
pip install testcontainers[kafka]
```

| Container Class | Import |
|----------------|--------|
| `PostgresContainer` | `from testcontainers.postgres import PostgresContainer` |
| `RedisContainer` | `from testcontainers.redis import RedisContainer` |
| `KafkaContainer` | `from testcontainers.kafka import KafkaContainer` |
| `MongoDbContainer` | `from testcontainers.mongodb import MongoDbContainer` |
| `ElasticsearchContainer` | `from testcontainers.elasticsearch import ElasticsearchContainer` |

## conftest.py Hierarchy

```
tests/
├── conftest.py          # session-scoped containers, engines, auth tokens
├── unit/
│   └── conftest.py      # mocks and stubs (no containers)
├── integration/
│   └── conftest.py      # db_session, redis_client (use containers from root)
└── contract/
    └── conftest.py      # http_client, dependency overrides
```

Root conftest provides containers. Subdirectory conftest.py files compose those containers into narrower fixtures.

## Factory Fixtures

Return a callable so tests can create multiple instances with variations:

```python
@pytest.fixture
def make_user(db_session):
    """Factory: call with keyword overrides."""
    async def _factory(**kwargs):
        defaults = {"name": "Test User", "email": "test@example.com", "role": "viewer"}
        data = {**defaults, **kwargs}
        user = User(**data)
        db_session.add(user)
        await db_session.flush()
        return user
    return _factory

# Usage:
async def test_admin_can_delete(make_user, http_client):
    admin = await make_user(role="admin", email="admin@example.com")
    target = await make_user(email="target@example.com")
    ...
```

## Additional Resources

- [reference.md](reference.md) — Testcontainers API (PostgresContainer, RedisContainer, KafkaContainer), async fixtures, conftest composition, database rollback patterns, factory-boy integration
- [examples.md](examples.md) — Complete working fixture examples for each pattern

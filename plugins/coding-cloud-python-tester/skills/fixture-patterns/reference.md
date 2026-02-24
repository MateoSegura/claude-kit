# Fixture Patterns — Complete Reference

Testcontainer API details, async fixture internals, conftest composition, database rollback patterns, and factory-boy integration.

## Testcontainers API

### PostgresContainer

```python
from testcontainers.postgres import PostgresContainer

# Constructor params (all optional, have defaults)
PostgresContainer(
    image="postgres:16-alpine",   # Docker image
    username="test",              # POSTGRES_USER
    password="test",              # POSTGRES_PASSWORD
    dbname="test",                # POSTGRES_DB
    driver="psycopg2",            # SQLAlchemy driver suffix
    port=5432,                    # internal port (always 5432)
)

# Methods
container.get_connection_url()     # "postgresql+psycopg2://test:test@localhost:PORT/test"
container.get_container_host_ip()  # "localhost" or Docker gateway IP
container.get_exposed_port(5432)   # mapped host port as string

# Async URL conversion
sync_url = container.get_connection_url()
async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
```

### RedisContainer

```python
from testcontainers.redis import RedisContainer

RedisContainer(
    image="redis:7-alpine",
    port=6379,
)

# Methods
container.get_container_host_ip()  # host
container.get_exposed_port(6379)   # port as string

# Build URL
host = container.get_container_host_ip()
port = container.get_exposed_port(6379)
url = f"redis://{host}:{port}/0"

# Create async client
import redis.asyncio as aioredis
client = aioredis.Redis(host=host, port=int(port), decode_responses=True)
```

### KafkaContainer

```python
from testcontainers.kafka import KafkaContainer

KafkaContainer(
    image="confluentinc/cp-kafka:7.6.0",
)

# Method
container.get_bootstrap_server()   # "localhost:PORT"

# Use with aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
producer = AIOKafkaProducer(bootstrap_servers=container.get_bootstrap_server())
```

## Async Fixtures

### Scope and Event Loop Alignment

pytest-asyncio 1.x requires that async fixtures and their dependents share an event loop. Set `asyncio_default_fixture_loop_scope` to match your broadest async fixture scope:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
```

This creates a single asyncio event loop for all tests, allowing session-scoped async fixtures to work correctly.

### Session-Scoped Async Fixture Pattern

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


@pytest.fixture(scope="session")
def postgres():
    """Synchronous container — testcontainers manages a sync thread internally."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
async def engine(postgres):
    """Async engine — session-scoped, shared across all tests."""
    url = postgres.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(url, pool_size=5)

    from app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)
```

### Function-Scoped Transactional Isolation

```python
# tests/conftest.py (continued)
@pytest.fixture
async def db(engine):
    """
    Transactional test isolation:
    1. Begin a savepoint (nested transaction)
    2. Run the test
    3. Roll back the savepoint — database returns to pre-test state
    """
    async with engine.connect() as conn:
        await conn.begin()
        # Use nested transaction (SAVEPOINT) so the test can also begin/commit
        await conn.begin_nested()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # Intercept session.commit() to do a savepoint flush instead
        from unittest.mock import patch, AsyncMock
        async def mock_commit():
            await session.flush()
            await conn.begin_nested()  # new savepoint for next commit call

        with patch.object(session, "commit", side_effect=mock_commit):
            yield session

        await session.close()
        await conn.rollback()
```

### Async Context Manager Fixtures

```python
@pytest.fixture
async def redis(redis_container):
    import redis.asyncio as aioredis
    host = redis_container.get_container_host_ip()
    port = int(redis_container.get_exposed_port(6379))
    client = aioredis.Redis(host=host, port=port, decode_responses=True)
    yield client
    # Flush test keys so next test starts clean
    await client.flushdb()
    await client.aclose()
```

## conftest.py Composition

### Root conftest.py (infrastructure)

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as c:
        yield c


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as c:
        yield c


@pytest.fixture(scope="session")
async def engine(postgres_container):
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.database import Base
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    e = create_async_engine(url)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()
```

### Integration conftest.py (sessions + clients)

```python
# tests/integration/conftest.py
import pytest
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def db(engine):
    """Transactional db session for integration tests."""
    async with engine.connect() as conn:
        await conn.begin()
        yield AsyncSession(bind=conn, expire_on_commit=False)
        await conn.rollback()


@pytest.fixture
async def cache(redis_container):
    host = redis_container.get_container_host_ip()
    port = int(redis_container.get_exposed_port(6379))
    client = aioredis.Redis(host=host, port=port, decode_responses=True)
    yield client
    await client.flushdb()
    await client.aclose()
```

### Contract conftest.py (HTTP client with overrides)

```python
# tests/contract/conftest.py
import pytest
import httpx
from app.main import create_app
from app.dependencies import get_db, get_cache


@pytest.fixture
async def http_client(db, cache):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_cache] = lambda: cache

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client

    app.dependency_overrides.clear()
```

## Database Rollback Patterns

### Pattern 1: Connection-Level Rollback (Preferred)

Wraps the entire test in a connection that is never committed to the DB. Uses SQLAlchemy's savepoint mechanism so the test's own `session.commit()` calls don't permanently write data.

```python
@pytest.fixture
async def db(engine):
    async with engine.connect() as conn:
        tx = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await tx.rollback()
```

Limitation: Does not work if the code under test uses a separate engine/connection.

### Pattern 2: Truncate After Test

For tests that must use real transactions (e.g., testing transaction error handling):

```python
TABLES_TO_TRUNCATE = ["users", "orders", "events"]

@pytest.fixture
async def db_clean(engine):
    session = AsyncSession(engine)
    yield session
    await session.close()
    # Truncate in reverse dependency order
    async with engine.begin() as conn:
        for table in reversed(TABLES_TO_TRUNCATE):
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
```

### Pattern 3: Per-Test Schema (Isolation at cost of speed)

```python
@pytest.fixture
async def isolated_db(postgres_container):
    """Create a fresh schema per test — maximum isolation, higher overhead."""
    import uuid
    from sqlalchemy.ext.asyncio import create_async_engine
    schema = f"test_{uuid.uuid4().hex[:8]}"
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA {schema}"))
        await conn.execute(text(f"SET search_path TO {schema}"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
    await engine.dispose()
```

## Factory Fixtures and factory-boy

```python
# tests/factories.py
import factory
from factory import Faker
from app.models import User, Order


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = Faker("name")
    email = Faker("email")
    role = "viewer"
    created_at = factory.LazyFunction(lambda: datetime.utcnow())


class OrderFactory(factory.Factory):
    class Meta:
        model = Order

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user = factory.SubFactory(UserFactory)
    total = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    status = "pending"
```

```python
# tests/conftest.py
@pytest.fixture
def make_user(db):
    """Async factory fixture backed by factory-boy."""
    async def _factory(**kwargs):
        user = UserFactory.build(**kwargs)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    return _factory

@pytest.fixture
def make_order(db, make_user):
    async def _factory(user=None, **kwargs):
        if user is None:
            user = await make_user()
        order = OrderFactory.build(user=user, **kwargs)
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order
    return _factory
```

```python
# Usage in tests
async def test_order_total_with_discount(make_order):
    order = await make_order(total=Decimal("100.00"), status="paid")
    discounted = apply_loyalty_discount(order, percent=10)
    assert discounted.total == Decimal("90.00")
```

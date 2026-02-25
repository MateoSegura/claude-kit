# Fixture Patterns — Complete Examples

Full working examples for each major fixture pattern.

## Complete Postgres + SQLAlchemy Setup

```python
# tests/conftest.py — full session-scoped setup with rollback isolation
import pytest
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from app.database import Base


# ── Containers (session scope) ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def redis_container():
    from testcontainers.redis import RedisContainer
    with RedisContainer("redis:7-alpine") as r:
        yield r


# ── Engine + Schema (session scope) ───────────────────────────────────────────

@pytest.fixture(scope="session")
async def engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    e = create_async_engine(url, echo=False, pool_size=5, max_overflow=10)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # clean slate
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


# ── DB session with transaction rollback (function scope) ─────────────────────

@pytest.fixture
async def db(engine) -> AsyncSession:
    """
    Wraps each test in a rolled-back transaction.
    The test can call session.flush() freely; nothing persists to the DB.
    """
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()


# ── Redis client (function scope) ─────────────────────────────────────────────

@pytest.fixture
async def redis(redis_container):
    import redis.asyncio as aioredis
    host = redis_container.get_container_host_ip()
    port = int(redis_container.get_exposed_port(6379))
    client = aioredis.Redis(host=host, port=port, decode_responses=True)
    yield client
    await client.flushdb()   # reset state for next test
    await client.aclose()


# ── HTTP client with FastAPI dependency overrides ─────────────────────────────

@pytest.fixture
async def http_client(db, redis):
    import httpx
    from app.main import create_app
    from app.dependencies import get_db, get_cache

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_cache] = lambda: redis

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ── Factory fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def make_user(db):
    async def _factory(
        name: str = "Test User",
        email: str | None = None,
        role: str = "viewer",
        **kwargs,
    ):
        from app.models import User
        if email is None:
            email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        user = User(name=name, email=email, role=role, **kwargs)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    return _factory


@pytest.fixture
def make_order(db, make_user):
    async def _factory(
        user=None,
        total: Decimal = Decimal("99.99"),
        status: str = "pending",
        **kwargs,
    ):
        from app.models import Order
        if user is None:
            user = await make_user()
        order = Order(user_id=user.id, total=total, status=status, **kwargs)
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order
    return _factory
```

## Example Test Using All Fixtures

```python
# tests/integration/test_order_service.py
import pytest
from decimal import Decimal
from app.services.order_service import OrderService


@pytest.mark.integration
async def test_complete_order_workflow(db, redis, make_user, make_order):
    """Full happy path: place order, charge, emit event, cache status."""
    user = await make_user(name="Alice", email="alice@example.com")
    order = await make_order(user=user, total=Decimal("150.00"))
    service = OrderService(session=db, cache=redis)

    result = await service.process_order(order.id)

    # Check DB state
    await db.refresh(order)
    assert order.status == "paid"

    # Check cache
    cached = await redis.get(f"order:{order.id}:status")
    assert cached == "paid"

    assert result.success is True


@pytest.mark.integration
async def test_duplicate_order_raises(db, make_order, make_user):
    """Idempotency: processing the same order twice should fail gracefully."""
    from app.exceptions import OrderAlreadyProcessedError
    user = await make_user()
    order = await make_order(user=user, status="paid")
    service = OrderService(session=db, cache=None)

    with pytest.raises(OrderAlreadyProcessedError):
        await service.process_order(order.id)
```

## Kafka Fixture with Topic Per Test

```python
# tests/integration/conftest.py (Kafka section)
import pytest
import uuid
from testcontainers.kafka import KafkaContainer


@pytest.fixture(scope="session")
def kafka_container():
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as k:
        yield k


@pytest.fixture(scope="session")
def kafka_bootstrap(kafka_container):
    return kafka_container.get_bootstrap_server()


@pytest.fixture
def kafka_topic(kafka_bootstrap):
    """Unique topic per test to avoid message bleed-over."""
    topic = f"test-{uuid.uuid4().hex[:8]}"
    # aiokafka creates topics lazily on first produce
    yield topic
    # Topic cleanup happens when container is torn down at session end


@pytest.fixture
async def kafka_producer(kafka_bootstrap):
    from aiokafka import AIOKafkaProducer
    import json

    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest.fixture
async def kafka_consumer(kafka_bootstrap, kafka_topic):
    from aiokafka import AIOKafkaConsumer
    import json

    consumer = AIOKafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_bootstrap,
        auto_offset_reset="earliest",
        group_id=f"test-consumer-{uuid.uuid4().hex[:8]}",
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    yield consumer
    await consumer.stop()
```

```python
# tests/integration/test_event_bus.py
import pytest
import asyncio
from app.events import EventBus


@pytest.mark.integration
@pytest.mark.slow
async def test_event_roundtrip(kafka_producer, kafka_consumer, kafka_topic):
    bus = EventBus(producer=kafka_producer, default_topic=kafka_topic)
    await bus.emit("order.created", {"order_id": "abc-123"})

    received = None
    async for message in kafka_consumer:
        received = message.value
        break  # consume one message

    assert received is not None
    assert received["order_id"] == "abc-123"


@pytest.mark.integration
@pytest.mark.slow
async def test_multiple_events_in_order(kafka_producer, kafka_consumer, kafka_topic):
    bus = EventBus(producer=kafka_producer, default_topic=kafka_topic)

    events = [{"seq": i} for i in range(5)]
    for e in events:
        await bus.emit("seq.test", e)

    received = []
    async for message in kafka_consumer:
        received.append(message.value["seq"])
        if len(received) == 5:
            break

    assert received == list(range(5))
```

## Scoped Fixtures for Auth Context

```python
# tests/conftest.py (auth section)
@pytest.fixture
def auth_token():
    """Generate a signed JWT for test requests."""
    from app.auth import create_access_token
    return create_access_token({"sub": "test-user-id", "role": "viewer"})


@pytest.fixture
def admin_token():
    from app.auth import create_access_token
    return create_access_token({"sub": "admin-user-id", "role": "admin"})


@pytest.fixture
async def authed_client(http_client, auth_token):
    """Pre-authenticated HTTP client for viewer-role tests."""
    http_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    yield http_client


@pytest.fixture
async def admin_client(http_client, admin_token):
    """Pre-authenticated HTTP client for admin-role tests."""
    http_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    yield http_client
```

```python
# Usage:
@pytest.mark.contract
async def test_viewer_cannot_delete_user(authed_client, make_user):
    user = await make_user()
    response = await authed_client.delete(f"/users/{user.id}")
    assert response.status_code == 403


@pytest.mark.contract
async def test_admin_can_delete_user(admin_client, make_user):
    user = await make_user()
    response = await admin_client.delete(f"/users/{user.id}")
    assert response.status_code == 204
```

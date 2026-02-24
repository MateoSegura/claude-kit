# pytest Testing — Concrete Examples

Complete test examples for unit tests, integration tests with testcontainers, and API contract tests.

## Unit Tests

### Service Layer Unit Test

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.models import User


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.find_by_email.return_value = None
    repo.save.side_effect = lambda u: User(id="uuid-1", **u.__dict__)
    return repo


@pytest.fixture
def user_service(mock_user_repo):
    return UserService(repo=mock_user_repo)


@pytest.mark.unit
async def test_create_user_success(user_service, mock_user_repo):
    user = await user_service.create_user(name="Alice", email="alice@example.com")

    assert user.id == "uuid-1"
    assert user.name == "Alice"
    mock_user_repo.save.assert_awaited_once()


@pytest.mark.unit
async def test_create_user_duplicate_email_raises(user_service, mock_user_repo):
    mock_user_repo.find_by_email.return_value = User(id="existing", name="Bob", email="bob@example.com")

    with pytest.raises(ValueError, match="already registered"):
        await user_service.create_user(name="Bob2", email="bob@example.com")


@pytest.mark.unit
@pytest.mark.parametrize("name,email,error_field", [
    ("", "valid@example.com", "name"),
    ("Alice", "not-an-email", "email"),
    ("A" * 256, "valid@example.com", "name"),
])
async def test_create_user_validation_errors(user_service, name, email, error_field):
    with pytest.raises(ValueError) as exc_info:
        await user_service.create_user(name=name, email=email)
    assert error_field in str(exc_info.value).lower()
```

### Pure Function Unit Tests

```python
# tests/unit/test_pricing.py
import pytest
from decimal import Decimal
from app.pricing import calculate_discount, apply_coupon


@pytest.mark.unit
@pytest.mark.parametrize("subtotal,tier,expected_discount", [
    (Decimal("100.00"), "bronze", Decimal("0.00")),
    (Decimal("500.00"), "silver", Decimal("25.00")),   # 5% off
    (Decimal("1000.00"), "gold", Decimal("100.00")),    # 10% off
    (Decimal("5000.00"), "platinum", Decimal("750.00")),# 15% off
])
def test_tier_discounts(subtotal, tier, expected_discount):
    assert calculate_discount(subtotal, tier) == expected_discount


@pytest.mark.unit
def test_coupon_stacks_with_tier_discount():
    subtotal = Decimal("1000.00")
    after_tier = calculate_discount(subtotal, "gold")      # -100.00
    after_coupon = apply_coupon(subtotal - after_tier, "EXTRA10")  # -90.00
    assert after_coupon == Decimal("810.00")


@pytest.mark.unit
def test_invalid_coupon_raises():
    with pytest.raises(ValueError, match="Unknown coupon"):
        apply_coupon(Decimal("100.00"), "INVALID_CODE")
```

## Integration Tests with Testcontainers

### PostgreSQL Integration Test

```python
# tests/integration/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base


@pytest.fixture(scope="session")
def postgres_container():
    """Start a real Postgres container for the test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    # testcontainers gives a sync URL; convert to async driver
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")

    engine = create_async_engine(async_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Transactional session — rolls back after each test."""
    async with db_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()
```

```python
# tests/integration/test_user_repository.py
import pytest
from app.repositories.user_repository import UserRepository
from app.models import User


@pytest.mark.integration
async def test_save_and_find_user(db_session):
    repo = UserRepository(session=db_session)

    user = await repo.save(User(name="Carol", email="carol@example.com"))
    assert user.id is not None

    found = await repo.find_by_email("carol@example.com")
    assert found.name == "Carol"


@pytest.mark.integration
async def test_find_by_email_missing_returns_none(db_session):
    repo = UserRepository(session=db_session)
    result = await repo.find_by_email("nobody@example.com")
    assert result is None


@pytest.mark.integration
async def test_duplicate_email_raises_integrity_error(db_session):
    from sqlalchemy.exc import IntegrityError
    repo = UserRepository(session=db_session)

    await repo.save(User(name="Dave", email="dave@example.com"))
    with pytest.raises(IntegrityError):
        await repo.save(User(name="Dave2", email="dave@example.com"))
```

### Redis Integration Test

```python
# tests/integration/conftest.py (add to existing)
import pytest
from testcontainers.redis import RedisContainer
import redis.asyncio as aioredis


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as r:
        yield r


@pytest.fixture(scope="session")
async def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    client = aioredis.Redis(host=host, port=int(port), decode_responses=True)
    yield client
    await client.aclose()
```

```python
# tests/integration/test_cache_service.py
import pytest
from app.services.cache_service import CacheService


@pytest.mark.integration
async def test_set_and_get_value(redis_client):
    cache = CacheService(redis=redis_client)
    await cache.set("key:test", {"value": 42}, ttl=60)
    result = await cache.get("key:test")
    assert result == {"value": 42}


@pytest.mark.integration
async def test_expired_key_returns_none(redis_client):
    import asyncio
    cache = CacheService(redis=redis_client)
    await cache.set("short:lived", "data", ttl=1)
    await asyncio.sleep(1.1)
    result = await cache.get("short:lived")
    assert result is None
```

### Kafka Integration Test

```python
# tests/integration/conftest.py (add to existing)
import pytest
from testcontainers.kafka import KafkaContainer


@pytest.fixture(scope="session")
def kafka_container():
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as kafka:
        yield kafka


@pytest.fixture(scope="session")
def kafka_bootstrap_servers(kafka_container):
    return kafka_container.get_bootstrap_server()
```

```python
# tests/integration/test_event_publisher.py
import pytest
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.events.publisher import EventPublisher


@pytest.mark.integration
@pytest.mark.slow
async def test_publish_event_reaches_kafka(kafka_bootstrap_servers):
    topic = "test.user.created"
    publisher = EventPublisher(bootstrap_servers=kafka_bootstrap_servers)

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=kafka_bootstrap_servers,
        auto_offset_reset="earliest",
        group_id="test-group",
    )
    await consumer.start()
    try:
        await publisher.publish("user.created", {"id": "abc", "name": "Eve"})

        # Poll with timeout
        msg = None
        async for message in consumer:
            msg = message
            break
        assert msg is not None
        assert b"Eve" in msg.value
    finally:
        await consumer.stop()
        await publisher.close()
```

## API Contract Tests

### FastAPI Contract Test with httpx

```python
# tests/contract/conftest.py
import pytest
import httpx
from app.main import create_app
from app.dependencies import get_db


@pytest.fixture
def app(db_session):
    """App with database dependency overridden."""
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db_session
    return application


@pytest.fixture
async def http_client(app):
    async with httpx.AsyncClient(
        app=app,
        base_url="http://testserver",
        transport=httpx.ASGITransport(app=app),
    ) as client:
        yield client
```

```python
# tests/contract/test_users_api.py
import pytest


@pytest.mark.contract
async def test_create_user_returns_201(http_client):
    response = await http_client.post("/users", json={
        "name": "Frank",
        "email": "frank@example.com",
    })
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["name"] == "Frank"
    assert body["email"] == "frank@example.com"


@pytest.mark.contract
async def test_create_user_missing_email_returns_422(http_client):
    response = await http_client.post("/users", json={"name": "Frank"})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "email"] for e in errors)


@pytest.mark.contract
async def test_get_user_not_found_returns_404(http_client):
    response = await http_client.get("/users/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.contract
async def test_list_users_paginated(http_client):
    # Create 3 users
    for i in range(3):
        await http_client.post("/users", json={
            "name": f"User {i}",
            "email": f"user{i}@example.com",
        })

    response = await http_client.get("/users?page=1&page_size=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3
    assert "next_page" in body


@pytest.mark.contract
async def test_response_headers_include_request_id(http_client):
    response = await http_client.get("/health")
    assert "X-Request-ID" in response.headers
```

### Schema Validation with Pydantic

```python
# tests/contract/test_schema_contracts.py
import pytest
from pydantic import TypeAdapter
from app.schemas import UserResponse, ErrorResponse


@pytest.mark.contract
async def test_user_response_matches_schema(http_client):
    r = await http_client.post("/users", json={"name": "Grace", "email": "grace@example.com"})
    assert r.status_code == 201
    # Pydantic will raise ValidationError if schema doesn't match
    adapter = TypeAdapter(UserResponse)
    user = adapter.validate_python(r.json())
    assert user.email == "grace@example.com"


@pytest.mark.contract
@pytest.mark.parametrize("path", ["/users/bad-id", "/items/missing"])
async def test_not_found_errors_match_error_schema(http_client, path):
    r = await http_client.get(path)
    assert r.status_code == 404
    adapter = TypeAdapter(ErrorResponse)
    adapter.validate_python(r.json())  # raises if schema mismatch
```

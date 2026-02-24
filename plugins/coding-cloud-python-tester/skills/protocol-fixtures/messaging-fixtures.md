# Messaging Test Fixtures

## Kafka with Testcontainers

```python
import pytest
from testcontainers.kafka import KafkaContainer
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

@pytest.fixture(scope="session")
def kafka_container():
    """Start a Kafka container for integration tests."""
    with KafkaContainer("confluentinc/cp-kafka:7.5.0") as kafka:
        yield kafka

@pytest.fixture
async def kafka_producer(kafka_container):
    """Async Kafka producer connected to test container."""
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_container.get_bootstrap_server()
    )
    await producer.start()
    yield producer
    await producer.stop()

@pytest.fixture
async def kafka_consumer(kafka_container):
    """Async Kafka consumer connected to test container."""
    consumer = AIOKafkaConsumer(
        "test-topic",
        bootstrap_servers=kafka_container.get_bootstrap_server(),
        auto_offset_reset="earliest",
        group_id="test-group",
    )
    await consumer.start()
    yield consumer
    await consumer.stop()
```

## Testing Event Publishing

```python
import json

@pytest.mark.asyncio
async def test_publish_event(kafka_producer, kafka_consumer):
    event = {"type": "resource.created", "data": {"id": "test-123"}}
    await kafka_producer.send_and_wait(
        "test-topic", json.dumps(event).encode()
    )

    msg = await asyncio.wait_for(kafka_consumer.__anext__(), timeout=5.0)
    parsed = json.loads(msg.value)
    assert parsed["type"] == "resource.created"
    assert parsed["data"]["id"] == "test-123"
```

## Redis Pub/Sub Fixtures

```python
from testcontainers.redis import RedisContainer
import redis.asyncio as aioredis

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as container:
        yield container

@pytest.fixture
async def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    client = aioredis.Redis(host=host, port=int(port))
    yield client
    await client.aclose()

@pytest.mark.asyncio
async def test_pubsub_notification(redis_client):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications")
    await redis_client.publish("notifications", "test-event")
    msg = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0), timeout=10.0)
    assert msg["data"] == b"test-event"
```

## Celery Eager Mode

```python
@pytest.fixture
def celery_config():
    """Configure Celery for eager (synchronous) test execution."""
    return {
        "task_always_eager": True,
        "task_eager_propagates": True,
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
    }

def test_background_task_runs(celery_config):
    from app.tasks import process_resource
    result = process_resource.delay(resource_id="test-123")
    assert result.successful()
    assert result.result == {"status": "processed", "id": "test-123"}
```

## NATS Fixtures

```python
import nats

@pytest.fixture
async def nats_client():
    """Connect to NATS server (assumes nats-server running in testcontainer or locally)."""
    nc = await nats.connect("nats://localhost:4222")
    yield nc
    await nc.drain()

@pytest.mark.asyncio
async def test_nats_request_reply(nats_client):
    async def handler(msg):
        await msg.respond(b"pong")

    sub = await nats_client.subscribe("test.ping", cb=handler)
    response = await nats_client.request("test.ping", b"ping", timeout=2.0)
    assert response.data == b"pong"
    await sub.unsubscribe()
```

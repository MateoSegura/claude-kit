---
name: cloud-python-knowledge:distributed-systems
description: "Python-specific distributed systems implementations: tenacity retries, pybreaker circuit breakers, aio-pika (RabbitMQ), aiokafka, redis.asyncio Streams consumers, asyncio-based outbox publisher, and idempotency patterns with FastAPI. For language-agnostic concepts, see core-backend:distributed-systems."
user-invocable: false
---

# Distributed Systems -- Python Implementations

Python-specific implementations using production libraries. For language-agnostic pattern concepts (circuit breaker theory, saga pattern, CQRS, eventual consistency rules), see the `core-backend:distributed-systems` skill.

## Additional resources

- [patterns-reference.md](patterns-reference.md) -- Full Python implementations: asyncio circuit breaker, retry, outbox with SQLAlchemy, idempotency store, event bus
- [anti-patterns.md](anti-patterns.md) -- Python-specific mistakes: blocking I/O in async, missing connection pool limits, unbounded asyncio.gather

---

## Library Quick Reference

| Pattern | Python Library | Install |
|---------|---------------|---------|
| Retry + backoff | `tenacity` | `pip install tenacity` |
| Circuit breaker | `pybreaker` | `pip install pybreaker` |
| RabbitMQ | `aio-pika` | `pip install aio-pika` |
| Kafka | `aiokafka` | `pip install aiokafka` |
| Redis Streams | `redis.asyncio` | `pip install redis` |
| HTTP client | `httpx` | `pip install httpx` |

---

## Retry with tenacity

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential_jitter,
    retry_if_exception_type, before_sleep_log,
)
import logging

@retry(
    retry=retry_if_exception_type((TransientError, httpx.TransportError)),
    wait=wait_exponential_jitter(initial=0.5, max=30, jitter=1),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def call_external_service(payload: dict) -> dict:
    return await http_client.post("/endpoint", json=payload)
```

---

## Circuit Breaker with pybreaker

```python
from pybreaker import CircuitBreaker, CircuitBreakerError

payment_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="payment-service",
)

@payment_breaker
async def charge_card(amount: int, token: str) -> dict:
    return await payment_client.charge(amount, token)

try:
    result = await charge_card(amount, token)
except CircuitBreakerError:
    await payment_queue.enqueue({"amount": amount, "token": token})
    return {"status": "queued"}
```

---

## Redis Streams Consumer

```python
import redis.asyncio as redis

r = redis.from_url("redis://localhost:6379", decode_responses=True)

# Produce
await r.xadd("orders", {"order_id": "123", "amount": "99.99"}, maxlen=10000)

# Consumer group
await r.xgroup_create("orders", "processors", id="0", mkstream=True)
messages = await r.xreadgroup("processors", "worker-1", {"orders": ">"}, count=10)
for stream, entries in messages:
    for msg_id, data in entries:
        await process_order(data)
        await r.xack("orders", "processors", msg_id)
```

---

## RabbitMQ with aio-pika

```python
import aio_pika

conn = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
channel = await conn.channel()
queue = await channel.declare_queue("tasks", durable=True)

# Publish
await channel.default_exchange.publish(
    aio_pika.Message(
        body=json.dumps(payload).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    ),
    routing_key="tasks",
)

# Consume
async with queue.iterator() as q:
    async for message in q:
        async with message.process():
            await handle_task(json.loads(message.body))
```

---

## Kafka with aiokafka

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
await producer.start()
await producer.send_and_wait("events", value=json.dumps(event).encode(), key=key.encode())

consumer = AIOKafkaConsumer(
    "events", bootstrap_servers="localhost:9092",
    group_id="my-group", auto_offset_reset="earliest",
)
await consumer.start()
async for msg in consumer:
    await handle_event(json.loads(msg.value))
```

---

## FastAPI Idempotency Dependency

```python
from fastapi import Depends, Header
from typing import Annotated

async def check_idempotency(
    idempotency_key: Annotated[str | None, Header()] = None,
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> str | None:
    if idempotency_key:
        cached = await store.get_cached_result(idempotency_key)
        if cached:
            raise IdempotentResponseException(cached)
    return idempotency_key
```

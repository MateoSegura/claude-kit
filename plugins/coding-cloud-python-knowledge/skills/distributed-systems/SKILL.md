---
name: coding-cloud-python-knowledge:distributed-systems
description: "Distributed systems patterns for Python cloud backends: circuit breakers, retries with exponential backoff, service discovery, event-driven architecture, message queues (Redis Streams, RabbitMQ, Kafka), saga pattern, CQRS, and eventual consistency. Load when designing or implementing inter-service communication, fault tolerance, or event-driven workflows."
---

# Distributed Systems — Pattern Catalog

## Additional resources

- [patterns-reference.md](patterns-reference.md) — Full implementations: circuit breaker, retry, saga, CQRS, message queue consumers
- [anti-patterns.md](anti-patterns.md) — Common mistakes that cause cascading failures, race conditions, message loss

---

## Pattern Decision Matrix

| Need | Pattern | Trade-off |
|------|---------|-----------|
| Prevent cascading failures | Circuit Breaker | Adds latency when closed; fast fail when open |
| Handle transient errors | Retry + Exponential Backoff | Must be idempotent; cap max attempts |
| Avoid thundering herd on retry | Jitter | Slightly less predictable timing |
| Coordinate multi-service transaction | Saga (choreography or orchestration) | Complex rollback logic |
| Separate read/write models | CQRS | Eventual consistency; more code |
| Decouple producers/consumers | Message Queue (Redis/RabbitMQ/Kafka) | At-least-once delivery; need deduplication |
| Order-sensitive event stream | Kafka | High throughput; partition ordering only |
| Lightweight pub/sub | Redis Streams or Pub/Sub | Redis Pub/Sub loses messages on restart |
| Reliable task queue | RabbitMQ | Requires broker management |
| Audit log / replay | Event Sourcing | Query complexity; storage growth |

---

## Retry + Backoff Quick Reference

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential_jitter,
    retry_if_exception_type, before_sleep_log,
)
import logging

# Exponential backoff with jitter (best practice for cloud services)
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

**Rules:**
- Only retry idempotent operations (GET, PUT, DELETE — NOT non-idempotent POST)
- Use jitter to avoid thundering herd (`wait_exponential_jitter` not `wait_exponential`)
- Set `stop_after_attempt` — unbounded retries cause resource exhaustion
- Log each retry with context (attempt number, wait time, error type)

---

## Circuit Breaker Quick Reference

```python
from pybreaker import CircuitBreaker, CircuitBreakerError

payment_breaker = CircuitBreaker(
    fail_max=5,         # open after 5 consecutive failures
    reset_timeout=30,   # try again after 30 seconds (half-open)
    name="payment-service",
)

@payment_breaker
async def charge_card(amount: int, token: str) -> dict:
    return await payment_client.charge(amount, token)

# Usage: handle open circuit
try:
    result = await charge_card(amount, token)
except CircuitBreakerError:
    # Fallback: queue for later processing
    await payment_queue.enqueue({"amount": amount, "token": token})
    return {"status": "queued", "message": "Payment will be processed shortly"}
```

**States:** CLOSED (normal) → OPEN (fast-fail after fail_max) → HALF-OPEN (test request) → CLOSED

---

## Message Queue Quick Reference

### Redis Streams (lightweight, ordered, persistent)

```python
import redis.asyncio as redis

r = redis.from_url("redis://localhost:6379", decode_responses=True)

# Produce
await r.xadd("orders", {"order_id": "123", "amount": "99.99"}, maxlen=10000)

# Consume (consumer group — at-least-once, ack required)
await r.xgroup_create("orders", "processors", id="0", mkstream=True)
messages = await r.xreadgroup("processors", "worker-1", {"orders": ">"}, count=10)
for stream, entries in messages:
    for msg_id, data in entries:
        await process_order(data)
        await r.xack("orders", "processors", msg_id)
```

### aio-pika (RabbitMQ — durable queues, dead-letter exchange)

```python
import aio_pika

conn = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
channel = await conn.channel()
queue = await channel.declare_queue("tasks", durable=True)

# Publish
await channel.default_exchange.publish(
    aio_pika.Message(body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
    routing_key="tasks",
)

# Consume
async with queue.iterator() as q:
    async for message in q:
        async with message.process():          # ack on exit, nack on exception
            await handle_task(json.loads(message.body))
```

### aiokafka (Kafka — high-throughput, partition ordering)

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
await producer.start()
await producer.send_and_wait("events", value=json.dumps(event).encode(), key=partition_key.encode())

consumer = AIOKafkaConsumer("events", bootstrap_servers="localhost:9092", group_id="my-group", auto_offset_reset="earliest")
await consumer.start()
async for msg in consumer:
    await handle_event(json.loads(msg.value))
```

---

## Saga Pattern Quick Reference

### Choreography (event-driven, no central coordinator)

```python
# Each service listens for events and emits its own
# OrderService → emits OrderCreated
# InventoryService → listens OrderCreated, emits StockReserved or StockFailed
# PaymentService → listens StockReserved, emits PaymentCharged or PaymentFailed
# Each failure triggers a compensating event

async def handle_order_created(event: OrderCreated) -> None:
    try:
        await inventory.reserve(event.items)
        await events.publish(StockReserved(order_id=event.order_id))
    except InsufficientStock:
        await events.publish(StockReservationFailed(order_id=event.order_id))
```

### Orchestration (central saga coordinator)

```python
class OrderSaga:
    async def execute(self, order_id: str) -> SagaResult:
        steps = [
            SagaStep(action=reserve_inventory, compensation=release_inventory),
            SagaStep(action=charge_payment, compensation=refund_payment),
            SagaStep(action=schedule_shipping, compensation=cancel_shipping),
        ]
        completed = []
        for step in steps:
            try:
                await step.action(order_id)
                completed.append(step)
            except Exception as e:
                # Rollback all completed steps in reverse order
                for done_step in reversed(completed):
                    await done_step.compensation(order_id)
                return SagaResult(success=False, error=str(e))
        return SagaResult(success=True)
```

---

## CQRS Quick Reference

```python
# Commands mutate state; Queries read state
# Separate handlers, separate models

class CreateOrderCommand(BaseModel):
    user_id: UUID
    items: list[OrderItem]

class OrderCommandHandler:
    async def handle(self, cmd: CreateOrderCommand, db: AsyncSession) -> UUID:
        order = Order.create(user_id=cmd.user_id, items=cmd.items)
        db.add(order)
        await db.flush()
        await event_bus.publish(OrderCreated(order_id=order.id, items=cmd.items))
        return order.id

# Read model (denormalized for fast queries)
class OrderReadModel(BaseModel):
    order_id: UUID
    user_name: str         # denormalized from user service
    item_count: int
    total_amount: Decimal
    status: str

class OrderQueryHandler:
    async def get_order(self, order_id: UUID) -> OrderReadModel:
        return await read_db.orders.find_one({"_id": str(order_id)})
```

---

## Eventual Consistency Rules

1. **Idempotency keys**: Every operation that mutates state must accept and store an idempotency key. Duplicate deliveries must produce the same outcome.
2. **Outbox pattern**: Write events to an outbox table in the same transaction as the state change. A separate process publishes from the outbox.
3. **Deduplication**: Consumers must track processed message IDs (Redis SET with TTL or DB table).
4. **Compensating transactions**: Every write operation must have a corresponding compensating operation for saga rollback.
5. **Read-your-writes**: If UI requires seeing its own writes immediately, use sticky sessions or synchronous confirmation before redirecting.

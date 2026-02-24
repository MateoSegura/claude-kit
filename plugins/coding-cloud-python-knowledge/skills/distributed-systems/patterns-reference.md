# Distributed Systems — Patterns Reference

Full implementations for production distributed systems patterns in Python.

---

## Circuit Breaker — Full Implementation

```python
# app/resilience/circuit_breaker.py
import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any
import structlog

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    fail_threshold: int = 5          # failures before opening
    success_threshold: int = 2       # successes to close from half-open
    timeout_seconds: float = 30.0    # seconds before trying half-open
    expected_exceptions: tuple = (Exception,)

class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.config.timeout_seconds:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, fn: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        try:
            result = await fn(*args, **kwargs)
            await self._on_success(current_state)
            return result
        except self.config.expected_exceptions as e:
            await self._on_failure(current_state)
            raise

    async def _on_success(self, state: CircuitState):
        async with self._lock:
            if state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info("Circuit closed", breaker=self.name)
            else:
                self._failure_count = max(0, self._failure_count - 1)

    async def _on_failure(self, state: CircuitState):
        async with self._lock:
            self._failure_count += 1
            self._success_count = 0
            if self._failure_count >= self.config.fail_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "Circuit opened",
                    breaker=self.name,
                    failures=self._failure_count,
                )

class CircuitOpenError(Exception):
    pass
```

---

## Retry with Exponential Backoff — Full Implementation

```python
# app/resilience/retry.py
import asyncio
import random
import time
from dataclasses import dataclass
from typing import TypeVar, Callable, Type
import structlog

logger = structlog.get_logger()
T = TypeVar("T")

@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 0.5
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter_factor: float = 0.25
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,)

async def retry_with_backoff(
    fn: Callable,
    config: RetryConfig = RetryConfig(),
    *args,
    **kwargs,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, config.max_attempts + 1):
        try:
            return await fn(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exc = e
            if attempt == config.max_attempts:
                break
            delay = min(
                config.initial_delay * (config.exponential_base ** (attempt - 1)),
                config.max_delay,
            )
            jitter = delay * config.jitter_factor * (2 * random.random() - 1)
            wait = max(0, delay + jitter)
            logger.warning(
                "Retrying after error",
                attempt=attempt,
                max_attempts=config.max_attempts,
                wait_seconds=round(wait, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            await asyncio.sleep(wait)
    raise last_exc
```

---

## Outbox Pattern — Transactional Event Publishing

```python
# app/outbox.py
"""
Guarantees at-least-once delivery of events by writing them to a DB table
in the same transaction as the business operation, then publishing async.
"""
from sqlalchemy import Column, String, JSON, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
import asyncio
import json

class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    topic: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class OutboxPublisher:
    """Polls outbox table and publishes unpublished messages."""
    def __init__(self, kafka_producer, poll_interval: float = 1.0):
        self._producer = kafka_producer
        self._poll_interval = poll_interval
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        while self._running:
            try:
                await self._publish_pending()
            except Exception:
                logger.exception("Outbox poll error")
            await asyncio.sleep(self._poll_interval)

    async def _publish_pending(self):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutboxMessage)
                .where(OutboxMessage.published == False)
                .limit(100)
                .with_for_update(skip_locked=True)  # avoid contention between workers
            )
            messages = list(result.scalars().all())
            for msg in messages:
                await self._producer.send_and_wait(
                    msg.topic,
                    value=json.dumps(msg.payload).encode(),
                )
                msg.published = True
            await db.commit()

# In service layer — write event to outbox in same transaction as state change:
async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    order = Order(**data.model_dump())
    db.add(order)
    db.add(OutboxMessage(
        topic="orders",
        payload={"event": "OrderCreated", "order_id": str(order.id)},
    ))
    # Both committed atomically — event cannot be lost
    await db.commit()
    return order
```

---

## Idempotency Key Pattern

```python
# app/idempotency.py
import hashlib
import json
from datetime import timedelta
import redis.asyncio as redis

class IdempotencyStore:
    def __init__(self, redis_client: redis.Redis, ttl: timedelta = timedelta(days=1)):
        self._redis = redis_client
        self._ttl = int(ttl.total_seconds())

    async def get_cached_result(self, key: str) -> dict | None:
        value = await self._redis.get(f"idempotency:{key}")
        if value:
            return json.loads(value)
        return None

    async def store_result(self, key: str, result: dict) -> None:
        await self._redis.setex(
            f"idempotency:{key}",
            self._ttl,
            json.dumps(result, default=str),
        )

def idempotency_key_from_request(body: bytes, user_id: str) -> str:
    content = json.dumps({"user_id": user_id, "body": body.decode()}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

# FastAPI dependency
async def check_idempotency(
    idempotency_key: Annotated[str | None, Header()] = None,
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> str | None:
    if idempotency_key:
        cached = await store.get_cached_result(idempotency_key)
        if cached:
            raise IdemopotentResponseException(cached)  # return cached response
    return idempotency_key
```

---

## Event Bus — Async Pub/Sub

```python
# app/events/bus.py
from collections import defaultdict
from typing import Callable, Type, Any
import asyncio
import inspect

class EventBus:
    def __init__(self):
        self._handlers: defaultdict[Type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type) -> Callable:
        """Decorator: @bus.subscribe(OrderCreated)"""
        def decorator(fn: Callable) -> Callable:
            self._handlers[event_type].append(fn)
            return fn
        return decorator

    async def publish(self, event: Any) -> None:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            logger.warning("No handlers for event", event_type=type(event).__name__)
            return
        tasks = [asyncio.create_task(self._invoke(h, event)) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.exception("Event handler failed", error=str(r))

    async def _invoke(self, handler: Callable, event: Any) -> None:
        if inspect.iscoroutinefunction(handler):
            await handler(event)
        else:
            await asyncio.to_thread(handler, event)

bus = EventBus()

# Usage
@bus.subscribe(OrderCreated)
async def send_confirmation_email(event: OrderCreated) -> None:
    await email_service.send_order_confirmation(event.order_id, event.user_email)

@bus.subscribe(OrderCreated)
async def update_inventory(event: OrderCreated) -> None:
    await inventory_service.reserve(event.items)
```

---

## Service Discovery — DNS-Based (K8s)

```python
# In Kubernetes, services are discoverable via DNS: <service>.<namespace>.svc.cluster.local

# app/discovery.py
import httpx
import os

class ServiceRegistry:
    """DNS-based service discovery for Kubernetes."""
    def __init__(self, namespace: str = "default"):
        self._namespace = namespace
        self._clients: dict[str, httpx.AsyncClient] = {}

    def client_for(self, service_name: str) -> httpx.AsyncClient:
        if service_name not in self._clients:
            host = f"http://{service_name}.{self._namespace}.svc.cluster.local"
            self._clients[service_name] = httpx.AsyncClient(
                base_url=host,
                timeout=httpx.Timeout(connect=1.0, read=10.0),
            )
        return self._clients[service_name]

    async def close_all(self):
        for client in self._clients.values():
            await client.aclose()

# External services: use environment variables for URLs
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-svc:8080")
```

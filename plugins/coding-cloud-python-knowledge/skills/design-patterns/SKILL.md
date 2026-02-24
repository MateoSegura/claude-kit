---
name: coding-cloud-python-knowledge:design-patterns
description: "Python cloud-backend design patterns: repository pattern, unit of work, dependency injection, factory, strategy, observer for events, structured logging, OpenTelemetry tracing, graceful shutdown, and connection pooling. Load when architecting Python backend services, reviewing code structure, or implementing cross-cutting concerns."
---

# Design Patterns — Python Cloud Backend

Quick reference for domain-specific patterns. See patterns-reference.md for full implementations. See anti-patterns.md for common mistakes to avoid.

## Additional resources

- [patterns-reference.md](patterns-reference.md) — Full implementations: repository, unit of work, DI container, factory, strategy, observer, OpenTelemetry, graceful shutdown
- [anti-patterns.md](anti-patterns.md) — Things to avoid: fat services, anemic domain models, sync blocking in async, missing connection cleanup

---

## Pattern Categories

| Category | Patterns | When to Load Reference |
|----------|----------|------------------------|
| Data Access | Repository, Unit of Work | DB interaction, transaction management |
| Composition | Dependency Injection, Factory, Strategy | Service wiring, runtime dispatch |
| Events | Observer, Event Bus, Outbox | Decoupled side effects, message publishing |
| Observability | Structured Logging, OpenTelemetry | Tracing, metrics, log correlation |
| Lifecycle | Graceful Shutdown, Connection Pooling | Startup/shutdown, resource management |

---

## Decision Matrix

| Need | Pattern | Trade-off |
|------|---------|-----------|
| Abstract DB queries from business logic | Repository | Extra abstraction layer; worth it for testability |
| Atomic multi-repo operations | Unit of Work | Single session shared across repos |
| Wire dependencies without tight coupling | DI (FastAPI `Depends`) | Slight verbosity; excellent testability |
| Create objects by type at runtime | Factory | Adds indirection; good for plugins/strategies |
| Swap algorithms at runtime | Strategy | More classes; cleaner than if/elif chains |
| Decouple side effects from core logic | Observer/Event Bus | Async exceptions must be caught explicitly |
| Guarantee event delivery | Outbox Pattern | Requires polling worker; adds infra |
| Correlate logs/traces/metrics | OpenTelemetry | SDK setup overhead; essential in production |
| Drain requests before shutdown | Graceful Shutdown | Adds shutdown time; prevents dropped requests |

---

## Repository Pattern Quick Reference

```python
from abc import ABC, abstractmethod
from uuid import UUID
from typing import Generic, TypeVar

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: UUID) -> T | None: ...
    @abstractmethod
    async def add(self, entity: T) -> T: ...
    @abstractmethod
    async def update(self, entity: T) -> T: ...
    @abstractmethod
    async def delete(self, id: UUID) -> None: ...

class SQLAlchemyUserRepository(Repository[User]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> User | None:
        return await self._session.get(User, id)

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user
```

---

## Unit of Work Quick Reference

```python
class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self._session = self._session_factory()
        self.users = SQLAlchemyUserRepository(self._session)
        self.orders = SQLAlchemyOrderRepository(self._session)
        return self

    async def __aexit__(self, exc_type, *_):
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

# Usage
async def create_order_with_inventory(cmd: CreateOrderCommand) -> str:
    async with UnitOfWork(AsyncSessionLocal) as uow:
        user = await uow.users.get(cmd.user_id)
        order = Order.create(user, cmd.items)
        await uow.orders.add(order)
        await uow.inventory.reserve(cmd.items, order.id)
        # commit on __aexit__ — all or nothing
    return str(order.id)
```

---

## Graceful Shutdown Quick Reference

```python
import signal, asyncio

class GracefulShutdown:
    def __init__(self):
        self._shutdown = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    def install(self):
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_signal)

    def _handle_signal(self):
        logger.info("Shutdown signal received")
        self._shutdown.set()

    async def wait(self):
        await self._shutdown.wait()

    async def shutdown(self, timeout: float = 30.0):
        logger.info("Starting graceful shutdown")
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Shutdown complete")
```

---

## OpenTelemetry Quick Reference

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def configure_telemetry(service_name: str, otlp_endpoint: str):
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI, SQLAlchemy, httpx
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()

# Manual spans
tracer = trace.get_tracer(__name__)

async def process_order(order_id: str) -> None:
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        try:
            result = await order_service.process(order_id)
            span.set_attribute("order.status", result.status)
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
```

---

## Structured Logging Quick Reference

```python
import structlog

# Configure once at startup (see patterns-reference.md for full setup)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # merge bound context
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

# Bind request context for all logs in this request
with structlog.contextvars.bound_contextvars(
    request_id=request_id,
    user_id=str(user.id),
):
    logger.info("Processing order", order_id=order_id, amount=amount)
    # → {"event": "Processing order", "request_id": "...", "user_id": "...", "order_id": "...", "amount": 99.99}
```

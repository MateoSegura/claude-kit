# Design Patterns Reference — Python Cloud Backend

Full Python implementations for production-grade design patterns. For language-agnostic pattern concepts and pseudocode, see `core-architecture:design-patterns`.

---

## Repository Pattern — Full Implementation

**Problem:** Business logic is tightly coupled to SQLAlchemy queries, making it hard to test or swap data stores.

**Solution:** Abstract data access behind an interface. Business logic calls `repo.get()`, not `db.execute(select(...))`.

```python
# app/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Sequence
from uuid import UUID

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: UUID) -> T | None: ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 20) -> Sequence[T]: ...

    @abstractmethod
    async def add(self, entity: T) -> T: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: UUID) -> bool: ...

# app/repositories/user_repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyUserRepository(Repository[User]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> User | None:
        return await self._session.get(User, id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        result = await self._session.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self._session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()   # write to DB, stay in transaction
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, id: UUID) -> bool:
        user = await self.get(id)
        if not user:
            return False
        await self._session.delete(user)
        await self._session.flush()
        return True
```

**When to use:** Any service layer that interacts with a database.
**Trade-off:** Extra abstraction layer. Worth it when: (1) writing tests (mock the repo), (2) potentially swapping databases, (3) keeping service layer clean.

---

## Unit of Work Pattern

**Problem:** A business operation touches multiple repositories, but they need to share one transaction.

**Solution:** Unit of Work wraps a session and exposes repositories. All repos share the same session. Commit/rollback is on the UoW.

```python
# app/uow.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self._session: AsyncSession = self._factory()
        # Expose repos — all share same session
        self.users = SQLAlchemyUserRepository(self._session)
        self.orders = SQLAlchemyOrderRepository(self._session)
        self.inventory = SQLAlchemyInventoryRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        """Write to DB without committing — useful for getting generated IDs."""
        await self._session.flush()

# FastAPI dependency
async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(AsyncSessionLocal) as uow:
        yield uow

# Usage in service
async def transfer_funds(
    from_account_id: UUID,
    to_account_id: UUID,
    amount: Decimal,
    uow: UnitOfWork,
) -> None:
    from_acc = await uow.accounts.get(from_account_id)
    to_acc = await uow.accounts.get(to_account_id)
    if not from_acc or not to_acc:
        raise NotFoundError("Account not found")
    if from_acc.balance < amount:
        raise InsufficientFundsError("Insufficient balance")
    from_acc.balance -= amount
    to_acc.balance += amount
    # Both updates committed atomically on __aexit__
```

---

## Dependency Injection — Service Wiring

**Problem:** Services need other services. Manual instantiation creates tight coupling and makes testing hard.

**Solution:** Use FastAPI's `Depends` system with a layered dependency graph.

```python
# app/dependencies.py
from functools import lru_cache
from fastapi import Depends
from typing import Annotated

# Settings — cached globally (created once)
@lru_cache
def get_settings() -> Settings:
    return Settings()

# Database session factory
@lru_cache
def get_session_factory() -> async_sessionmaker:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_size=20)
    return async_sessionmaker(engine, expire_on_commit=False)

# UoW per-request
async def get_uow(
    factory: Annotated[async_sessionmaker, Depends(get_session_factory)],
) -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(factory) as uow:
        yield uow

# HTTP client — cached globally (connection pool reused)
@lru_cache
def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100),
        timeout=httpx.Timeout(10.0),
    )

# Service layer — composed from dependencies
def get_user_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    return UserService(uow=uow, http_client=http_client, settings=settings)

# Type alias for cleaner endpoints
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

@router.post("/users")
async def create_user(body: UserCreate, svc: UserServiceDep) -> UserResponse:
    user = await svc.create(body)
    return UserResponse.model_validate(user)
```

---

## Factory Pattern

**Problem:** Need to create different implementations of an interface based on runtime configuration.

**Solution:** Factory function or class that returns the correct implementation.

```python
# app/storage/factory.py
from enum import Enum

class StorageBackend(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"

class StorageClient(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes) -> str: ...
    @abstractmethod
    async def download(self, key: str) -> bytes: ...
    @abstractmethod
    async def delete(self, key: str) -> None: ...

class S3StorageClient(StorageClient):
    def __init__(self, bucket: str, region: str): ...
    async def upload(self, key: str, data: bytes) -> str:
        ...

class GCSStorageClient(StorageClient):
    def __init__(self, bucket: str, project: str): ...
    async def upload(self, key: str, data: bytes) -> str:
        ...

class LocalStorageClient(StorageClient):
    def __init__(self, base_path: str): ...
    async def upload(self, key: str, data: bytes) -> str:
        ...

def create_storage_client(settings: Settings) -> StorageClient:
    match settings.storage_backend:
        case StorageBackend.S3:
            return S3StorageClient(bucket=settings.s3_bucket, region=settings.aws_region)
        case StorageBackend.GCS:
            return GCSStorageClient(bucket=settings.gcs_bucket, project=settings.gcp_project)
        case StorageBackend.LOCAL:
            return LocalStorageClient(base_path=settings.local_storage_path)
        case _:
            raise ValueError(f"Unknown storage backend: {settings.storage_backend}")

# Register as DI dependency
@lru_cache
def get_storage_client() -> StorageClient:
    return create_storage_client(get_settings())
```

---

## Strategy Pattern

**Problem:** Multiple algorithms for the same operation (pricing, shipping, auth) with if/elif chains.

**Solution:** Define strategy interface; swap implementation at runtime.

```python
# app/pricing/strategies.py
from abc import ABC, abstractmethod
from decimal import Decimal

class PricingStrategy(ABC):
    @abstractmethod
    async def calculate(self, base_price: Decimal, context: PricingContext) -> Decimal: ...

class StandardPricing(PricingStrategy):
    async def calculate(self, base_price: Decimal, context: PricingContext) -> Decimal:
        return base_price

class PremiumPricing(PricingStrategy):
    async def calculate(self, base_price: Decimal, context: PricingContext) -> Decimal:
        return base_price * Decimal("0.85")  # 15% discount

class DynamicPricing(PricingStrategy):
    def __init__(self, demand_client: DemandAPIClient):
        self._demand = demand_client

    async def calculate(self, base_price: Decimal, context: PricingContext) -> Decimal:
        demand_factor = await self._demand.get_factor(context.product_id)
        return base_price * demand_factor

# Registry for factory + strategy together
PRICING_STRATEGIES: dict[str, type[PricingStrategy]] = {
    "standard": StandardPricing,
    "premium": PremiumPricing,
    "dynamic": DynamicPricing,
}

class PricingService:
    def __init__(self, strategy: PricingStrategy):
        self._strategy = strategy

    async def get_price(self, base_price: Decimal, context: PricingContext) -> Decimal:
        return await self._strategy.calculate(base_price, context)
```

---

## Observer Pattern — Event-Driven Side Effects

```python
# app/events/dispatcher.py
from collections import defaultdict
from typing import Callable, Type, Any
import asyncio

class EventDispatcher:
    def __init__(self):
        self._handlers: defaultdict[Type, list[Callable]] = defaultdict(list)

    def on(self, event_type: Type) -> Callable:
        """Decorator: @dispatcher.on(UserCreated)"""
        def decorator(fn: Callable) -> Callable:
            self._handlers[event_type].append(fn)
            return fn
        return decorator

    async def dispatch(self, event: Any) -> None:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        results = await asyncio.gather(
            *[asyncio.ensure_future(h(event)) for h in handlers],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception(
                    "Event handler failed",
                    event_type=type(event).__name__,
                    handler=handlers[i].__name__,
                    exc_info=result,
                )

dispatcher = EventDispatcher()

@dispatcher.on(UserCreated)
async def send_welcome_email(event: UserCreated) -> None:
    await email_service.send_welcome(event.user_id, event.email)

@dispatcher.on(UserCreated)
async def provision_default_workspace(event: UserCreated) -> None:
    await workspace_service.create_default(event.user_id)
```

---

## OpenTelemetry — Full Setup

```python
# app/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import structlog

def setup_telemetry(service_name: str, otlp_endpoint: str = "http://otel-collector:4317") -> None:
    resource = Resource.create({SERVICE_NAME: service_name, "service.version": "1.0.0"})

    # Traces
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True),
            max_export_batch_size=512,
            export_timeout_millis=30_000,
        )
    )
    trace.set_tracer_provider(trace_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=60_000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    # Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=trace_provider)
    HTTPXClientInstrumentor().instrument(tracer_provider=trace_provider)
    RedisInstrumentor().instrument(tracer_provider=trace_provider)

# Inject trace context into structlog
def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

# Custom metrics
meter = metrics.get_meter(__name__)
order_counter = meter.create_counter("orders.created", unit="1", description="Number of orders created")
request_duration = meter.create_histogram("http.request.duration", unit="ms")

# Usage
order_counter.add(1, {"status": "success", "tier": "premium"})
```

---

## Graceful Shutdown — Full Implementation

```python
# app/shutdown.py
import asyncio
import signal
from typing import Callable
import structlog

logger = structlog.get_logger()

class GracefulShutdown:
    def __init__(self, app_name: str = "service", shutdown_timeout: float = 30.0):
        self._app_name = app_name
        self._shutdown_timeout = shutdown_timeout
        self._event = asyncio.Event()
        self._cleanup_hooks: list[Callable] = []

    def register_cleanup(self, fn: Callable) -> None:
        """Register an async cleanup function to call on shutdown."""
        self._cleanup_hooks.append(fn)

    def install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)

    def _signal_handler(self, sig: signal.Signals) -> None:
        logger.info("Shutdown signal received", signal=sig.name)
        self._event.set()

    async def wait_for_shutdown(self) -> None:
        await self._event.wait()

    async def execute_shutdown(self) -> None:
        logger.info("Executing graceful shutdown", app=self._app_name)
        try:
            async with asyncio.timeout(self._shutdown_timeout):
                for fn in reversed(self._cleanup_hooks):
                    try:
                        await fn()
                    except Exception:
                        logger.exception("Cleanup hook failed", hook=fn.__name__)
        except asyncio.TimeoutError:
            logger.error("Shutdown timed out", timeout=self._shutdown_timeout)
        logger.info("Shutdown complete")

# Integrate with FastAPI lifespan
shutdown = GracefulShutdown()

@asynccontextmanager
async def lifespan(app: FastAPI):
    shutdown.install_signal_handlers()

    # Startup
    await db_pool.connect()
    app.state.redis = await redis.from_url(settings.redis_url)

    # Register cleanup in reverse order
    shutdown.register_cleanup(lambda: app.state.redis.aclose())
    shutdown.register_cleanup(engine.dispose)
    shutdown.register_cleanup(http_client.aclose)

    yield

    # FastAPI handles SIGTERM via its own mechanism; we also support direct call
    await shutdown.execute_shutdown()
```

---

## Connection Pooling Patterns

```python
# PostgreSQL via asyncpg (direct, no SQLAlchemy)
import asyncpg

pool: asyncpg.Pool | None = None

async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        max_inactive_connection_lifetime=300,   # close idle connections after 5min
        command_timeout=30,
        statement_cache_size=200,               # cache prepared statements
    )

async def get_conn() -> asyncpg.Connection:
    return await pool.acquire()

# Redis pool (via redis.asyncio)
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=5,
    retry_on_timeout=True,
)
redis_client = redis.Redis(connection_pool=redis_pool)

# SQLAlchemy pool tuning
engine = create_async_engine(
    settings.database_url,
    pool_size=20,            # persistent connections in pool
    max_overflow=10,         # extra connections allowed above pool_size
    pool_timeout=30,         # wait up to 30s for connection from pool
    pool_recycle=3600,       # recreate connections older than 1hr (avoids stale connections)
    pool_pre_ping=True,      # test connection before use (catches dropped connections)
    echo=False,
)
```

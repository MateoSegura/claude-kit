# Python Backend — Code Examples

Complete working patterns for common backend scenarios.

---

## Complete Async CRUD Service

```python
# services/user_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import User
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.exceptions import NotFoundError, ConflictError

class UserService:
    async def create(self, db: AsyncSession, data: UserCreate) -> User:
        existing = await db.execute(
            select(User.id).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email {data.email} already registered")

        user = User(**data.model_dump())
        db.add(user)
        await db.flush()   # assign ID without committing
        await db.refresh(user)
        return user

    async def get(self, db: AsyncSession, user_id: UUID) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def list(
        self, db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> tuple[list[User], int]:
        query = select(User).offset(skip).limit(limit)
        count_query = select(func.count(User.id))

        users_result, count_result = await asyncio.gather(
            db.execute(query),
            db.execute(count_query),
        )
        return list(users_result.scalars().all()), count_result.scalar_one()

    async def update(self, db: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await db.flush()
        await db.refresh(user)
        return user

    async def delete(self, db: AsyncSession, user_id: UUID) -> None:
        user = await self.get(db, user_id)
        await db.delete(user)

user_service = UserService()
```

---

## Async HTTP Client Service

```python
# clients/external_api.py
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger()

class ExternalAPIClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key, "Accept": "application/json"},
            timeout=httpx.Timeout(connect=3.0, read=timeout),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(3),
    )
    async def get_resource(self, resource_id: str) -> dict:
        try:
            resp = await self._client.get(f"/resources/{resource_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ResourceNotFoundError(resource_id) from e
            raise

    async def batch_fetch(self, ids: list[str], concurrency: int = 5) -> list[dict]:
        sem = asyncio.Semaphore(concurrency)
        async def fetch_one(rid: str) -> dict:
            async with sem:
                return await self.get_resource(rid)
        return await asyncio.gather(*[fetch_one(rid) for rid in ids])

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

---

## Lifespan Resource Management

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

from app.db import engine
from app.clients import ExternalAPIClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Database connection pool
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))   # verify connectivity

    # Redis pool
    app.state.redis = await redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )

    # External API client
    app.state.external_api = ExternalAPIClient(
        base_url=settings.external_api_url,
        api_key=settings.external_api_key,
    )

    yield

    # --- Shutdown ---
    await app.state.redis.aclose()
    await app.state.external_api.close()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

---

## Structured Logging Setup

```python
# app/logging.py
import logging
import structlog
from structlog.types import EventDict

def add_service_context(logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "my-service"
    event_dict["version"] = "1.0.0"
    return event_dict

def configure_logging(level: str = "INFO", json_logs: bool = True):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_service_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer() if json_logs
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

# Usage
logger = structlog.get_logger()
logger.info("User created", user_id=str(user.id), email=user.email)
logger.error("Payment failed", order_id=order_id, error=str(exc), exc_info=True)
```

---

## Caching Pattern with Redis

```python
# app/cache.py
import json
import hashlib
from functools import wraps
from typing import Any, Callable
import redis.asyncio as redis

class CacheClient:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def get(self, key: str) -> Any | None:
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self._redis.setex(key, ttl_seconds, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator: cache async function result in Redis."""
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, cache: CacheClient, **kwargs):
            cache_key = f"{key_prefix}:{fn.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            hit = await cache.get(cache_key)
            if hit is not None:
                return hit
            result = await fn(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

---

## Health Check Endpoint

```python
# app/health.py
from fastapi import APIRouter, Request
from sqlalchemy import text
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthStatus(BaseModel):
    status: str
    checks: dict[str, str]

@router.get("/health/live")
async def liveness() -> dict:
    """K8s liveness probe — always 200 if process is alive."""
    return {"status": "ok"}

@router.get("/health/ready", response_model=HealthStatus)
async def readiness(request: Request) -> HealthStatus:
    """K8s readiness probe — 200 only when all dependencies are ready."""
    checks: dict[str, str] = {}

    # Database check
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return HealthStatus(
        status="ok" if all_ok else "degraded",
        checks=checks,
    )
```

---

## Background Worker with asyncio.Queue

```python
# app/workers.py
import asyncio
from dataclasses import dataclass
from typing import Any
import structlog

logger = structlog.get_logger()

@dataclass
class Job:
    id: str
    type: str
    payload: dict[str, Any]

class WorkerPool:
    def __init__(self, num_workers: int = 4, queue_size: int = 1000):
        self.queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=queue_size)
        self.num_workers = num_workers
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i), name=f"worker-{i}")
            self._tasks.append(task)
        logger.info("Worker pool started", workers=self.num_workers)

    async def stop(self):
        # Signal workers to stop
        for _ in self._tasks:
            await self.queue.put(None)   # sentinel value
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Worker pool stopped")

    async def submit(self, job: Job) -> None:
        await self.queue.put(job)

    async def _worker(self, worker_id: int) -> None:
        while True:
            item = await self.queue.get()
            if item is None:  # sentinel
                self.queue.task_done()
                break
            try:
                await self._process(item)
            except Exception:
                logger.exception("Job failed", job_id=item.id, worker=worker_id)
            finally:
                self.queue.task_done()

    async def _process(self, job: Job) -> None:
        logger.info("Processing job", job_id=job.id, type=job.type)
        # Dispatch by type
        handler = JOB_HANDLERS.get(job.type)
        if handler:
            await handler(job.payload)
        else:
            logger.warning("Unknown job type", type=job.type)
```

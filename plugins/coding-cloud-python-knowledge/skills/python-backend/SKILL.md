---
name: coding-cloud-python-knowledge:python-backend
description: "Core Python backend patterns covering asyncio event loop, async/await concurrency, type hints, FastAPI/Starlette, httpx, Pydantic v2, dependency injection, and middleware. Load when writing or reviewing Python async web services, REST APIs, or backend application code."
---

# Python Backend — Quick Reference

Modern Python backend stack: FastAPI 0.100+, Pydantic v2, SQLAlchemy 2.0 async, httpx, Python 3.11+.

## Additional resources

- [api-reference.md](api-reference.md) — FastAPI route patterns, Pydantic models, middleware, error handling, dependency injection examples
- [examples.md](examples.md) — Complete working code: async CRUD service, background tasks, streaming, websockets

---

## asyncio Quick Reference

```python
import asyncio

# Run top-level coroutine (Python 3.7+)
asyncio.run(main())

# Concurrent execution — gather returns results in order
results = await asyncio.gather(fetch_a(), fetch_b(), fetch_c())

# Fire-and-forget background task
task = asyncio.create_task(background_job())

# Timeout
async with asyncio.timeout(5.0):   # Python 3.11+
    result = await slow_operation()

# asyncio.wait_for (pre-3.11 fallback)
result = await asyncio.wait_for(slow_operation(), timeout=5.0)

# Queue-based producer/consumer
queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
await queue.put(item)
item = await queue.get()
queue.task_done()
await queue.join()
```

**Rules:**
- Use `async def` for any function with `await` inside it
- Never call blocking I/O (`time.sleep`, `requests.get`) from an async function — use `asyncio.to_thread()` or `run_in_executor`
- Each asyncio event loop runs in one OS thread; use `asyncio.run()` once at the entry point

---

## Type Hints Quick Reference

```python
from typing import Annotated, Any
from collections.abc import AsyncGenerator, Sequence

# Annotated — attach metadata/validators to types
UserId = Annotated[int, Field(gt=0)]

# Generic repository
from typing import Generic, TypeVar
T = TypeVar("T")

class Repository(Generic[T]):
    async def get(self, id: int) -> T | None: ...
    async def list(self) -> Sequence[T]: ...

# Callable signatures
Handler = Callable[[Request], Awaitable[Response]]

# ParamSpec for decorator typing (Python 3.10+)
from typing import ParamSpec
P = ParamSpec("P")
```

---

## Pydantic v2 Quick Reference

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings

class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()

    @model_validator(mode="after")
    def check_age(self) -> "UserCreate":
        if self.age is not None and self.age < 0:
            raise ValueError("age must be non-negative")
        return self

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
```

**v2 changes from v1:**
- `model_config = ConfigDict(...)` replaces inner `class Config`
- `@field_validator` replaces `@validator`; add `@classmethod`
- `model_validator(mode="after")` replaces `@root_validator`
- `X | None` preferred over `Optional[X]`
- `model.model_dump()` replaces `model.dict()`
- `model.model_validate(data)` replaces `model.parse_obj(data)`

---

## FastAPI Quick Reference

```python
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_pool.connect()
    yield
    # Shutdown
    await db_pool.disconnect()

app = FastAPI(title="My Service", version="1.0.0", lifespan=lifespan)

# Router with prefix
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse, status_code=200)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    user = await user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
```

**Dependency injection rules:**
- Use `Annotated[Type, Depends(fn)]` (preferred) or `param: Type = Depends(fn)`
- Async deps stay async; sync deps run in thread pool automatically
- Yield deps use `try/finally` for cleanup (replaces `__exit__` pattern)
- Cache deps per-request with `use_cache=True` (default)

---

## httpx Quick Reference

```python
import httpx
from typing import Any

# Shared async client (reuse across requests — important for connection pooling)
client = httpx.AsyncClient(
    base_url="https://api.example.com",
    timeout=httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=1.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    headers={"User-Agent": "my-service/1.0"},
)

async def fetch_user(user_id: int) -> dict[str, Any]:
    response = await client.get(f"/users/{user_id}")
    response.raise_for_status()   # raises httpx.HTTPStatusError on 4xx/5xx
    return response.json()

# Always close on shutdown
await client.aclose()
```

---

## Middleware Pattern

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response

# Starlette BaseHTTPMiddleware (more structured)
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)

app.add_middleware(AuthMiddleware)
```

---

## Error Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        self.message = message
        self.code = code
        self.status = status

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": exc.code, "message": exc.message},
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "internal_error"})
```

# Python Backend — API Reference

Detailed patterns for FastAPI, Pydantic v2, async SQLAlchemy, and related APIs.

---

## FastAPI — Complete Route Patterns

### Path, Query, Body Parameters

```python
from fastapi import APIRouter, Query, Path, Body, Header, Cookie
from typing import Annotated

router = APIRouter()

@router.get("/items/{item_id}")
async def read_item(
    # Path parameter with validation
    item_id: Annotated[int, Path(title="Item ID", ge=1)],
    # Query parameters
    q: Annotated[str | None, Query(max_length=50)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    # Header
    x_token: Annotated[str | None, Header()] = None,
) -> ItemResponse:
    ...

@router.post("/items", status_code=201)
async def create_item(
    # Request body
    item: Annotated[ItemCreate, Body(embed=False)],
    # Multiple bodies: embed=True adds field name as key
    metadata: Annotated[dict, Body(embed=True)] = {},
) -> ItemResponse:
    ...
```

### Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/send-email")
async def send_email(
    email: EmailRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    background_tasks.add_task(send_email_task, email.to, email.subject, email.body)
    return {"message": "Email queued"}

async def send_email_task(to: str, subject: str, body: str) -> None:
    # Runs after response is returned to client
    await smtp_client.send(to=to, subject=subject, body=body)
```

### Streaming Responses

```python
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/stream/{job_id}")
async def stream_results(job_id: str):
    async def event_generator():
        async for chunk in result_stream.iter(job_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### WebSockets

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("Client %s disconnected", client_id)
```

---

## Pydantic v2 — Model Patterns

### Request/Response Models

```python
from pydantic import BaseModel, Field, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_camel
from datetime import datetime
from uuid import UUID

class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0)
    tags: list[str] = Field(default_factory=list)

class ItemCreate(ItemBase):
    model_config = ConfigDict(extra="forbid")

class ItemUpdate(BaseModel):
    # All fields optional for PATCH
    name: str | None = Field(None, min_length=1, max_length=200)
    price: float | None = Field(None, gt=0)
    tags: list[str] | None = None

class ItemResponse(ItemBase):
    model_config = ConfigDict(
        from_attributes=True,                    # ORM mode (replaces orm_mode=True)
        alias_generator=to_camel,                # JSON uses camelCase
        populate_by_name=True,                   # also accept snake_case
    )
    id: UUID
    created_at: datetime
    updated_at: datetime
```

### Discriminated Unions

```python
from typing import Literal
from pydantic import BaseModel

class CatEvent(BaseModel):
    type: Literal["cat"]
    meow_volume: int

class DogEvent(BaseModel):
    type: Literal["dog"]
    bark_intensity: str

Animal = Annotated[CatEvent | DogEvent, Field(discriminator="type")]

class EventEnvelope(BaseModel):
    event: Animal

# FastAPI handles discriminated unions in request bodies automatically
```

### Custom Types

```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class PositiveDecimal:
    """Custom type: decimal string that must be > 0."""
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        from decimal import Decimal, InvalidOperation
        try:
            d = Decimal(str(v))
        except InvalidOperation:
            raise ValueError(f"Invalid decimal: {v!r}")
        if d <= 0:
            raise ValueError("Must be positive")
        return d
```

---

## Dependency Injection — Full Patterns

### Database Session Dependency

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,   # verify connections before use
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # prevent lazy-load errors after commit
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Layered Dependencies

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    database_url: str
    model_config = ConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Inject settings
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = verify_token(token, settings.secret_key)
    user = await user_repo.get(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# Reuse auth dependency
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me")
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
```

### Class-Based Dependencies

```python
class Paginator:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=200)] = 20,
    ):
        self.skip = skip
        self.limit = limit

@router.get("/items")
async def list_items(
    pagination: Annotated[Paginator, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ItemResponse]:
    return await item_service.list(db, skip=pagination.skip, limit=pagination.limit)
```

---

## Middleware — Production Patterns

### Request ID Middleware

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

logger = structlog.get_logger()

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,   # e.g. ["https://app.example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)
```

### Rate Limiting Middleware (via slowapi)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/limited")
@limiter.limit("10/minute")
async def limited_endpoint(request: Request) -> dict:
    return {"status": "ok"}
```

---

## Error Handling — Complete Patterns

### Structured Error Response

```python
from pydantic import BaseModel
from fastapi import Request
from fastapi.exceptions import RequestValidationError

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None

class ErrorResponse(BaseModel):
    errors: list[ErrorDetail]
    request_id: str | None = None

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        ErrorDetail(
            code="validation_error",
            message=str(err["msg"]),
            field=".".join(str(loc) for loc in err["loc"]),
        )
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(errors=errors).model_dump(),
    )
```

### Domain Exception Hierarchy

```python
class DomainError(Exception):
    status_code: int = 400
    error_code: str = "domain_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class NotFoundError(DomainError):
    status_code = 404
    error_code = "not_found"

class ConflictError(DomainError):
    status_code = 409
    error_code = "conflict"

class AuthorizationError(DomainError):
    status_code = 403
    error_code = "forbidden"

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
    )
```

---

## Async SQLAlchemy 2.0 Patterns

### Model Definition

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from datetime import datetime
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    items: Mapped[list["Item"]] = relationship(back_populates="owner", lazy="selectin")
```

### Async Queries

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def list_users(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

async def update_user(db: AsyncSession, user_id: UUID, data: dict) -> int:
    result = await db.execute(
        update(User).where(User.id == user_id).values(**data).returning(User.id)
    )
    await db.flush()
    return result.scalar_one_or_none()
```

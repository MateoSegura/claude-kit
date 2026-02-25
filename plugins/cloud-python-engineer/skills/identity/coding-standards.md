# Coding Standards -- Cloud-Native Python Backend

This document is the detailed style guide for all Python code produced by the cloud-python-engineer plugin. It supplements the summary in SKILL.md with exhaustive rules and examples.

## File Organization

### Project Layout (per service)

```
service-name/
├── pyproject.toml            # uv-managed, ruff config, mypy config
├── uv.lock                   # Deterministic lockfile (committed)
├── alembic.ini               # Alembic configuration
├── alembic/
│   └── versions/             # Migration files
├── src/
│   └── service_name/
│       ├── __init__.py
│       ├── main.py           # Application factory, lifespan
│       ├── config.py         # pydantic-settings BaseSettings
│       ├── deps.py           # Dependency injection factories
│       ├── routers/          # FastAPI route modules
│       │   ├── __init__.py
│       │   └── health.py
│       ├── schemas/          # Pydantic v2 request/response models
│       │   ├── __init__.py
│       │   └── events.py
│       ├── models/           # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   └── base.py       # DeclarativeBase subclass
│       ├── repositories/     # Database access layer
│       │   └── __init__.py
│       ├── services/         # Domain / business logic
│       │   └── __init__.py
│       ├── workers/          # Async message consumers
│       │   └── __init__.py
│       ├── proto/            # .proto files and generated stubs
│       │   └── __init__.py
│       └── telemetry.py      # OpenTelemetry bootstrap
├── tests/                    # Test suite (tester plugin's domain)
├── Dockerfile
└── k8s/
    ├── deployment.yaml
    └── service.yaml
```

### Module Header

Every `.py` file starts with:

```python
"""One-line module docstring describing purpose."""

from __future__ import annotations

# stdlib imports
# third-party imports
# local imports
```

`from __future__ import annotations` enables PEP 604 union syntax (`X | None`) and deferred evaluation for forward references. Required in every file, no exceptions.

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Module | `snake_case` | `user_repository.py` |
| Package | `snake_case` | `service_name/` |
| Class | `PascalCase` | `UserRepository` |
| Function / method | `snake_case` | `get_user_by_id` |
| Variable | `snake_case` | `current_user` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Type alias | `PascalCase` | `UserId = NewType("UserId", UUID)` |
| Protocol | `PascalCase` + descriptive | `HasId`, `Cacheable` |
| Private | leading underscore | `_parse_token` |
| Protected (subclass API) | leading underscore | `_validate_state` |
| Environment variable | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |
| Pydantic model | `PascalCase` + suffix | `CreateUserRequest`, `UserResponse` |
| SQLAlchemy model | `PascalCase` | `User`, `OrderItem` |

### Pydantic Model Naming

- Request bodies: `<Action><Entity>Request` (e.g., `CreateOrderRequest`)
- Response bodies: `<Entity>Response` (e.g., `OrderResponse`)
- Event payloads: `<Entity><Event>Event` (e.g., `OrderCreatedEvent`)
- Config: `<Service>Settings` (e.g., `PaymentServiceSettings`)
- Internal DTOs: `<Entity>Data` (e.g., `UserData`)

## Type Annotation Rules

### Required everywhere

```python
# CORRECT -- full annotations
async def get_user(user_id: UUID, session: AsyncSession) -> UserResponse:
    ...

# WRONG -- missing return type
async def get_user(user_id: UUID, session: AsyncSession):
    ...

# WRONG -- missing parameter type
async def get_user(user_id, session: AsyncSession) -> UserResponse:
    ...
```

### Use modern syntax (Python 3.12+)

```python
# CORRECT
def process(items: list[str]) -> dict[str, int]: ...
def maybe(value: str | None) -> str: ...
type UserId = NewType("UserId", UUID)

# WRONG -- legacy typing imports
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]: ...
def maybe(value: Optional[str]) -> str: ...
```

### Generic classes

```python
from collections.abc import Sequence, Mapping, AsyncIterator

# CORRECT -- use collections.abc
def filter_active(users: Sequence[User]) -> list[User]: ...
async def stream_events() -> AsyncIterator[Event]: ...

# WRONG -- typing module generics
from typing import Sequence, List
```

### TypeVar and Protocol

```python
from typing import TypeVar, Protocol

T = TypeVar("T")

class Repository(Protocol[T]):
    async def get_by_id(self, entity_id: UUID) -> T | None: ...
    async def save(self, entity: T) -> T: ...
```

## Docstring Standards

Use Google-style docstrings. Type info lives in annotations, not in the docstring.

```python
async def create_order(
    request: CreateOrderRequest,
    repo: OrderRepository,
    publisher: EventPublisher,
) -> OrderResponse:
    """Create a new order and publish the creation event.

    Validates inventory availability before persisting. If inventory
    is insufficient, raises InsufficientInventoryError without
    modifying any state.

    Args:
        request: Validated order creation payload.
        repo: Order persistence layer.
        publisher: Event bus for domain events.

    Returns:
        The created order with assigned ID and timestamps.

    Raises:
        InsufficientInventoryError: When requested quantity exceeds stock.
        DuplicateOrderError: When idempotency key already exists.
    """
```

Rules:
- One-line summary in imperative mood, ending with a period
- Blank line between summary and extended description
- `Args:` section lists each parameter with a one-line description (no types -- they are in the signature)
- `Returns:` describes the return value semantically
- `Raises:` lists every exception the function intentionally raises
- Skip `Args:` for `self` and `cls`

## Error Handling

### Exception hierarchy

```python
class ServiceError(Exception):
    """Base exception for this service."""

class NotFoundError(ServiceError):
    """Requested entity does not exist."""

class ConflictError(ServiceError):
    """Operation conflicts with current state."""

class ValidationError(ServiceError):
    """Domain validation failed (not Pydantic validation)."""
```

### Rules

1. Never catch `Exception` or `BaseException` without re-raising. Catch specific exceptions.
2. Use `raise ... from err` to preserve exception chains.
3. FastAPI exception handlers map domain exceptions to HTTP status codes in a single `exception_handlers.py`.
4. Log at `error` level when catching unexpected exceptions; log at `warning` for expected/recoverable ones.
5. Never return error information as a dict or tuple -- raise an exception.

```python
# CORRECT
try:
    user = await repo.get_by_id(user_id)
except RecordNotFoundError as err:
    raise NotFoundError(f"User {user_id} not found") from err

# WRONG -- bare except
try:
    user = await repo.get_by_id(user_id)
except:
    return None

# WRONG -- returning error dict
async def get_user(user_id: UUID) -> dict:
    user = await repo.get_by_id(user_id)
    if user is None:
        return {"error": "not found"}  # Never do this
```

## FastAPI Patterns

### Router structure

```python
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
)
async def create_order(
    request: CreateOrderRequest,
    repo: OrderRepository = Depends(get_order_repo),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> OrderResponse:
    """Create order and publish domain event."""
    order = await repo.create(request)
    await publisher.publish(OrderCreatedEvent.from_order(order))
    return OrderResponse.model_validate(order)
```

### Dependency injection

```python
# deps.py
from collections.abc import AsyncGenerator

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def get_order_repo(
    session: AsyncSession = Depends(get_db_session),
) -> OrderRepository:
    return OrderRepository(session)
```

### Application factory with lifespan

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await init_telemetry()
    await init_db_pool()
    yield
    # Shutdown
    await close_db_pool()

def create_app() -> FastAPI:
    app = FastAPI(title="Order Service", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(order_router)
    return app
```

## SQLAlchemy 2.0 Async Patterns

### Model definition

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### Repository pattern

```python
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserData | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return UserData.model_validate(row) if row else None
```

## Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# In a handler
async def create_order(request: CreateOrderRequest) -> OrderResponse:
    logger.info("order_created", order_id=str(order.id), customer_id=str(request.customer_id))
```

Log events use `snake_case` event names. Bind structured fields as keyword arguments. Never format strings manually for log messages.

## ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D203",    # one-blank-line-before-class (conflicts with D211)
    "D213",    # multi-line-summary-second-line (conflicts with D212)
    "COM812",  # trailing comma (conflicts with formatter)
    "ISC001",  # single-line implicit string concat (conflicts with formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "D"]  # allow assert, skip docstrings in tests
"alembic/**/*.py" = ["D", "INP001"]  # migrations don't need docstrings
```

## mypy Configuration

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]
warn_return_any = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = ["grpc.*", "google.protobuf.*"]
ignore_missing_imports = true
```

# Design Patterns — Python Anti-Patterns

Python-specific structural mistakes that hurt maintainability, performance, and testability. For language-agnostic anti-patterns, see `core-architecture:design-patterns`.

---

## Anti-Pattern 1: Fat Service / God Class

**What developers do wrong:** Putting all business logic, DB access, HTTP calls, and validation into a single service class.

```python
# BAD: UserService does everything — 1000+ line class
class UserService:
    def __init__(self, db: AsyncSession, http: httpx.AsyncClient, cache: Redis, email: EmailClient):
        self.db = db
        self.http = http
        self.cache = cache
        self.email = email

    async def create_user(self, data: dict) -> dict:
        # Validation inline
        if not data.get("email") or "@" not in data["email"]:
            raise ValueError("Bad email")
        # Direct DB query
        existing = await self.db.execute(select(User).where(User.email == data["email"]))
        if existing.scalar_one_or_none():
            raise ConflictError("Email taken")
        # Create
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        # Email inline
        await self.http.post("https://mail-api.com/send", json={"to": data["email"], "template": "welcome"})
        # Cache inline
        await self.cache.setex(f"user:{user.id}", 300, json.dumps({"id": str(user.id)}))
        return {"id": str(user.id)}
```

**Why it fails:** Impossible to test in isolation (must mock 4+ dependencies). Cannot swap email provider. Cannot change caching without touching business logic. Grows unboundedly.

```python
# GOOD: separate concerns into domain-focused classes
class UserRepository:
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None: ...
    async def add(self, db: AsyncSession, user: User) -> User: ...

class UserService:
    def __init__(self, repo: UserRepository, event_bus: EventBus):
        self._repo = repo
        self._events = event_bus

    async def create(self, uow: UnitOfWork, data: UserCreate) -> User:
        existing = await self._repo.get_by_email(uow.session, data.email)
        if existing:
            raise ConflictError("Email already registered")
        user = User(email=data.email, name=data.name)
        await self._repo.add(uow.session, user)
        await self._events.publish(UserCreated(user_id=user.id, email=user.email))
        return user

# Email sent by event handler — decoupled from creation
@event_bus.on(UserCreated)
async def send_welcome_email(event: UserCreated) -> None:
    await email_service.send_welcome(event.email)
```

---

## Anti-Pattern 2: Anemic Domain Model

**What developers do wrong:** Domain objects are pure data bags with no behavior. All logic lives in service classes.

```python
# BAD: Order is just a dict with a class name
class Order:
    def __init__(self):
        self.id = None
        self.status = None
        self.items = []
        self.total = 0

# Service contains all logic — violates tell-don't-ask
class OrderService:
    async def ship_order(self, order: Order) -> None:
        if order.status != "confirmed":
            raise ValueError("Order not confirmed")
        if order.total <= 0:
            raise ValueError("Invalid total")
        order.status = "shipped"
        order.shipped_at = datetime.utcnow()
```

**Why it fails:** Business rules are scattered across services. Domain objects cannot enforce their own invariants. Adding a new rule requires finding all services that touch `Order.status`.

```python
# GOOD: rich domain model with encapsulated behavior
class Order:
    def __init__(self, user_id: UUID, items: list[OrderItem]):
        self.id = uuid4()
        self.user_id = user_id
        self.items = items
        self.status = OrderStatus.PENDING
        self.total = sum(item.price * item.quantity for item in items)
        self._events: list[DomainEvent] = []

    def confirm(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise InvalidStateError(f"Cannot confirm order in {self.status} state")
        self.status = OrderStatus.CONFIRMED
        self._events.append(OrderConfirmed(order_id=self.id))

    def ship(self) -> None:
        if self.status != OrderStatus.CONFIRMED:
            raise InvalidStateError(f"Cannot ship order in {self.status} state")
        self.status = OrderStatus.SHIPPED
        self.shipped_at = datetime.utcnow()
        self._events.append(OrderShipped(order_id=self.id))

    def collect_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events

# Service calls domain methods — no logic leakage
async def ship_order(order_id: UUID, uow: UnitOfWork) -> None:
    order = await uow.orders.get(order_id)
    order.ship()   # domain enforces rules
    events = order.collect_events()
    for event in events:
        await event_bus.publish(event)
```

---

## Anti-Pattern 3: Sync I/O in Async Context

**What developers do wrong:** Calling synchronous blocking functions inside `async def` without `asyncio.to_thread`.

```python
# BAD: time.sleep and requests.get block the event loop
async def send_report(report_id: str) -> None:
    # Generates report synchronously — blocks all other requests for 2+ seconds
    report = generate_pdf_report(report_id)   # pure CPU, 2s
    # Sends via requests (sync) — blocks event loop
    requests.post("https://notify.api/send", json={"file": report})
    time.sleep(1)   # NEVER do this
```

**Why it fails:** The entire asyncio event loop is blocked for the duration. No other requests can be processed. Under load, this causes cascading timeouts.

```python
# GOOD: use asyncio.to_thread for CPU-bound or legacy sync code
async def send_report(report_id: str) -> None:
    # Offload CPU-bound work to thread pool
    report = await asyncio.to_thread(generate_pdf_report, report_id)

    # Use async HTTP client
    async with httpx.AsyncClient() as client:
        await client.post("https://notify.api/send", json={"file": report})

    # Use asyncio.sleep (yields control to event loop)
    await asyncio.sleep(1)

# For truly CPU-intensive work, consider ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=4)

async def heavy_computation(data: bytes) -> bytes:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, compute_intensive_function, data)
```

---

## Anti-Pattern 4: Missing __aenter__/__aexit__ on Clients

**What developers do wrong:** Creating async clients that hold resources but never defining cleanup, leading to connection leaks.

```python
# BAD: client created but never explicitly closed
class PaymentClient:
    def __init__(self, base_url: str):
        self._http = httpx.AsyncClient(base_url=base_url)

    async def charge(self, amount: int) -> dict:
        resp = await self._http.post("/charge", json={"amount": amount})
        return resp.json()
    # No close() — connections accumulate until GC
```

**Why it fails:** httpx.AsyncClient holds a connection pool. Without closing, file descriptors and sockets accumulate. Under load, process hits OS file descriptor limit.

```python
# GOOD: implement context manager protocol + explicit close
class PaymentClient:
    def __init__(self, base_url: str):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            limits=httpx.Limits(max_connections=20),
        )

    async def charge(self, amount: int) -> dict:
        resp = await self._http.post("/charge", json={"amount": amount})
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "PaymentClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

# Register in lifespan for shared client
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.payment = PaymentClient(base_url=settings.payment_url)
    yield
    await app.state.payment.close()
```

---

## Anti-Pattern 5: Using mutable default arguments

**What developers do wrong:** Defining Pydantic models or dataclasses with mutable default values.

```python
# BAD: all instances share the same list object
class OrderCreate(BaseModel):
    items: list[OrderItem] = []   # shared mutable default!
    tags: dict[str, str] = {}     # same problem
```

**Why it fails:** Python evaluates default arguments once at class definition time. All instances share the same list object. Modifying one instance's items modifies all instances.

```python
# GOOD: use Field(default_factory=...) for mutable defaults
from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    items: list[OrderItem] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

# Also applies to dataclasses
from dataclasses import dataclass, field

@dataclass
class Config:
    allowed_origins: list[str] = field(default_factory=list)
    feature_flags: dict[str, bool] = field(default_factory=dict)
```

---

## Anti-Pattern 6: Not Using expire_on_commit=False

**What developers do wrong:** Using SQLAlchemy's default `expire_on_commit=True` with lazy-loading in async context.

```python
# BAD: accessing attributes after commit raises MissingGreenlet or DetachedInstanceError
AsyncSessionLocal = async_sessionmaker(engine)   # expire_on_commit=True by default

async def create_user(data: dict) -> UserResponse:
    async with AsyncSessionLocal() as db:
        user = User(**data)
        db.add(user)
        await db.commit()
        # After commit, SQLAlchemy expires all attributes
        # Accessing user.email here triggers lazy I/O — fails in async!
        return UserResponse(id=user.id, email=user.email)  # MissingGreenlet error!
```

**Why it fails:** SQLAlchemy expires all ORM attributes after commit by default. In sync mode, accessing expired attributes triggers implicit lazy SQL. In async mode, implicit lazy I/O is not possible — raises `MissingGreenlet`.

```python
# GOOD: disable expire_on_commit for async sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # attributes remain accessible after commit
)

async def create_user(data: dict) -> UserResponse:
    async with AsyncSessionLocal() as db:
        user = User(**data)
        db.add(user)
        await db.commit()
        await db.refresh(user)   # explicitly refresh to get DB-generated values
        return UserResponse(id=user.id, email=user.email)  # works correctly
```

---

## Anti-Pattern 7: Global State Mutation

**What developers do wrong:** Storing per-request state in module-level globals.

```python
# BAD: global state shared across requests — race conditions
current_user: User | None = None
request_id: str = ""

@router.get("/orders")
async def list_orders() -> list[Order]:
    global current_user, request_id
    current_user = await get_user(request.headers["Authorization"])
    request_id = request.headers.get("X-Request-ID", "")
    # Another concurrent request overwrites current_user here!
    return await order_service.list_for_user(current_user.id)
```

**Why it fails:** Concurrent requests share the same module globals. Request A sets `current_user`, request B overwrites it before request A uses it. Results in wrong user data or authorization bypass.

```python
# GOOD: use contextvars for per-coroutine state
from contextvars import ContextVar

_current_user: ContextVar[User | None] = ContextVar("current_user", default=None)
_request_id: ContextVar[str] = ContextVar("request_id", default="")

def get_current_user_ctx() -> User | None:
    return _current_user.get()

# Set in middleware — each coroutine has its own copy
class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = await authenticate(request)
        _current_user.set(user)
        _request_id.set(request.headers.get("X-Request-ID", str(uuid4())))
        return await call_next(request)

# Or use structlog.contextvars (built on top of contextvars)
with structlog.contextvars.bound_contextvars(request_id=request_id, user_id=str(user.id)):
    response = await call_next(request)
```

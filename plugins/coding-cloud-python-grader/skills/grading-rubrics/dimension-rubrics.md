# Dimension Rubrics — Detailed Grading Criteria

Per-dimension rubric with checks, expected patterns, anti-patterns, and scoring impact for each of the 8 grading dimensions.

---

## Dimension 1: async-correctness (Weight: 20%)

### Purpose
Python's asyncio model is cooperative: all coroutines share a single OS thread. A single blocking call stalls every concurrent request. This dimension catches misuse that degrades throughput or causes deadlocks.

### Expected Patterns

**Correct async I/O:**
```python
# Good — non-blocking DB call
async def get_user(user_id: int) -> User:
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    return User(**row)

# Good — parallel fan-out
results = await asyncio.gather(
    fetch_profile(user_id),
    fetch_permissions(user_id),
    fetch_preferences(user_id),
)
```

**Correct task lifecycle:**
```python
# Good — task tracked and cancelled on shutdown
class WorkerManager:
    def __init__(self):
        self._tasks: set[asyncio.Task] = set()

    def spawn(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self):
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

**Correct shared-state access:**
```python
# Good — lock protects state across await points
_lock = asyncio.Lock()
_cache: dict[str, str] = {}

async def get_cached(key: str) -> str:
    async with _lock:
        if key not in _cache:
            _cache[key] = await fetch(key)
        return _cache[key]
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Example | Severity | Scoring Impact |
|---|---|---|---|
| Blocking sleep | `time.sleep(1)` inside `async def` | Critical | -25 pts |
| Synchronous HTTP client | `requests.get(url)` inside `async def` | Critical | -25 pts |
| Synchronous file I/O (large files) | `open(path).read()` on large payloads | High | -15 pts |
| Unawaited coroutine | `send_email(user)` without `await` | Critical | -25 pts |
| Fire-and-forget task without reference | `asyncio.create_task(work())` — result discarded | High | -15 pts |
| `asyncio.run()` inside running loop | Nested event loop call | Critical | -25 pts |
| Sequential awaits for independent I/O | Two `await fetch()` that could be `gather()` | Medium | -8 pts |
| `asyncio.Lock` with threading.Lock | Using wrong lock primitive | Critical | -25 pts |
| Shared mutable state without lock | Dict modified across `await` points | High | -15 pts |
| Thread pool misuse | `loop.run_in_executor` for async-native operation | Low | -3 pts |

### Checks to Perform

1. Search for `time.sleep` in async functions.
2. Search for `import requests` and verify it is not called inside `async def` bodies.
3. Search for `asyncio.create_task` and verify results are assigned to variables.
4. Search for `asyncio.run(` and verify it is only called at the top-level entry point.
5. Identify sequential `await` calls on independent resources — flag as Medium if they could be `gather()`.
6. Check that `threading.Lock()` is not used in async code (use `asyncio.Lock()` instead).

---

## Dimension 2: type-safety (Weight: 15%)

### Purpose
Type annotations enable static analysis (mypy, pyright), improve IDE support, and serve as machine-checkable documentation. In cloud microservices, untyped boundaries cause runtime errors that are hard to trace across service calls.

### Expected Patterns

**Full annotation coverage:**
```python
from typing import Optional
from pydantic import BaseModel

class CreateOrderRequest(BaseModel):
    user_id: int
    items: list[str]
    discount_code: Optional[str] = None

async def create_order(request: CreateOrderRequest) -> OrderResponse:
    ...
```

**No bare Any without justification:**
```python
# Bad
def process(data: Any) -> Any: ...

# Good — justified Any with comment
def process(data: Any) -> dict[str, Any]:  # third-party SDK returns untyped dict
    ...
```

**Pydantic for config and validated I/O:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_url: str
    redis_url: str
    max_connections: int = 10

    class Config:
        env_file = ".env"
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| Public function with no annotations | High | -15 pts per function (cap at 3) |
| `# type: ignore` without explanation comment | Medium | -8 pts |
| Bare `Any` in a Pydantic model field | High | -15 pts |
| Missing `response_model` on FastAPI route | Medium | -8 pts (overlaps api-contracts) |
| `dict` used instead of TypedDict or Pydantic for structured data | Medium | -8 pts |
| `Optional` used without `None` default in Pydantic | Low | -3 pts |
| Missing return type on async def | Medium | -8 pts |
| `cast()` used to hide type errors rather than fix them | Medium | -8 pts |

### Checks to Perform

1. Scan all `def` and `async def` for missing parameter or return type annotations.
2. Search for `Any` in non-test code and verify it has a justification comment.
3. Verify all FastAPI route handlers declare `response_model`.
4. Check that `# type: ignore` comments include an explanation.
5. Verify `pydantic` or `pydantic_settings` used for settings/config (not raw dict).

---

## Dimension 3: security (Weight: 20%)

### Purpose
Cloud services are exposed surfaces. Security findings in this dimension can result in data breach, credential theft, or service compromise. Aligned to OWASP Top 10 2025.

### Expected Patterns

**Parameterized queries:**
```python
# Good — parameterized
await conn.execute(
    "INSERT INTO users (name, email) VALUES ($1, $2)",
    name, email
)

# Good — ORM with typed model
user = await User.create(name=name, email=email)
```

**Secrets from environment only:**
```python
# Good — required env var, no plaintext default
db_password = os.environ["DATABASE_PASSWORD"]

# Good — pydantic-settings validation
class Settings(BaseSettings):
    db_password: SecretStr  # type: SecretStr prevents accidental logging
```

**TLS verification enforced:**
```python
# Good
async with aiohttp.ClientSession() as session:
    async with session.get(url, ssl=True) as resp:
        data = await resp.json()
```

### Anti-Patterns and Their Severity

| Anti-Pattern | OWASP Category | Severity | Scoring Impact |
|---|---|---|---|
| Hardcoded secret/token/password in source | A02:Cryptographic Failures | Critical | -25 pts |
| SQL via f-string or `%` interpolation | A03:Injection | Critical | -25 pts |
| `os.system()` or `subprocess` with user input | A03:Injection | Critical | -25 pts |
| `ssl=False` or `verify=False` on outbound HTTP | A02:Cryptographic Failures | High | -15 pts |
| `os.environ.get("SECRET", "default-value")` with plaintext default | A02:Cryptographic Failures | High | -15 pts |
| Secret in log output | A09:Security Logging Failures | High | -15 pts |
| Path traversal: `open(user_input)` without validation | A01:Broken Access Control | Critical | -25 pts |
| Pickle deserialization of untrusted data | A08:Software and Data Integrity | Critical | -25 pts |
| CORS `allow_origins=["*"]` with credentials | A01:Broken Access Control | High | -15 pts |
| Unvalidated redirect | A01:Broken Access Control | Medium | -8 pts |
| `DEBUG=True` in production config | A05:Security Misconfiguration | High | -15 pts |
| Overly broad exception catch hiding security errors | A09:Security Logging Failures | Medium | -8 pts |

### Checks to Perform

1. Search for string patterns: `password =`, `secret =`, `api_key =`, `token =` assigned to string literals.
2. Search for f-string SQL: `f"SELECT ... {user_input}"`.
3. Search for `subprocess.run`, `os.system`, `eval(`, `exec(` with variable input.
4. Search for `verify=False`, `ssl=False`, `check_hostname=False`.
5. Search for `os.environ.get("", "` with a non-empty default for secrets.
6. Check `logging` calls for accidental inclusion of password, token, or key variables.

---

## Dimension 4: observability (Weight: 10%)

### Purpose
In distributed cloud systems, logs and traces are the primary diagnostic tools. Poor observability means incidents take longer to detect and resolve. This dimension ensures the service is "debuggable in production."

### Expected Patterns

**Structured logging with correlation:**
```python
import structlog

log = structlog.get_logger()

async def handle_request(request_id: str, user_id: int):
    log = log.bind(request_id=request_id, user_id=user_id)
    log.info("processing_request", action="start")
    try:
        result = await process(user_id)
        log.info("processing_request", action="complete", result_count=len(result))
    except Exception as exc:
        log.error("processing_request", action="failed", error=str(exc))
        raise
```

**OpenTelemetry span creation:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def call_payment_service(order_id: str) -> PaymentResult:
    with tracer.start_as_current_span("payment_service.charge") as span:
        span.set_attribute("order.id", order_id)
        result = await payment_client.charge(order_id)
        span.set_attribute("payment.status", result.status)
    return result
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| Log statements are bare strings with no structured fields | High | -15 pts |
| No correlation/trace ID in log records | High | -15 pts |
| PII (email, name, SSN) in log output | Critical | -25 pts (also security overlap) |
| Token or secret value in log output | Critical | -25 pts (also security overlap) |
| External I/O with no span or log boundary | Medium | -8 pts |
| `print()` used instead of logger | Medium | -8 pts |
| ERROR level used for expected client errors (400s) | Low | -3 pts |
| No health check endpoint for readiness | Medium | -8 pts (overlaps k8s-hygiene) |
| Exception swallowed without log | High | -15 pts |
| Log level hardcoded to DEBUG in production config | Medium | -8 pts |

### Checks to Perform

1. Search for `print(` in non-test, non-script code.
2. Verify logger is bound with `request_id`, `trace_id`, or equivalent before log calls in request handlers.
3. Search for external HTTP calls and DB calls without enclosing spans.
4. Check for PII field names (`email`, `phone`, `ssn`, `password`) in log format strings.
5. Verify exception handlers always log the exception before re-raising or returning an error response.

---

## Dimension 5: api-contracts (Weight: 15%)

### Purpose
Microservices communicate over HTTP/gRPC/queues. Broken or undeclared contracts cause silent data loss and cross-team outages. This dimension ensures contracts are explicit, stable, and validated.

### Expected Patterns

**Explicit response models:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    user = await db.get_user(user_id)
    return UserResponse.model_validate(user)
```

**Consistent error envelope:**
```python
class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(code="VALIDATION_ERROR", message=str(exc))
        ).model_dump()
    )
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| FastAPI route with no `response_model` | High | -15 pts per route (cap at 3) |
| `response_model=dict` or `response_model=Any` | High | -15 pts |
| Error responses inconsistent (some have `detail`, some have `message`) | Medium | -8 pts |
| 200 returned for partial failures | High | -15 pts |
| Breaking change: removed field from response model | Critical | -25 pts |
| Breaking change: type narrowed on existing field | High | -15 pts |
| Nullable field not typed `Optional` / `T \| None` | Medium | -8 pts |
| Missing 422 validation handler override in catch-all | Medium | -8 pts |
| `openapi_extra` used to bypass Pydantic schema | Low | -3 pts |
| Endpoint not included in OpenAPI schema (`include_in_schema=False` undocumented) | Low | -3 pts |

### Checks to Perform

1. List all `@app.get`, `@app.post`, etc. decorators and verify each has `response_model`.
2. Verify error response shapes are consistent across all exception handlers.
3. Check diff for removed fields or type changes in response models (if reviewing a diff).
4. Confirm 4xx/5xx handlers return the standard error envelope, not raw FastAPI `detail`.
5. Verify `Optional` / `T | None` used for any field that may be absent.

---

## Dimension 6: performance-risk (Weight: 10%)

### Purpose
Performance bugs in cloud services manifest as latency spikes, memory bloat, or cascading timeouts. This dimension flags patterns that will degrade under load without necessarily failing in tests.

### Expected Patterns

**Paginated list endpoints:**
```python
@app.get("/orders", response_model=Page[OrderResponse])
async def list_orders(
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
) -> Page[OrderResponse]:
    orders = await db.fetch_orders(cursor=cursor, limit=limit)
    return Page(items=orders, next_cursor=orders[-1].id if orders else None)
```

**Parallel I/O instead of sequential:**
```python
# Good
profile, permissions = await asyncio.gather(
    user_service.get_profile(user_id),
    auth_service.get_permissions(user_id),
)

# Bad — sequential when independent
profile = await user_service.get_profile(user_id)
permissions = await auth_service.get_permissions(user_id)
```

**Bounded queries:**
```python
# Good
rows = await conn.fetch("SELECT id, name FROM items WHERE active = $1 LIMIT $2", True, limit)
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| List endpoint without pagination | High | -15 pts |
| `SELECT *` on large tables | Medium | -8 pts |
| N+1 query in loop (fetch parent then fetch each child) | High | -15 pts |
| Unbounded `asyncio.gather()` fan-out (no semaphore) | Medium | -8 pts |
| ORM `.all()` without limit on potentially large table | High | -15 pts |
| Synchronous call to external service inside request handler | Critical | -25 pts (also async-correctness) |
| In-memory sort/filter of full DB result set | Medium | -8 pts |
| Background task used for transactional work (no durability) | High | -15 pts |
| No connection pool or pool size too small for concurrency | Medium | -8 pts |
| Cache with no TTL or eviction policy | Low | -3 pts |

### Checks to Perform

1. Find all list/search endpoints and verify `limit` / pagination parameters exist.
2. Search for ORM `.all()`, `.filter()` calls without `.limit()`.
3. Look for `for item in items: await fetch(item)` patterns (N+1).
4. Count sequential `await` calls in the same function that could be `gather()`.
5. Search for `asyncio.gather(*[fetch(i) for i in large_list])` without a semaphore.

---

## Dimension 7: test-coverage (Weight: 5%)

### Purpose
Tests verify correctness and prevent regressions. This dimension does not measure line coverage percentages — it checks for the presence and quality of key test types.

### Expected Patterns

**Async test with pytest-asyncio:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user_returns_201():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"
```

**Mocking external services:**
```python
import respx
import httpx

@pytest.mark.asyncio
@respx.mock
async def test_payment_service_timeout():
    respx.post("https://payments.example.com/charge").mock(side_effect=httpx.TimeoutException)
    result = await pay(order_id="ord_123")
    assert result.status == "failed"
    assert result.error_code == "TIMEOUT"
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| `asyncio.run()` in test (not `pytest-asyncio`) | Medium | -8 pts |
| External HTTP call not mocked in unit tests | High | -15 pts |
| Tests leave DB rows after teardown | Medium | -8 pts |
| No integration test exercising full request cycle | High | -15 pts |
| `unittest.mock.Mock` (not `AsyncMock`) for async callables | High | -15 pts |
| Hardcoded sleep in tests to wait for async work | Medium | -8 pts |
| Tests only cover happy path (no error or edge case) | Low | -3 pts |

### Checks to Perform

1. Verify `pytest.ini` or `pyproject.toml` configures `asyncio_mode = auto` or `@pytest.mark.asyncio` used on all async tests.
2. Check that `AsyncMock` is used for any mocked `async def` callable.
3. Search for `asyncio.run(` in test files.
4. Verify at least one test makes an end-to-end HTTP request through the app.
5. Check test fixtures for teardown logic (database cleanup, mock reset).

---

## Dimension 8: k8s-hygiene (Weight: 5%)

### Purpose
Kubernetes workloads without proper resource limits and probes cause cluster instability and poor rolling update behavior. This dimension checks Deployment/StatefulSet manifests and application shutdown handling.

### Expected Patterns

**Deployment with required hygiene:**
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          image: myapp:1.2.3  # pinned tag, not latest
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          securityContext:
            runAsNonRoot: true
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
```

**Graceful shutdown in Python:**
```python
import signal
import asyncio

shutdown_event = asyncio.Event()

def handle_sigterm(*args):
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)

async def main():
    server = await start_server()
    await shutdown_event.wait()
    await server.shutdown(timeout=30)
```

### Anti-Patterns and Their Severity

| Anti-Pattern | Severity | Scoring Impact |
|---|---|---|
| No `resources.requests` or `resources.limits` | High | -15 pts |
| `image: latest` in Deployment | Medium | -8 pts |
| No `livenessProbe` defined | High | -15 pts |
| No `readinessProbe` defined | High | -15 pts |
| `securityContext` absent | Medium | -8 pts |
| `runAsRoot: true` or `runAsUser: 0` | High | -15 pts |
| No SIGTERM handler in application | High | -15 pts |
| `preStop` hook absent when graceful drain needed | Medium | -8 pts |
| Memory limit set but no request (burst without guarantee) | Low | -3 pts |
| `privileged: true` | Critical | -25 pts |

### Checks to Perform

1. Find all `Deployment`, `StatefulSet`, `DaemonSet` YAML manifests.
2. Verify each container spec has both `resources.requests` and `resources.limits`.
3. Verify `livenessProbe` and `readinessProbe` exist on each container.
4. Search for `image: latest` or untagged image references.
5. Verify `securityContext` includes `runAsNonRoot: true`.
6. Search for `signal.signal(signal.SIGTERM` in the application entry point.

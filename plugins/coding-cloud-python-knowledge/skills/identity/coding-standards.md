# Python Cloud-Backend Coding Standards

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `user_service.py`, `health_check.py` |
| Classes | `PascalCase` | `OrderRepository`, `RetryPolicy` |
| Functions / methods | `snake_case` | `get_user_by_id()`, `start_background_tasks()` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT_S` |
| Type aliases | `PascalCase` | `UserId = NewType("UserId", int)` |
| Protobuf messages | `PascalCase` (generated) | `CreateOrderRequest` |
| Protobuf fields | `snake_case` (generated) | `order_id`, `created_at` |
| Environment variables | `SCREAMING_SNAKE_CASE` | `DATABASE_URL`, `LOG_LEVEL` |
| Kubernetes resources | `kebab-case` | `user-service`, `order-api-config` |
| Docker image tags | `kebab-case` with semver | `user-service:1.2.3` |

## Formatting

- Formatter: `ruff format` (Black-compatible, ~100x faster)
- Linter: `ruff check` with `select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]`
- Line length: 88 characters (ruff/Black default)
- Imports: sorted by `isort` rules via ruff (`I` rule set), stdlib / third-party / local sections
- Trailing commas: always in multi-line constructs (prevents noisy diffs)
- String quotes: double quotes for strings, single quotes acceptable in f-strings internals

## Type Annotations

- All public functions MUST have complete type annotations for parameters and return values
- Use `from __future__ import annotations` at module top for PEP 604 union syntax (`X | None`)
- Prefer `collections.abc` generics (`Sequence`, `Mapping`) over `typing` equivalents
- Use `typing.TypeAlias` for complex type aliases
- Use `typing.Protocol` for structural subtyping instead of ABC when only method signatures matter
- Pydantic models use field annotations; avoid `Any` except at serialization boundaries
- Run `mypy --strict` or `pyright` in strict mode as part of CI

## Error Handling

- Raise domain-specific exceptions inheriting from a project base exception
- Never catch bare `except:` or `except Exception:` without re-raising or logging
- Use `contextlib.suppress(SpecificError)` instead of empty except blocks
- HTTP handlers return structured error responses via FastAPI exception handlers, not raw strings
- gRPC handlers set `context.abort(grpc.StatusCode.X, "message")` with appropriate status codes
- Always clean up resources in `finally` blocks or use async context managers

## Async Conventions

- Use `async def` for any I/O-bound function (HTTP calls, DB queries, file reads)
- Never call blocking I/O inside `async def` -- use `asyncio.to_thread()` for unavoidable sync calls
- Use `asyncio.TaskGroup` (3.11+) for structured concurrency, not bare `create_task()`
- Graceful shutdown: register signal handlers that cancel the task group or set a shutdown event
- Timeouts: always wrap external calls with `asyncio.wait_for()` or `httpx` timeout parameters

## FastAPI / Starlette Patterns

- Use dependency injection (`Depends()`) for shared resources (DB sessions, auth, config)
- Define request/response models as Pydantic `BaseModel` subclasses -- never accept raw dicts
- Use `lifespan` context manager for startup/shutdown (not deprecated `on_event`)
- Middleware order: CORS -> request ID -> logging -> auth -> rate limiting
- Background tasks: use `BackgroundTasks` for fire-and-forget; use task queues (Celery/arq) for reliable processing

## gRPC Patterns

- Proto files live in a shared `proto/` directory with `buf` for linting and breaking-change detection
- Generated code goes in a separate package, never hand-edited
- Interceptors handle cross-cutting concerns (logging, auth, metrics) -- not inline in handlers
- Use streaming RPCs only when the payload is genuinely unbounded; prefer unary for request-response

## Docker Conventions

- Multi-stage builds: `builder` stage with dev dependencies, `runtime` stage with only production deps
- Base image: `python:3.11-slim` or `python:3.12-slim` for runtime stage
- Non-root user: always create and switch to a non-root user in the runtime stage
- Copy only `requirements.txt` (or lockfile) first, install deps, then copy source -- maximizes layer caching
- Use `.dockerignore` to exclude `.git`, `__pycache__`, `.venv`, `tests/`, `*.pyc`
- Health check: `HEALTHCHECK CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]`

## Kubernetes Conventions

- Always set resource requests AND limits for CPU and memory
- Liveness probe: TCP or HTTP check on the service port; 10s initial delay, 5s period
- Readiness probe: HTTP `/ready` endpoint that checks downstream dependencies
- Use `ConfigMap` for non-sensitive config, `Secret` for credentials -- never bake either into images
- Pod disruption budgets: `minAvailable: 1` for any service with 2+ replicas
- Labels: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component`

## Testing Standards

- Test files mirror source layout: `src/services/order.py` -> `tests/services/test_order.py`
- Use `pytest-asyncio` with `mode = "auto"` for async test functions
- Fixtures provide isolated resources; use `testcontainers` for Postgres, Redis, Kafka
- Mocking: prefer dependency injection over `unittest.mock.patch` -- inject fakes via FastAPI overrides
- Integration tests use real containers; unit tests mock external boundaries only
- Minimum coverage target: 80% line coverage for business logic modules

## Documentation

- Module-level docstrings: one-line summary of the module's purpose
- Public functions: Google-style docstrings with `Args:`, `Returns:`, `Raises:` sections
- Pydantic models: use `Field(description="...")` for API docs auto-generation
- Proto files: use comments above each `message` and `rpc` for documentation generation
- README per service: purpose, how to run locally, how to deploy, environment variables

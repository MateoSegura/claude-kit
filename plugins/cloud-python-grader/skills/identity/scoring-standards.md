# Scoring Standards

Complete dimension rubrics, automated check commands, severity definitions, deduction formulas, letter grade mapping, and report format specifications for Python cloud-backend code grading.

## Deductive Scoring Formula

Every dimension starts at 100. Findings deduct points:

```
raw_score = 100 - (critical_count * 25) - (high_count * 10) - (medium_count * 5) - (low_count * 2)
dimension_score = max(0, raw_score)
```

No caps on deductions per severity level. The floor is 0.

## Letter Grade Mapping

| Score Range | Letter Grade | Interpretation |
|-------------|-------------|----------------|
| 90-100 | A | Production-ready. Minor improvements possible but not blocking. |
| 80-89 | B | Solid. No critical issues. Suitable for production with minor revisions. |
| 70-79 | C | Acceptable. Meets minimum bar. Several improvements needed. |
| 60-69 | D | Below standard. Significant quality issues. Requires revision before deployment. |
| 0-59 | F | Failing. Fundamental problems. Major rework needed. |

## Severity Definitions

### Critical (-25 points)

A defect that causes runtime failure, data loss, security vulnerability, or correctness violation. In the Python cloud-backend context: patterns that will crash at runtime, silently lose data, expose attack surfaces, or violate type contracts at API boundaries.

**Domain examples**:
- Missing `await` on async DB query (coroutine discarded, data never read/written)
- Bare `except:` or `except Exception:` without re-raise (swallows `KeyboardInterrupt`, `SystemExit`)
- SQL injection via f-string interpolation in query construction
- `typing.Any` on public endpoint parameters or return types
- Blocking I/O inside `async def` without `asyncio.to_thread()` (event loop starvation)
- Hardcoded database passwords, API keys, or tokens in source files
- `asyncio.Task` that modifies shared mutable state without synchronization primitives

### High (-10 points)

A significant quality defect that degrades reliability, maintainability, or operability. The code works in the happy path but is fragile, poorly structured, or violates important conventions.

**Domain examples**:
- Missing `async with` for SQLAlchemy `AsyncSession` (connection leak on exception)
- No resource requests/limits in Kubernetes Deployment manifest
- Missing health or readiness probes
- `@ts-ignore` equivalent: `# type: ignore` without error code specification
- Container running as root user
- No timeout on external HTTP/gRPC calls
- Pydantic model using `dict` instead of typed fields for structured data

### Medium (-5 points)

A convention violation or missed optimization that affects consistency or readability but does not cause failures.

**Domain examples**:
- Inconsistent error response schema across endpoints
- Using deprecated `on_event("startup")` instead of `lifespan` context manager
- Missing Google-style docstring on public function
- Import ordering violation (ruff I rules)
- Pydantic `Field()` without `description` on API-facing model
- Test function name does not describe expected behavior
- gRPC handler returning generic `StatusCode.INTERNAL` instead of specific status

### Low (-2 points)

A stylistic issue or minor inconsistency with no functional impact.

**Domain examples**:
- Trailing whitespace or inconsistent blank lines
- Redundant type annotation where inference suffices
- Commented-out code (dead code)
- Unused import (caught by ruff F401)
- Variable name does not follow snake_case convention
- Missing trailing comma in multi-line function arguments

## Dimension Rubrics

### 1. Async Correctness (20%)

**What to check**:
- Every `async def` function properly `await`s all coroutine calls
- No blocking I/O (file reads, `time.sleep()`, synchronous HTTP) inside `async def`
- `asyncio.TaskGroup` (3.11+) used for concurrent tasks, not bare `asyncio.create_task()`
- Graceful shutdown: signal handlers or lifespan context cancels running tasks
- `asyncio.wait_for()` or explicit timeouts on all external async calls
- No `asyncio.run()` called inside an already-running event loop
- Background tasks properly cancelled on shutdown (no orphaned coroutines)

**Automated checks**:
```bash
# Grep for common async anti-patterns
rg "time\.sleep\(" --type py src/
rg "requests\.(get|post|put|delete|patch)\(" --type py src/
rg "open\(" --type py src/ | grep -v "aiofiles\|async with"
```

### 2. Type Safety (15%)

**What to check**:
- `mypy --strict` or `pyright` strict mode configured and passing (check `pyproject.toml`)
- All public functions have complete parameter and return type annotations
- No `Any` on API boundaries (FastAPI endpoint parameters, return types, Pydantic model fields)
- `from __future__ import annotations` used for modern union syntax
- `typing.Protocol` used for structural subtyping where appropriate
- Pydantic v2 models use typed fields, not `dict[str, Any]`
- No `# type: ignore` without specific error code (e.g., `# type: ignore[arg-type]`)

**Automated checks**:
```bash
mypy --strict --no-error-summary --show-error-codes src/
rg "# type: ignore(?!\[)" --type py src/   # bare type: ignore without error code
rg ": Any" --type py src/                   # Any usage
```

### 3. Security (15%)

**What to check**:
- No SQL injection: all queries use parameterized statements or ORM methods
- No hardcoded secrets: check for password/key/token string literals
- Input validation: all endpoint parameters validated via Pydantic models, not raw strings/dicts
- CORS configuration: explicit origin allowlist, not `allow_origins=["*"]` in production
- Authentication/authorization patterns present on protected endpoints
- Dependency versions: no known CVEs in pinned dependencies (check with `pip-audit` or `safety`)
- Docker: non-root user, no secrets baked into image layers

**Automated checks**:
```bash
bandit -r src/ -f json
rg "(password|secret|token|api_key)\s*=\s*[\"']" --type py src/
rg "allow_origins.*\*" --type py src/
```

### 4. Observability (10%)

**What to check**:
- Structured logging via `structlog` or `logging` with JSON formatter -- not bare `print()`
- `LOG_LEVEL` configurable via environment variable
- Request/response logging middleware with trace correlation IDs
- OpenTelemetry or equivalent tracing instrumentation on service boundaries
- Prometheus metrics endpoint (`/metrics`) or StatsD integration
- Health endpoint (`/health` or `/healthz`) returns 200 when service is alive
- Readiness endpoint (`/ready`) checks downstream dependencies
- Error reporting: unhandled exceptions logged with stack trace and request context

**Automated checks**:
```bash
rg "print\(" --type py src/ | grep -v "test"    # print statements in non-test code
rg "structlog|logging\.getLogger" --type py src/  # logging setup
rg "/health|/ready|/metrics" --type py src/       # observability endpoints
```

### 5. API Contracts (15%)

**What to check**:
- All endpoints use Pydantic `BaseModel` for request bodies and response models
- HTTP status codes are semantically correct (201 for creation, 404 for not found, 422 for validation)
- Error responses follow a consistent schema (e.g., `{"detail": "message", "code": "ERROR_CODE"}`)
- API versioning strategy present (URL prefix `/v1/` or header-based)
- Google API Design Guide adherence: resource-oriented URLs, standard methods (List, Get, Create, Update, Delete)
- gRPC service definitions use proper status codes and structured error details
- Request/response examples in Pydantic model `model_config` or docstrings

**Automated checks**:
```bash
rg "status_code=" --type py src/routes/ src/routers/   # status code usage
rg "class.*BaseModel" --type py src/models/             # Pydantic model presence
rg "HTTPException" --type py src/                       # error handling pattern
```

### 6. Performance Risk (10%)

**What to check**:
- No N+1 query patterns: loops that issue individual DB queries instead of batch/join
- Connection pooling configured for database and HTTP clients
- `selectinload` / `joinedload` used for SQLAlchemy relationship eager loading
- No unbounded iteration: large result sets use pagination or streaming
- Background processing: CPU-intensive work offloaded to task queues, not in-request
- Caching strategy for frequently-read, infrequently-written data
- No redundant serialization/deserialization in hot paths

**Automated checks**:
```bash
rg "for .+ in .+:" --type py src/ -A 3 | grep -i "await.*query\|await.*execute"  # N+1 pattern
rg "pool_size|create_engine|create_async_engine" --type py src/                     # pool config
```

### 7. Test Coverage (10%)

**What to check**:
- Test files exist and follow mirror layout (`src/services/order.py` -> `tests/services/test_order.py`)
- `pytest-asyncio` configured with `mode = "auto"` for async test functions
- Fixtures provide isolated resources (`conftest.py` patterns)
- Mocking discipline: prefer dependency injection over `unittest.mock.patch`
- Integration tests use `testcontainers` or equivalent for real database/message broker testing
- Test names describe expected behavior (not just `test_order_1`, `test_order_2`)
- Edge cases tested: empty inputs, error paths, boundary values, concurrent access

**Automated checks**:
```bash
# Count test files vs source files
find tests/ -name "test_*.py" | wc -l
find src/ -name "*.py" | grep -v __init__ | wc -l
rg "async def test_" tests/        # async test functions
rg "testcontainers" tests/          # integration test infrastructure
```

### 8. K8s Hygiene (5%)

**What to check**:
- Resource requests AND limits set for CPU and memory in every container spec
- Liveness probe defined (TCP or HTTP)
- Readiness probe defined (HTTP to `/ready` endpoint)
- Container runs as non-root user (`securityContext.runAsNonRoot: true`)
- ConfigMap for non-sensitive config, Secret for credentials -- never hardcoded
- Standard labels present: `app.kubernetes.io/name`, `app.kubernetes.io/version`
- Pod disruption budget defined for services with 2+ replicas
- Image tag is specific (not `latest`)
- `imagePullPolicy` set appropriately (`IfNotPresent` for versioned tags)

**Automated checks**:
```bash
rg "resources:" k8s/                    # resource definitions
rg "livenessProbe:|readinessProbe:" k8s/  # probe definitions
rg "runAsNonRoot" k8s/                  # non-root check
rg "image:.*:latest" k8s/              # latest tag anti-pattern
```

## Pass/Fail Thresholds

### Overall Pass/Fail

The overall result is **PASS** if ALL of the following are true:
1. Composite weighted score >= 60
2. No critical failure override is triggered

### Critical Failure Overrides

These conditions force an overall FAIL regardless of composite score:

| Override Condition | Rationale |
|-------------------|-----------|
| Async Correctness score = 0 | A Python async service that cannot handle concurrency correctly is non-functional |
| Security score = 0 | A service with zero security posture is not deployable |
| Three or more dimensions score below 30 | Broad quality failure across multiple areas indicates systemic problems |

## Report Header Template

Every report MUST begin with:

```markdown
# Code Grading Report
- **Timestamp**: YYYY-MM-DD HH:MM:SS UTC
- **Python Version**: 3.xx.x
- **Target Stack**: FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + gRPC
- **Files Analyzed**: <count>
- **Total Findings**: <count> (C:<n> H:<n> M:<n> L:<n>)
- **Tool Versions**: ruff <ver>, mypy <ver>, bandit <ver>
- **Tools Unavailable**: <list or "none">
```

## Weighted Composite Calculation

### Default Weights

| Dimension | Weight |
|-----------|--------|
| Async Correctness | 20.0% |
| Type Safety | 15.0% |
| Security | 15.0% |
| Observability | 10.0% |
| API Contracts | 15.0% |
| Performance Risk | 10.0% |
| Test Coverage | 10.0% |
| K8s Hygiene | 5.0% |
| **Total** | **100.0%** |

### N/A Weight Redistribution Example

If K8s Hygiene (5%) is N/A (no k8s manifests in repo):

```
remaining_total = 100 - 5 = 95
async_correctness_adjusted = 20 / 95 * 100 = 21.05%
type_safety_adjusted = 15 / 95 * 100 = 15.79%
security_adjusted = 15 / 95 * 100 = 15.79%
observability_adjusted = 10 / 95 * 100 = 10.53%
api_contracts_adjusted = 15 / 95 * 100 = 15.79%
performance_risk_adjusted = 10 / 95 * 100 = 10.53%
test_coverage_adjusted = 10 / 95 * 100 = 10.53%
```

### Composite Formula

```
composite = sum(dimension_score_i * adjusted_weight_i) / 100
```

Result is rounded to the nearest integer.

## Confidence Scoring

The synthesizer assigns a confidence level based on evidence available:

| Confidence | Criteria |
|------------|----------|
| High | >= 15 source files analyzed, >= 20 total findings (including low), zero N/A dimensions |
| Medium | 8-14 files analyzed, or 10-19 total findings, or 1 N/A dimension |
| Low | < 8 files analyzed, or < 10 total findings, or >= 2 N/A dimensions |

Confidence is reported in the scorecard but does not affect the score. It signals to the reader how much weight to place on the evaluation.

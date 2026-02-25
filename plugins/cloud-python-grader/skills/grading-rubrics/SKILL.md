---
name: cloud-python-grader:grading-rubrics
description: "Grading rubrics, scoring formula, and severity definitions for the 8-dimension code review framework covering async correctness, type safety, security, observability, API contracts, performance risk, test coverage, and Kubernetes hygiene for Python cloud microservices."
user-invocable: false
---

# Grading Rubrics — Python Cloud Microservices

Quick-reference entry point for the 8-dimension grading framework. Load dimension-rubrics.md for per-dimension checks and expected patterns. Load severity-definitions.md for severity criteria and weight rationale.

## 8 Grading Dimensions

| # | Dimension | Weight | Description |
|---|-----------|--------|-------------|
| 1 | `async-correctness` | 20% | Proper async/await usage, no blocking calls in event loop, task lifecycle management |
| 2 | `type-safety` | 15% | Type annotations coverage, mypy compliance, Pydantic model usage |
| 3 | `security` | 20% | OWASP alignment, secrets hygiene, injection prevention, least-privilege |
| 4 | `observability` | 10% | Structured logging, OpenTelemetry tracing, metrics, correlation IDs |
| 5 | `api-contracts` | 15% | OpenAPI schema accuracy, response model completeness, error envelope consistency |
| 6 | `performance-risk` | 10% | N+1 queries, unbounded iteration, missing pagination, cache misuse |
| 7 | `test-coverage` | 5% | Unit/integration test presence, async test patterns, mocking correctness |
| 8 | `k8s-hygiene` | 5% | Resource limits, liveness/readiness probes, security context, graceful shutdown |

Total weight: 100%

## Scoring Formula

Each dimension is scored 0–100. The final score is the weighted sum:

```
final_score = sum(dimension_score[i] * weight[i] for i in dimensions)
```

Dimension score starts at 100 and deducts per finding by severity:

| Severity | Deduction per finding | Maximum deductions |
|----------|-----------------------|--------------------|
| Critical | 25 pts | 4 findings exhaust dimension |
| High     | 15 pts | 6 findings exhaust dimension |
| Medium   | 8 pts  | 12 findings exhaust dimension |
| Low      | 3 pts  | informational only (floor 70) |

Minimum dimension score is 0 (cannot go negative). Low findings cannot push a dimension below 70.

## Grade Thresholds

| Final Score | Grade | Meaning |
|-------------|-------|---------|
| 90–100 | A | Production-ready — minor polish only |
| 80–89  | B | Ship with tracked improvements |
| 70–79  | C | Fix High findings before merge |
| 60–69  | D | Fix all Critical + High before merge |
| < 60   | F | Significant rework required |

## Dimension Quick-Reference Checklist

### async-correctness
- No `time.sleep()` inside `async def` — use `asyncio.sleep()`
- No synchronous I/O (blocking DB calls, `requests.get()`) inside event loop coroutines
- All `asyncio.create_task()` results stored and awaited or cancelled on shutdown
- `asyncio.Lock` used for shared mutable state accessed across `await` points
- No `asyncio.run()` called from within a running event loop

### type-safety
- All public function signatures annotated (parameters + return type)
- No bare `Any` without justification comment
- Pydantic models used for all request/response bodies and config
- `Optional[T]` replaced with `T | None` (Python 3.10+) where applicable
- mypy strict mode passes with no ignored errors in production code

### security
- No hardcoded secrets, tokens, or credentials in source files
- SQL queries use parameterized statements (no f-string interpolation)
- User-supplied input validated/sanitized before use in OS commands or file paths
- Secrets loaded from environment variables or a secrets manager (never `os.environ.get` fallback to plaintext default)
- HTTP clients enforce TLS verification (`verify=True`)

### observability
- All log statements use structured key-value fields (not f-strings as sole context)
- `trace_id` / `correlation_id` propagated through all log records
- OpenTelemetry spans created for external calls (DB, HTTP, queue)
- ERROR log level used only for actionable conditions requiring human attention
- No sensitive data (PII, tokens) in log output

### api-contracts
- All endpoints have explicit Pydantic `response_model`
- Error responses follow consistent envelope: `{"error": {"code": str, "message": str}}`
- `422` validation errors not swallowed with catch-all exception handlers
- Breaking changes flagged: removed fields, changed types, renamed paths
- Nullable fields explicitly typed as `Optional` / `T | None`

### performance-risk
- No `SELECT *` or unbounded queries without `LIMIT`
- ORM relationships not loaded eagerly when only FK is needed
- Pagination applied to all list endpoints
- `asyncio.gather()` used for parallel independent I/O, not sequential `await` chains
- Background tasks not used for work requiring transactional guarantees

### test-coverage
- `pytest-asyncio` used for async test functions (not bare `asyncio.run()`)
- External services mocked with `unittest.mock.AsyncMock` or `respx`
- At least one integration test exercises the full request/response cycle
- Test fixtures clean up database state (no cross-test leakage)

### k8s-hygiene
- `resources.requests` and `resources.limits` set for CPU and memory
- `livenessProbe` and `readinessProbe` defined with appropriate `initialDelaySeconds`
- `securityContext.runAsNonRoot: true` and `readOnlyRootFilesystem: true`
- `SIGTERM` handler implemented for graceful drain of in-flight requests
- No `latest` image tags in Deployment manifests

## Additional Resources

- [dimension-rubrics.md](dimension-rubrics.md) — Per-dimension rubric with checks, expected patterns, anti-patterns, and scoring impact. Load when grading a specific dimension.
- [severity-definitions.md](severity-definitions.md) — Severity criteria with examples, scoring weight rationale, and escalation rules. Load when classifying a finding's severity.

# coding-cloud-python-debugger

> **Role:** Debugger · **Version:** 0.0.2

Python cloud-backend debugger — diagnoses asyncio failures, profiles CPU/memory, analyzes distributed traces, debugs database queries, traces gRPC call chains, and investigates container/pod crashes.

```bash
claude-kit --kit coding-cloud-python-debugger
# or load the full team:
claude-kit --kit coding-cloud-python
```

**Companion auto-loaded:** `coding-cloud-python-knowledge` (asyncio, FastAPI, gRPC, Docker, Kubernetes, design patterns)

---

## Agents

| Agent | Description |
|-------|-------------|
| `triage-analyst` | First-responder diagnostician that classifies Python cloud service failures into 6 categories: asyncio, performance, distributed-trace, database, gRPC, and container/infrastructure. Use when the user reports an error, crash, or degraded behavior and the root domain is not yet clear. |
| `asyncio-debugger` | Specialist debugger for Python asyncio failures including unhandled task exceptions, event loop blocking, cancellation cascades, deadlocked coroutines, TaskGroup failures, and asyncio.shield misuse. Use when triage classifies the issue as asyncio-related or when the user reports hung requests, event loop warnings, or CancelledError propagation. |
| `profiler-analyst` | Specialist for CPU and memory profiling of Python cloud services. Guides usage of py-spy for CPU flame graphs, memray for memory allocation tracking, and tracemalloc for per-line allocation analysis. Use when triage classifies the issue as performance-related or when the user reports high CPU, memory growth, slow endpoints, or GC pressure. |
| `trace-analyst` | Specialist for distributed trace analysis via OpenTelemetry. Reads OTLP trace exports, Jaeger/Tempo query results, and application logs to reconstruct request flow across services, identify latency anomalies, and correlate traces with structured logs. Use when triage classifies the issue as distributed-trace-related or when the user reports cross-service latency, missing spans, or request flow breakdowns. |
| `db-query-debugger` | Specialist for database query debugging in Python cloud services. Diagnoses slow queries via EXPLAIN ANALYZE, missing indexes, N+1 query patterns, connection pool exhaustion, transaction deadlocks, and SQLAlchemy/asyncpg session lifecycle issues. Use when triage classifies the issue as database-related or when the user reports slow queries, connection errors, or ORM-related exceptions. |
| `grpc-chain-debugger` | Specialist for gRPC call chain debugging in Python microservices. Diagnoses status code errors, deadline propagation failures, metadata forwarding issues, streaming failures, protobuf serialization errors, and interceptor stack problems. Use when triage classifies the issue as gRPC-related or when the user reports gRPC status errors, deadline exceeded, or inter-service communication failures. |
| `container-crash-analyst` | Specialist for container and Kubernetes pod crash analysis. Diagnoses OOMKill events, CrashLoopBackOff cycles, liveness/readiness probe failures, resource limit misconfiguration, image pull errors, init container failures, and Docker build issues. Use when triage classifies the issue as container/infrastructure-related or when the user reports pod crashes, deployment failures, or container startup errors. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-cloud-python-debugger:debug` | Triage and diagnose failures in cloud Python services. Classifies symptoms into one of six categories, routes to the appropriate specialist, and delivers a structured diagnostic report. Read-only — the debugger never writes or modifies code. |

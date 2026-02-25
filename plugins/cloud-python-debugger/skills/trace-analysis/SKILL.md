---
name: cloud-python-debugger:trace-analysis
description: "Quick reference for OpenTelemetry distributed trace analysis — OTLP data model, Jaeger query patterns, common anomaly signatures in traces, trace-to-log correlation, and span status codes."
user-invocable: false
---

# Trace Analysis — Quick Reference

For context propagation failures, sampling impact, cross-service span reconstruction, exporter failure modes, and Grafana Tempo queries, see [reference.md](reference.md).

## OTLP Data Model

### Span Hierarchy

```
Trace (trace_id: 128-bit hex)
└── Root Span (parent_span_id = null)
    ├── Child Span A (parent_span_id = root.span_id)
    │   └── Child Span A1
    └── Child Span B
```

### Key Span Fields

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | 128-bit hex | Unique trace identifier — same across all spans |
| `span_id` | 64-bit hex | Unique span identifier |
| `parent_span_id` | 64-bit hex | Links to parent; absent on root span |
| `name` | string | Operation name (e.g., `GET /api/users`, `db.query`) |
| `kind` | enum | `INTERNAL`, `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER` |
| `start_time_unix_nano` | uint64 | Start timestamp in nanoseconds |
| `end_time_unix_nano` | uint64 | End timestamp |
| `status.code` | enum | `UNSET`, `OK`, `ERROR` |
| `status.message` | string | Error message if `status.code = ERROR` |
| `attributes` | map | Key-value metadata |
| `events` | list | Timestamped log points within a span |
| `links` | list | Cross-trace references |

### Span Status Codes

| Code | Meaning | When to set |
|------|---------|-------------|
| `UNSET` (0) | Default — no explicit status | Successful operations where status is not relevant |
| `OK` (1) | Explicitly success | Set when you want to override `UNSET` as "definitely succeeded" |
| `ERROR` (2) | Operation failed | Any exception, HTTP 5xx, DB error |

**Note**: HTTP 4xx (client errors) should generally NOT set `ERROR` on the server-side span — the server handled the request correctly. Set `ERROR` for 5xx.

### Common Semantic Conventions (OTel 1.x)

| Attribute | Example Value | Used For |
|-----------|--------------|---------|
| `http.method` | `GET` | HTTP client/server spans |
| `http.status_code` | `200` | HTTP response code |
| `http.route` | `/api/users/{id}` | URL template (not actual URL) |
| `db.system` | `postgresql` | DB type |
| `db.statement` | `SELECT * FROM users WHERE id = $1` | SQL query |
| `db.name` | `mydb` | Database name |
| `net.peer.name` | `db.internal` | Remote host |
| `net.peer.port` | `5432` | Remote port |
| `messaging.system` | `kafka` | Message queue type |
| `rpc.method` | `GetUser` | gRPC method name |
| `exception.type` | `ValueError` | Exception class name |
| `exception.message` | `invalid input` | Exception message |
| `exception.stacktrace` | `...` | Full traceback |

---

## Jaeger Query Patterns

### Basic Queries (Jaeger UI / API)

```
# Find traces for a service
service: my-python-api

# Find traces with errors
service: my-python-api  tags: error=true

# Find slow traces (> 2s end-to-end)
service: my-python-api  min-duration: 2s

# Find traces containing a specific operation
service: my-python-api  operation: POST /api/orders

# Find by trace ID
<paste 32-char hex trace_id>
```

### Jaeger HTTP API

```bash
# Search traces
curl "http://jaeger:16686/api/traces?service=my-api&limit=20&lookback=1h"

# Get specific trace
curl "http://jaeger:16686/api/traces/<trace_id>"

# List services
curl "http://jaeger:16686/api/services"

# List operations for a service
curl "http://jaeger:16686/api/services/my-api/operations"
```

---

## Common Anomaly Signatures

| Anomaly | Visual Pattern | Root Cause |
|---------|---------------|------------|
| N+1 queries | Many identical narrow DB spans in a loop | ORM lazy loading; missing eager load |
| Missing spans | Gap in timeline, orphaned child spans | Context propagation failure |
| High fan-out latency | Many parallel children; total > slowest child | Resource contention, connection pool wait |
| Sequential where parallel | Long chain of CLIENT spans | `await` inside loop instead of `asyncio.gather` |
| Span with no children but high duration | Fat leaf span | CPU-bound work, large serialization, blocking I/O |
| Error only on retry | Span with `ERROR` followed by identical `OK` span | Transient failure; circuit breaker may help |
| Sampled trace is incomplete | Some services missing entirely | Those services use incompatible propagator format |

---

## Trace-to-Log Correlation

### Inject Trace Context into Logs (Python)

```python
from opentelemetry import trace
import logging

class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            record.trace_id = format(ctx.trace_id, '032x')
            record.span_id = format(ctx.span_id, '016x')
            record.trace_flags = ctx.trace_flags
        else:
            record.trace_id = '0' * 32
            record.span_id = '0' * 16
            record.trace_flags = 0
        return True

# Attach to logger
logging.getLogger().addFilter(TraceContextFilter())
```

### JSON Log Format with Trace Fields

```python
import json, logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, 'trace_id', None),
            "span_id": getattr(record, 'span_id', None),
        })
```

### Querying Correlated Logs (Loki / CloudWatch)

```logql
# Loki — find logs for a specific trace
{service="my-api"} | json | trace_id="<32-char-hex>"

# CloudWatch Insights
fields @timestamp, @message, trace_id
| filter trace_id = "<32-char-hex>"
| sort @timestamp asc
```

---

## Span Events (Structured Log Points)

Span events are timestamped annotations within a span — more precise than logs for tracing flow within a single operation:

```python
from opentelemetry import trace

span = trace.get_current_span()

# Record an event (e.g., cache hit)
span.add_event("cache.hit", attributes={"cache.key": key, "cache.ttl": 300})

# Record an exception as a span event (standard convention)
try:
    risky_operation()
except Exception as e:
    span.record_exception(e)          # adds event with exception.* attributes
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
    raise
```

## Additional Resources

- [reference.md](reference.md) — Context propagation failure debugging (W3C, B3), sampling impact on trace completeness, cross-service span reconstruction, exporter failure modes, Grafana Tempo query syntax

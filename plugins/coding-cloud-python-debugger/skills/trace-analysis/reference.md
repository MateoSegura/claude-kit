# Trace Analysis — Deep Reference

## Context Propagation Failures

### How Propagation Works

Distributed tracing requires passing `trace_id` and `span_id` across process boundaries via HTTP headers (or message metadata). The propagator reads/writes these headers.

**W3C TraceContext headers:**

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^ ^^
             version  trace_id (32 hex chars)   span_id (16 hex)  flags
tracestate: vendor1=opaqueValue,vendor2=opaqueValue
```

**B3 Multi-Header (legacy Zipkin):**

```
X-B3-TraceId: 4bf92f3577b34da6a3ce929d0e0e4736
X-B3-SpanId: 00f067aa0ba902b7
X-B3-ParentSpanId: <parent>
X-B3-Sampled: 1
```

**B3 Single Header:**

```
b3: 4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-1
```

### Diagnosing Propagation Failures

**Symptom: Service B spans appear as separate root traces (no parent)**

Cause options:
1. Service A uses W3C (`traceparent`) but Service B expects B3 headers.
2. An intermediate proxy (nginx, load balancer) strips unknown headers.
3. Service B's instrumentation is not reading headers (e.g., missing `propagate.extract()`).
4. Async context lost — context not propagated into background tasks.

**Check 1: Verify headers are being sent**

```bash
# Intercept outgoing request from Service A
sudo tcpdump -i any -A port 8080 2>/dev/null | grep -E "traceparent|X-B3"
# OR add temporary logging in outgoing requests
```

**Check 2: Verify headers are being received and read by Service B**

```python
# FastAPI — add middleware to log incoming trace headers
from fastapi import Request

@app.middleware("http")
async def log_trace_headers(request: Request, call_next):
    trace_headers = {k: v for k, v in request.headers.items()
                     if k.lower() in ('traceparent', 'tracestate', 'x-b3-traceid',
                                      'x-b3-spanid', 'x-b3-sampled', 'b3')}
    if trace_headers:
        print(f"[TRACE] Incoming headers: {trace_headers}")
    return await call_next(request)
```

**Check 3: Verify propagator configuration**

```python
from opentelemetry.propagate import get_global_textmap
print(get_global_textmap())
# Should show: CompositePropagator([TraceContextTextMapPropagator, BaggagePropagator])
# If empty or missing B3: your OTEL_PROPAGATORS env var may be wrong

# Set explicitly if needed:
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    B3MultiFormat(),
]))
```

### Context Lost in asyncio Tasks

A common bug: creating an `asyncio.Task` from outside a span context — the new task does not inherit the current span.

```python
# BUG: task created outside the span, no trace context
async def handler(request):
    background = asyncio.create_task(background_work())  # ← no trace context!
    return "OK"

# FIX: capture context and pass it explicitly
import contextvars
from opentelemetry import context as otel_context

async def handler(request):
    ctx = otel_context.get_current()  # capture active context
    background = asyncio.create_task(background_work_with_ctx(ctx))
    return "OK"

async def background_work_with_ctx(ctx):
    token = otel_context.attach(ctx)
    try:
        await background_work()
    finally:
        otel_context.detach(token)
```

---

## Sampling Impact on Trace Completeness

### Sampling Modes

| Mode | What is Sampled | Impact |
|------|----------------|--------|
| `AlwaysOn` | 100% of traces | No data loss; high storage cost |
| `AlwaysOff` | 0% | No traces at all (debug only) |
| `TraceIdRatioBased(0.1)` | ~10% randomly | May miss rare errors; cheap |
| `ParentBased(TraceIdRatioBased)` | Respects parent's sampling decision | Consistent across services |
| `OTLP tail sampling` | Decided AFTER trace completes | Captures all errors at lower volume |

### Sampling Anti-Pattern

```python
# WRONG: each service samples independently
# Service A: 10% → Service B: 10% → complete trace probability = 1%
# This means 99% of multi-service traces are incomplete fragments

# RIGHT: use ParentBased so child services honour parent's decision
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

sampler = ParentBased(root=TraceIdRatioBased(0.1))
# Service A: 10% → Service B: always records if parent was sampled
```

### Tail Sampling with OTel Collector

Tail sampling requires an OTel Collector in the path to buffer spans and make the sampling decision after the full trace arrives:

```yaml
# otel-collector-config.yaml (tail sampling policy)
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 50000
    policies:
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces-policy
        type: latency
        latency: {threshold_ms: 2000}
      - name: sample-rest
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
```

---

## Cross-Service Span Reconstruction

### Manual Trace Reconstruction from Logs

When Jaeger/Tempo is unavailable but logs contain `trace_id`:

```bash
# Grep all service logs for a specific trace_id
grep "4bf92f3577b34da6a3ce929d0e0e4736" /var/log/service-a.log /var/log/service-b.log \
  | sort -k1,1    # sort by timestamp field

# With jq if logs are JSON
jq -r 'select(.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736") | [.timestamp, .service, .message] | @tsv' \
  /var/log/*.json | sort
```

### Reconstructing Span Tree from OTLP Export

```python
from collections import defaultdict

def build_span_tree(spans):
    """Given a list of span dicts, build parent-child tree."""
    by_id = {s['span_id']: s for s in spans}
    children = defaultdict(list)
    root = None

    for span in spans:
        parent = span.get('parent_span_id')
        if parent and parent in by_id:
            children[parent].append(span)
        else:
            root = span

    def print_tree(span, depth=0):
        duration_ms = (span['end_time'] - span['start_time']) / 1e6
        print(f"{'  ' * depth}[{span['name']}] {duration_ms:.1f}ms "
              f"{'ERROR' if span.get('status') == 'ERROR' else ''}")
        for child in sorted(children[span['span_id']],
                            key=lambda s: s['start_time']):
            print_tree(child, depth + 1)

    if root:
        print_tree(root)
```

---

## Exporter Failure Modes

### OTLP gRPC Exporter

| Failure | Symptom | Fix |
|---------|---------|-----|
| Connection refused | `StatusCode.UNAVAILABLE` logged; traces silent | Check collector endpoint, port 4317 |
| TLS mismatch | `SSL handshake failed` | Match TLS config; check certs |
| Timeout | Spans queued then dropped after `max_export_batch_size` | Increase `export_timeout_millis` |
| Endpoint wrong protocol | `UNIMPLEMENTED` or silent drop | HTTP exporter on gRPC port or vice versa |

### OTLP HTTP Exporter

Default endpoint: `http://localhost:4318/v1/traces`

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="http://otel-collector:4318/v1/traces",
    timeout=10,
    headers={"Authorization": "Bearer <token>"},
)
```

### Debugging Exporter

```python
# Temporarily replace with console exporter to verify spans are created
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
# Now all spans print to stdout — verify structure before debugging exporter
```

---

## Grafana Tempo Query Syntax

### TraceQL (Tempo 2.0+)

```traceql
# Find all traces with ERROR status
{ status = error }

# Find traces where any span took > 2s
{ duration > 2s }

# Find traces from a specific service
{ resource.service.name = "my-python-api" }

# Find traces with a DB span slower than 500ms
{ span.db.system = "postgresql" && duration > 500ms }

# Find traces with specific HTTP route and error
{ span.http.route = "/api/orders" && status = error }

# Combine: service + any child span with error
{ resource.service.name = "my-python-api" } && { status = error }
```

### Linking Grafana Logs to Tempo

In Grafana data source config (Loki), add a derived field:

```json
{
  "name": "TraceID",
  "matcherRegex": "trace_id=(\\w+)",
  "url": "${__value.raw}",
  "urlDisplayLabel": "View Trace",
  "datasourceUid": "<tempo-datasource-uid>"
}
```

This renders a "View Trace" link in log lines that contain `trace_id=<hex>`.

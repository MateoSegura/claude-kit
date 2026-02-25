---
name: core-devops:observability
description: "Observability fundamentals: the three pillars (logs, metrics, traces), structured logging, OpenTelemetry concepts, alerting strategies, SLIs/SLOs/SLAs, and dashboard design. Load when designing monitoring, logging, or alerting for any service."
user-invocable: false
---

# Observability -- Quick Reference

## Additional resources

- [observability-reference.md](observability-reference.md) -- Structured logging patterns, OpenTelemetry setup, alerting strategies, SLI/SLO definitions, dashboard design

---

## The Three Pillars

| Pillar | What it captures | Primary tool | Use case |
|--------|-----------------|--------------|----------|
| Logs | Discrete events with context | ELK, Loki, CloudWatch | Debugging specific requests, audit trails |
| Metrics | Numeric measurements over time | Prometheus, Datadog, CloudWatch | Dashboards, alerting, capacity planning |
| Traces | Request flow across services | Jaeger, Tempo, X-Ray | Latency analysis, dependency mapping |

**Key principle:** Each pillar answers different questions. Logs tell you *what happened*, metrics tell you *how the system is performing*, traces tell you *where time is spent*.

---

## Structured Logging

Always emit structured logs (JSON) instead of free-form text:

```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "ERROR",
  "message": "Failed to process order",
  "service": "order-service",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "order_id": "ORD-12345",
  "error": "connection timeout",
  "duration_ms": 5032
}
```

**Rules:**
- Always include: timestamp, level, message, service name
- Include trace_id and span_id for correlation with distributed traces
- Add domain-specific context (order_id, user_id, etc.)
- Never log secrets, passwords, tokens, or PII
- Use consistent field names across all services

### Log Levels

| Level | When to use |
|-------|------------|
| ERROR | Operation failed; requires attention |
| WARN | Unexpected condition; system recovered but should be investigated |
| INFO | Significant business events (request served, job completed) |
| DEBUG | Detailed diagnostic info (disabled in production) |

---

## Metrics -- The Four Golden Signals

Monitor these four signals for every service (per Google SRE):

| Signal | What to measure | Example metric |
|--------|----------------|----------------|
| Latency | Time to serve a request | `http_request_duration_seconds` |
| Traffic | Demand on the system | `http_requests_total` |
| Errors | Rate of failed requests | `http_errors_total` |
| Saturation | How full the system is | `cpu_utilization`, `memory_usage` |

### Metric Types

| Type | Description | Example |
|------|------------|---------|
| Counter | Monotonically increasing value | Total requests, errors |
| Gauge | Value that goes up and down | Current connections, queue depth |
| Histogram | Distribution of values | Request latency buckets |
| Summary | Pre-calculated quantiles | p50, p95, p99 latency |

---

## SLIs, SLOs, and SLAs

| Concept | Definition | Example |
|---------|-----------|---------|
| SLI (Service Level Indicator) | Quantitative measure of service behavior | 99.2% of requests complete in < 200ms |
| SLO (Service Level Objective) | Target value for an SLI | "99.9% availability over 30 days" |
| SLA (Service Level Agreement) | Contract with consequences for missing SLO | "99.9% uptime or credit issued" |

### Common SLIs

| Category | SLI | Calculation |
|----------|-----|-------------|
| Availability | Successful requests / total requests | `1 - (error_count / total_count)` |
| Latency | Requests faster than threshold | `fast_count / total_count` |
| Throughput | Requests processed per second | `rate(requests_total[5m])` |
| Correctness | Valid responses / total responses | `correct_count / total_count` |

### Error Budget

Error budget = `1 - SLO`. For a 99.9% SLO over 30 days:
- Error budget = 0.1% = 43.2 minutes of downtime
- When budget is exhausted: freeze deployments, focus on reliability

---

## Alerting Strategy

### Alert Severity Levels

| Severity | Response | Example |
|----------|----------|---------|
| Critical (P1) | Page on-call immediately | Service down, data loss risk |
| High (P2) | Notify team, respond within 1 hour | Error rate > 5%, SLO burn rate high |
| Warning (P3) | Review next business day | Disk usage > 80%, certificate expiring |
| Info | Dashboard only, no notification | Deployment completed, scaling event |

### Alerting Rules

1. **Alert on symptoms, not causes** -- alert on "error rate > 5%" not "CPU > 90%"
2. **Every alert must be actionable** -- if the responder cannot do anything, it is noise
3. **Use multi-window burn rates** -- avoid alerting on brief spikes
4. **Include runbook links** -- every alert should link to resolution steps
5. **Tune thresholds quarterly** -- review and adjust based on actual incidents

---

## OpenTelemetry Concepts

OpenTelemetry (OTel) provides a unified standard for collecting telemetry:

| Component | Purpose |
|-----------|---------|
| SDK | Instrument your application code |
| Collector | Receive, process, and export telemetry |
| Exporter | Send data to backends (Jaeger, Prometheus, etc.) |
| Context propagation | Pass trace context across service boundaries |

### Trace Structure

```
Trace (end-to-end request)
  └── Span: HTTP GET /api/orders (parent)
        ├── Span: Database query (child)
        ├── Span: Cache lookup (child)
        └── Span: HTTP POST /payments (child, different service)
              └── Span: Payment processing (grandchild)
```

Each span has: name, start/end time, attributes, status, parent span ID.

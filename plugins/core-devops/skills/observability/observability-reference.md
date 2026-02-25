# Observability Reference -- Full Patterns

Comprehensive reference for implementing observability across any technology stack.

---

## Structured Logging Patterns

### Log Format Standard

All services should emit JSON-structured logs with a consistent schema:

```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.orders",
  "message": "Order processed successfully",
  "service": "order-service",
  "version": "1.2.3",
  "environment": "production",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "order_id": "ORD-12345",
  "customer_id": "CUST-678",
  "duration_ms": 142,
  "status_code": 200
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO 8601 | Event time in UTC |
| level | string | ERROR, WARN, INFO, DEBUG |
| message | string | Human-readable event description |
| service | string | Service name (matches K8s deployment name) |
| trace_id | string | Distributed trace identifier |
| span_id | string | Current span identifier |

### Context Enrichment

Add domain-relevant fields to log entries:

| Domain | Context fields |
|--------|---------------|
| HTTP | method, path, status_code, duration_ms, client_ip, user_agent |
| Database | query_type, table, duration_ms, rows_affected |
| Queue | queue_name, message_id, consumer_group |
| Auth | user_id, auth_method, success (never log tokens or passwords) |

### What NOT to Log

- Passwords, API keys, tokens, or secrets
- Credit card numbers, SSNs, or other PII
- Full request/response bodies in production (use sampling)
- Health check hits (pollute logs with noise)

---

## Prometheus Metrics Patterns

### Naming Conventions

```
<namespace>_<subsystem>_<name>_<unit>

# Examples
http_server_request_duration_seconds      # histogram
http_server_requests_total                # counter
app_queue_depth_messages                  # gauge
db_connection_pool_size_connections       # gauge
```

**Rules:**
- Use snake_case
- Include unit as suffix (_seconds, _bytes, _total)
- Counters end in `_total`
- Use `_seconds` for durations (not milliseconds)

### Standard Service Metrics

```
# RED metrics (Rate, Errors, Duration) -- for request-driven services
http_server_requests_total{method, path, status}              # counter
http_server_request_duration_seconds{method, path}            # histogram
http_server_errors_total{method, path, error_type}            # counter

# USE metrics (Utilization, Saturation, Errors) -- for resources
process_cpu_utilization_ratio                                  # gauge
process_memory_usage_bytes                                     # gauge
db_connection_pool_active_connections                          # gauge
db_connection_pool_max_connections                             # gauge
queue_messages_pending                                         # gauge
```

### Histogram Bucket Selection

```
# HTTP latency (most requests < 1s)
buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

# Batch job duration (seconds to minutes)
buckets: [1, 5, 15, 30, 60, 120, 300, 600]

# Response size (bytes)
buckets: [100, 1000, 10000, 100000, 1000000, 10000000]
```

---

## OpenTelemetry Setup

### Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
  resource:
    attributes:
      - key: environment
        value: production
        action: upsert

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

### Context Propagation

Trace context propagates across service boundaries via HTTP headers:

| Header | Standard | Value |
|--------|----------|-------|
| `traceparent` | W3C Trace Context | `00-{trace_id}-{span_id}-{flags}` |
| `tracestate` | W3C Trace Context | Vendor-specific key-value pairs |
| `b3` | Zipkin B3 | `{trace_id}-{span_id}-{sampled}` |

**Rules:**
- Use W3C Trace Context as the primary propagation format
- Configure all HTTP clients and servers to propagate trace headers
- Message queues: embed trace context in message headers/attributes

### Sampling Strategies

| Strategy | When to use |
|----------|-------------|
| Always-on | Development, low-traffic services |
| Probabilistic (e.g., 10%) | High-traffic services in production |
| Rate-limited (e.g., 100/sec) | Consistent sample count regardless of traffic |
| Tail-based (keep errors/slow) | When you need all error traces but can sample success |

---

## Alerting Deep Dive

### Multi-Window Burn Rate Alerts

Instead of simple threshold alerts, use burn rate to detect SLO violations:

```
# Error budget consumption rate
burn_rate = error_rate / (1 - SLO)

# Alert when burning budget too fast
# Fast burn: 14.4x in 1 hour (exhausts budget in ~2.5 days)
# Slow burn: 3x in 6 hours (exhausts budget in ~10 days)
```

| Window | Burn rate | Urgency | Action |
|--------|-----------|---------|--------|
| 5 min / 1 hour | 14.4x | Critical | Page immediately |
| 30 min / 6 hours | 6x | High | Page during business hours |
| 2 hours / 1 day | 3x | Medium | Ticket for next business day |
| 6 hours / 3 days | 1x | Low | Review weekly |

### Alert Template

```yaml
# Prometheus alerting rule
groups:
  - name: slo-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_server_requests_total{status=~"5.."}[5m]))
            / sum(rate(http_server_requests_total[5m]))
          ) > 0.01
        for: 5m
        labels:
          severity: critical
          service: order-service
        annotations:
          summary: "Error rate > 1% for 5 minutes"
          runbook: "https://wiki.example.com/runbooks/high-error-rate"
          dashboard: "https://grafana.example.com/d/service-health"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_server_request_duration_seconds_bucket[5m])) by (le)
          ) > 1.0
        for: 10m
        labels:
          severity: high
        annotations:
          summary: "p99 latency > 1s for 10 minutes"
```

### On-Call Routing

| Severity | Route | Escalation |
|----------|-------|------------|
| Critical | PagerDuty -> primary on-call | Auto-escalate after 15 min |
| High | PagerDuty -> primary on-call | Auto-escalate after 1 hour |
| Warning | Slack channel #alerts | Team reviews next business day |
| Info | Dashboard only | No notification |

---

## SLO Implementation

### Defining SLOs

```yaml
# slo.yaml (conceptual)
service: order-service
slos:
  - name: availability
    description: "Proportion of successful HTTP requests"
    sli:
      type: availability
      good: "http_server_requests_total{status!~'5..'}"
      total: "http_server_requests_total"
    target: 99.9
    window: 30d

  - name: latency
    description: "Proportion of requests faster than 200ms"
    sli:
      type: latency
      good: "http_server_request_duration_seconds_bucket{le='0.2'}"
      total: "http_server_requests_total"
    target: 99.0
    window: 30d
```

### Error Budget Calculation

| SLO target | Error budget (30 days) | Allowed downtime |
|-----------|----------------------|------------------|
| 99% | 1% | 7 hours 18 min |
| 99.5% | 0.5% | 3 hours 39 min |
| 99.9% | 0.1% | 43 min 12 sec |
| 99.95% | 0.05% | 21 min 36 sec |
| 99.99% | 0.01% | 4 min 19 sec |

---

## Dashboard Design

### Dashboard Hierarchy

```
Level 1: Executive Overview
  └── Overall system health, SLO compliance, business KPIs

Level 2: Service Overview
  └── Per-service: latency, error rate, throughput, saturation

Level 3: Service Detail
  └── Endpoint breakdown, dependency health, resource usage

Level 4: Debug
  └── Individual traces, raw logs, detailed metrics
```

### Service Dashboard Layout (Level 2)

| Row | Panels | Purpose |
|-----|--------|---------|
| 1 | SLO status, error budget remaining | Are we meeting our targets? |
| 2 | Request rate, error rate, latency (p50/p95/p99) | Four golden signals |
| 3 | CPU, memory, connection pool usage | Resource saturation |
| 4 | Dependency latency, dependency error rate | Upstream/downstream health |
| 5 | Recent deployments, config changes | Correlation with changes |

### Dashboard Rules

1. **Every dashboard needs a purpose statement** -- who is the audience and what decisions does it support?
2. **Use consistent time ranges** -- default to last 1 hour with 30-day option
3. **Red/yellow/green thresholds match alert thresholds** -- visual and alerting must agree
4. **Include deployment markers** -- annotate graphs with deploy timestamps
5. **Link to related dashboards and runbooks** -- enable drill-down exploration

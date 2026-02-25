---
name: core-backend:distributed-systems
description: "Distributed systems patterns for backend services: circuit breakers, retries with exponential backoff, service discovery, event-driven architecture, saga pattern, CQRS, eventual consistency, idempotency, outbox pattern, and distributed tracing. Load when designing or implementing inter-service communication, fault tolerance, or event-driven workflows."
user-invocable: false
---

# Distributed Systems -- Pattern Catalog

## Additional resources

- [patterns-reference.md](patterns-reference.md) -- Full implementations: circuit breaker, retry, saga, CQRS, outbox pattern, event bus, idempotency
- [anti-patterns.md](anti-patterns.md) -- Common mistakes that cause cascading failures, race conditions, message loss

---

## Pattern Decision Matrix

| Need | Pattern | Trade-off |
|------|---------|-----------|
| Prevent cascading failures | Circuit Breaker | Adds latency when closed; fast fail when open |
| Handle transient errors | Retry + Exponential Backoff | Must be idempotent; cap max attempts |
| Avoid thundering herd on retry | Jitter | Slightly less predictable timing |
| Coordinate multi-service transaction | Saga (choreography or orchestration) | Complex rollback logic |
| Separate read/write models | CQRS | Eventual consistency; more code |
| Decouple producers/consumers | Message Queue | At-least-once delivery; need deduplication |
| Audit log / replay | Event Sourcing | Query complexity; storage growth |
| Guarantee event delivery | Outbox Pattern | Requires polling worker; adds infrastructure |
| Prevent duplicate processing | Idempotency Keys | Storage overhead for key tracking |

---

## Circuit Breaker

States: CLOSED (normal) -> OPEN (fast-fail after threshold) -> HALF-OPEN (test request) -> CLOSED

```
class CircuitBreaker:
    config:
        fail_threshold    = 5     // failures before opening
        success_threshold = 2     // successes to close from half-open
        timeout           = 30s   // seconds before trying half-open

    state = CLOSED
    failure_count = 0
    success_count = 0
    opened_at = null

    function call(operation):
        if state == OPEN:
            if now() - opened_at >= timeout:
                state = HALF_OPEN
            else:
                raise CircuitOpenError

        try:
            result = operation()
            on_success()
            return result
        catch expected_exception:
            on_failure()
            rethrow

    function on_success():
        if state == HALF_OPEN:
            success_count += 1
            if success_count >= success_threshold:
                state = CLOSED
                reset_counters()
        else:
            failure_count = max(0, failure_count - 1)

    function on_failure():
        failure_count += 1
        success_count = 0
        if failure_count >= fail_threshold:
            state = OPEN
            opened_at = now()
```

**Rules:**
- Wrap calls to external services, not internal logic
- Provide a fallback (queue for later, return cached data, return degraded response)
- Monitor circuit state transitions -- frequent opens indicate downstream issues
- Use separate breakers per downstream service

---

## Retry + Exponential Backoff

```
function retry_with_backoff(operation, config):
    config defaults:
        max_attempts = 3
        initial_delay = 0.5s
        max_delay = 30s
        base = 2.0
        jitter_factor = 0.25

    for attempt in 1..max_attempts:
        try:
            return operation()
        catch retryable_exception as error:
            if attempt == max_attempts:
                raise error
            delay = min(initial_delay * base^(attempt - 1), max_delay)
            jitter = delay * jitter_factor * random(-1, 1)
            wait = max(0, delay + jitter)
            sleep(wait)
```

**Rules:**
- Only retry idempotent operations (GET, PUT, DELETE -- NOT non-idempotent POST without idempotency key)
- Always use jitter to avoid thundering herd
- Set a max attempt count -- unbounded retries cause resource exhaustion
- Log each retry with context (attempt number, wait time, error type)

---

## Saga Pattern

### Choreography (event-driven, no central coordinator)

Each service listens for events and emits its own:
1. OrderService emits `OrderCreated`
2. InventoryService listens for `OrderCreated`, emits `StockReserved` or `StockFailed`
3. PaymentService listens for `StockReserved`, emits `PaymentCharged` or `PaymentFailed`
4. Each failure triggers a compensating event

### Orchestration (central saga coordinator)

```
class OrderSaga:
    function execute(order_id):
        steps = [
            Step(action=reserve_inventory, compensation=release_inventory),
            Step(action=charge_payment,    compensation=refund_payment),
            Step(action=schedule_shipping,  compensation=cancel_shipping),
        ]
        completed = []
        for step in steps:
            try:
                step.action(order_id)
                completed.append(step)
            catch error:
                // Rollback all completed steps in reverse order
                for done_step in reversed(completed):
                    done_step.compensation(order_id)
                return SagaResult(success=false, error=error)
        return SagaResult(success=true)
```

**When to use orchestration vs choreography:**
- Choreography: few services (2-3), simple flows, teams own their own services
- Orchestration: many services (4+), complex ordering, need visibility into saga state

---

## CQRS (Command Query Responsibility Segregation)

Separate the write model (commands) from the read model (queries):

```
// Commands mutate state through the write model
Command: CreateOrder { user_id, items }
    -> CommandHandler writes to normalized write DB
    -> Publishes OrderCreated event

// Queries read from a denormalized read model
Query: GetOrderSummary { order_id }
    -> QueryHandler reads from denormalized read DB
    -> Returns OrderSummary { order_id, user_name, item_count, total, status }
```

**Rules:**
- Write model is normalized (3NF), optimized for consistency
- Read model is denormalized, optimized for query performance
- Read model is updated asynchronously via events (eventual consistency)
- If the UI must see its own writes immediately, use synchronous confirmation or sticky sessions

---

## Eventual Consistency Rules

1. **Idempotency keys**: Every state-mutating operation must accept and store an idempotency key. Duplicate deliveries must produce the same outcome.
2. **Outbox pattern**: Write events to an outbox table in the same transaction as the state change. A separate process publishes from the outbox.
3. **Deduplication**: Consumers must track processed message IDs (cache with TTL or database table).
4. **Compensating transactions**: Every write operation must have a corresponding compensating operation for saga rollback.
5. **Read-your-writes**: If the UI requires seeing its own writes immediately, use sticky sessions or synchronous confirmation before redirecting.

# Distributed Systems -- Patterns Reference

Full implementations for production distributed systems patterns. All examples use pseudocode -- adapt to your language and framework.

---

## Circuit Breaker -- Full Implementation

```
// Resilience module: circuit_breaker

enum CircuitState { CLOSED, OPEN, HALF_OPEN }

struct CircuitBreakerConfig:
    fail_threshold: int = 5          // failures before opening
    success_threshold: int = 2       // successes to close from half-open
    timeout_seconds: float = 30.0    // seconds before trying half-open
    expected_exceptions: list[ExceptionType] = [TransientError]

class CircuitBreaker:
    name: string
    config: CircuitBreakerConfig
    state: CircuitState = CLOSED
    failure_count: int = 0
    success_count: int = 0
    opened_at: timestamp = null
    lock: mutex

    property effective_state -> CircuitState:
        if state == OPEN and elapsed(opened_at) >= config.timeout_seconds:
            return HALF_OPEN
        return state

    function call(operation) -> result:
        with lock:
            current = effective_state

        if current == OPEN:
            raise CircuitOpenError("Circuit '{name}' is OPEN")

        try:
            result = operation()
            on_success(current)
            return result
        catch config.expected_exceptions as error:
            on_failure(current)
            rethrow

    function on_success(state):
        with lock:
            if state == HALF_OPEN:
                success_count += 1
                if success_count >= config.success_threshold:
                    state = CLOSED
                    failure_count = 0
                    success_count = 0
                    log.info("Circuit closed", breaker=name)
            else:
                failure_count = max(0, failure_count - 1)

    function on_failure(state):
        with lock:
            failure_count += 1
            success_count = 0
            if failure_count >= config.fail_threshold:
                state = OPEN
                opened_at = now()
                log.warn("Circuit opened", breaker=name, failures=failure_count)
```

---

## Retry with Exponential Backoff -- Full Implementation

```
// Resilience module: retry

struct RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 0.5       // seconds
    max_delay: float = 30.0          // seconds
    exponential_base: float = 2.0
    jitter_factor: float = 0.25      // 25% jitter
    retryable_exceptions: list[ExceptionType] = [TransientError]

function retry_with_backoff(operation, config = RetryConfig()) -> result:
    last_error = null
    for attempt in 1..config.max_attempts:
        try:
            return operation()
        catch config.retryable_exceptions as error:
            last_error = error
            if attempt == config.max_attempts:
                break
            delay = min(
                config.initial_delay * config.exponential_base ^ (attempt - 1),
                config.max_delay
            )
            jitter = delay * config.jitter_factor * random_uniform(-1, 1)
            wait = max(0, delay + jitter)
            log.warn("Retrying after error",
                attempt=attempt,
                max_attempts=config.max_attempts,
                wait_seconds=wait,
                error=error.message,
                error_type=type(error).name
            )
            sleep(wait)
    raise last_error
```

---

## Outbox Pattern -- Transactional Event Publishing

Guarantees at-least-once delivery by writing events to a DB table in the same transaction as the business operation, then publishing asynchronously.

```
// Database table: outbox_messages
table outbox_messages:
    id: uuid (primary key, auto-generated)
    topic: string
    payload: json
    published: boolean (default false)
    created_at: timestamp (default now())

class OutboxPublisher:
    producer: MessageProducer   // Kafka, RabbitMQ, etc.
    poll_interval: float = 1.0  // seconds

    function start():
        spawn_background_task(poll_loop)

    function poll_loop():
        while running:
            try:
                publish_pending()
            catch error:
                log.error("Outbox poll error", error=error)
            sleep(poll_interval)

    function publish_pending():
        within transaction(db):
            messages = db.query(
                "SELECT * FROM outbox_messages WHERE published = false
                 LIMIT 100 FOR UPDATE SKIP LOCKED"
            )
            for msg in messages:
                producer.send(msg.topic, serialize(msg.payload))
                msg.published = true
            db.commit()

// Usage in service layer -- write event in same transaction as state change:
function create_order(db, data) -> Order:
    within transaction(db):
        order = Order.create(data)
        db.insert(order)
        db.insert(OutboxMessage(
            topic="orders",
            payload={"event": "OrderCreated", "order_id": order.id}
        ))
        // Both committed atomically -- event cannot be lost
    return order
```

---

## Idempotency Key Pattern

```
class IdempotencyStore:
    cache: KeyValueStore   // Redis, Memcached, or DB table
    ttl: duration = 24h

    function get_cached_result(key: string) -> result or null:
        value = cache.get("idempotency:" + key)
        if value:
            return deserialize(value)
        return null

    function store_result(key: string, result: object):
        cache.set("idempotency:" + key, serialize(result), ttl=ttl)

function generate_idempotency_key(body: bytes, user_id: string) -> string:
    content = serialize_json({"user_id": user_id, "body": body}, sort_keys=true)
    return sha256(content)

// Usage in request handler:
function handle_request(request):
    key = request.headers["Idempotency-Key"]
    if key:
        cached = idempotency_store.get_cached_result(key)
        if cached:
            return cached  // return previous result
    result = process_request(request)
    if key:
        idempotency_store.store_result(key, result)
    return result
```

---

## Event Bus -- In-Process Pub/Sub

```
class EventBus:
    handlers: map[EventType -> list[HandlerFunction]]

    function subscribe(event_type) -> decorator:
        // Register handler for event type
        function decorator(handler):
            handlers[event_type].append(handler)
            return handler
        return decorator

    function publish(event):
        event_handlers = handlers.get(type(event), [])
        if not event_handlers:
            log.warn("No handlers for event", event_type=type(event).name)
            return
        results = execute_concurrently([
            invoke(handler, event) for handler in event_handlers
        ])
        for result in results:
            if is_error(result):
                log.error("Event handler failed", error=result)

// Usage:
bus = EventBus()

@bus.subscribe(OrderCreated)
function send_confirmation_email(event):
    email_service.send_order_confirmation(event.order_id, event.user_email)

@bus.subscribe(OrderCreated)
function update_inventory(event):
    inventory_service.reserve(event.items)
```

---

## Service Discovery Patterns

### DNS-Based (Kubernetes-native)

In Kubernetes, services are discoverable via DNS:
```
<service-name>.<namespace>.svc.cluster.local
```

### Service Registry (Consul, etcd, ZooKeeper)

Services register themselves on startup and deregister on shutdown. Clients query the registry for service addresses.

### Client-Side Load Balancing

Client maintains a list of known service instances and distributes requests:
- Round-robin: simple, equal distribution
- Weighted: route more traffic to healthier/faster instances
- Least-connections: route to instance with fewest active requests

### Sidecar Proxy (Service Mesh)

A sidecar proxy (Envoy, Linkerd) handles discovery, load balancing, retries, and mTLS transparently. The application code makes plain HTTP/gRPC calls to localhost.

---

## Distributed Tracing

Propagate trace context across service boundaries:

```
// Trace context headers (W3C Trace Context standard):
// traceparent: 00-<trace-id>-<span-id>-<trace-flags>
// tracestate: <vendor-specific data>

// At each service boundary:
// 1. Extract trace context from incoming request headers
// 2. Create a child span linked to the parent
// 3. Inject trace context into outgoing request headers
// 4. Record span attributes: service name, operation, duration, status
// 5. Send spans to collector (OpenTelemetry, Jaeger, Zipkin)

// Key attributes to record:
//   service.name, http.method, http.url, http.status_code
//   db.system, db.statement, db.operation
//   rpc.system, rpc.service, rpc.method
//   error (boolean), error.message
```

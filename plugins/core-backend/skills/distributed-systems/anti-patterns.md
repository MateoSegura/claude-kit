# Distributed Systems -- Anti-Patterns

Common mistakes in distributed systems that cause cascading failures, data loss, and race conditions.

---

## Anti-Pattern 1: Retry Without Idempotency

**What developers do wrong:** Retry non-idempotent operations (e.g., POST /charge) without checking if the operation already succeeded.

```
// BAD: charging the card multiple times on retry
function charge_customer(customer_id, amount):
    retry(3):
        return payment_api.post("/charge", {customer_id, amount})
```

**Why it fails:** If the first request succeeds but the response times out, all retry attempts also succeed -- the customer is charged multiple times.

```
// GOOD: use idempotency key, server deduplicates
function charge_customer(customer_id, amount, idempotency_key):
    retry(3, on=TransientError):
        return payment_api.post("/charge",
            body={customer_id, amount},
            headers={"Idempotency-Key": idempotency_key}
        )
```

---

## Anti-Pattern 2: No Dead Letter Queue

**What developers do wrong:** Consumer crashes on a bad message and the message is requeued infinitely.

```
// BAD: poison message loops forever, blocking the queue
for message in queue.consume():
    process(message.body)
    message.ack()
    // If process() throws, message is nacked and requeued indefinitely
```

**Why it fails:** A single malformed message blocks the queue forever. All subsequent messages pile up behind it.

```
// GOOD: limit retries, route to DLQ after max attempts
for message in queue.consume():
    attempt = message.headers.get("x-retry-count", 0)
    try:
        process(message.body)
        message.ack()
    catch error:
        if attempt >= MAX_RETRIES:
            dead_letter_queue.publish(message.body,
                headers={...message.headers, "x-failure-reason": error.message})
            message.ack()  // remove from main queue
        else:
            retry_queue.publish(message.body,
                headers={...message.headers, "x-retry-count": attempt + 1},
                delay=RETRY_DELAYS[attempt])
            message.ack()
```

---

## Anti-Pattern 3: Distributed Transactions via Two-Phase Commit

**What developers do wrong:** Using 2PC across microservices for consistency.

```
// BAD: 2PC creates tight coupling and blocking
function create_order_2pc(order_data):
    // Phase 1: prepare
    inv_prepared = inventory_service.post("/prepare", order_data)
    pay_prepared = payment_service.post("/prepare", order_data)
    if inv_prepared.ok and pay_prepared.ok:
        // Phase 2: commit
        inventory_service.post("/commit", {tx_id: inv_prepared.tx_id})
        payment_service.post("/commit", {tx_id: pay_prepared.tx_id})
```

**Why it fails:** If the coordinator crashes after Phase 1, both services are locked waiting for commit/abort. Services are tightly coupled; one slow service blocks all transactions.

```
// GOOD: use Saga pattern with compensating transactions
class OrderSaga:
    function execute(order_id, order_data):
        try:
            inventory_service.post("/reserve", {order_data, order_id})
        catch error:
            return failure(error)
        try:
            payment_service.post("/charge", {order_data, order_id})
        catch error:
            inventory_service.post("/release", {order_id})  // compensate
            return failure(error)
        return success()
```

---

## Anti-Pattern 4: Missing Connection Pool Limits

**What developers do wrong:** Creating one HTTP or DB connection per request with no limits.

```
// BAD: new client per request, unbounded connections
function handle_request(payload):
    client = new HttpClient()  // new connection each time
    result = client.post("http://downstream/api", payload)
    client.close()
    return result
```

**Why it fails:** Under load, hundreds of open connections exhaust downstream service connection limits, file descriptors, and memory. Cold TCP handshake on every request adds 50-200ms latency.

```
// GOOD: shared client with connection pool, created at startup
app.http_client = new HttpClient(
    max_connections=100,
    max_keepalive=20,
    connect_timeout=2s,
    read_timeout=10s
)

function handle_request(payload):
    result = app.http_client.post("http://downstream/api", payload)
    return result
```

---

## Anti-Pattern 5: Fire-and-Forget Without Error Handling

**What developers do wrong:** Spawning background tasks for critical operations and ignoring failures.

```
// BAD: if background task fails, nobody knows
function create_order(order):
    db.insert(order)
    db.commit()
    spawn_task(notify_warehouse(order))   // silent failure
    spawn_task(send_confirmation(order))  // silent failure
```

**Why it fails:** Unhandled exceptions in background tasks are silently swallowed. Critical side effects (warehouse notification, email) fail without detection.

```
// GOOD: use outbox for critical ops; log errors for non-critical
function create_order(order):
    within transaction(db):
        db.insert(order)
        // Critical: use outbox pattern for warehouse notification
        db.insert(OutboxMessage(
            topic="warehouse",
            payload={"order_id": order.id}
        ))

    // Non-critical: fire-and-forget WITH error logging
    spawn_task(
        try:
            send_confirmation(order)
        catch error:
            log.error("Confirmation email failed", order_id=order.id, error=error)
    )
```

---

## Anti-Pattern 6: Shared Database Between Services

**What developers do wrong:** Microservices sharing a single database schema for convenience.

```
// BAD: OrderService directly queries UserService's table
function get_order_with_user(db, order_id):
    result = db.query(
        "SELECT o.*, u.* FROM orders o
         JOIN users u ON o.user_id = u.id
         WHERE o.id = ?", order_id
    )
    return result
```

**Why it fails:** Schema changes in UserService break OrderService silently. Both services must be deployed together. Violates bounded context isolation.

```
// GOOD: service-to-service call or event-driven denormalization
function get_order_with_user(order_id):
    order = order_repo.get(order_id)
    user = user_service_client.get_user(order.user_id)  // API call, may cache
    return {order, user}

// Or: denormalize user name into order at creation time (eventual consistency)
// Order table stores: user_id, user_name (snapshot at order time)
```

---

## Anti-Pattern 7: Unbounded Concurrent Requests

**What developers do wrong:** Sending a large batch of concurrent requests without concurrency limits.

```
// BAD: 10,000 concurrent HTTP requests overwhelm downstream
user_ids = range(10000)
users = execute_concurrently([fetch_user(id) for id in user_ids])
```

**Why it fails:** All 10,000 requests fire simultaneously, exhausting connection pool limits, triggering rate limits on downstream services, and causing memory pressure from queued responses.

```
// GOOD: use a semaphore to bound concurrency
function fetch_all_users(user_ids, concurrency=20):
    semaphore = new Semaphore(concurrency)
    function fetch_one(id):
        with semaphore:
            return fetch_user(id)
    return execute_concurrently([fetch_one(id) for id in user_ids])
```

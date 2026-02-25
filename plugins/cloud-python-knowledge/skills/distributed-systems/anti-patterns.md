# Distributed Systems — Anti-Patterns

Common mistakes in Python distributed systems that cause cascading failures, data loss, and race conditions.

---

## Anti-Pattern 1: Retry Without Idempotency

**What developers do wrong:** Retry non-idempotent operations (e.g., `POST /charge`) without checking if the operation already succeeded.

```python
# BAD: charging the card multiple times on retry
@retry(stop=stop_after_attempt(3))
async def charge_customer(customer_id: str, amount: int) -> dict:
    return await payment_api.post("/charge", json={"customer_id": customer_id, "amount": amount})
```

**Why it fails:** If the first request succeeds but the response times out, all 3 retry attempts also succeed — the customer is charged 3 times.

```python
# GOOD: use idempotency key, server deduplicates
@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=10),
)
async def charge_customer(customer_id: str, amount: int, idempotency_key: str) -> dict:
    return await payment_api.post(
        "/charge",
        json={"customer_id": customer_id, "amount": amount},
        headers={"Idempotency-Key": idempotency_key},
    )
```

---

## Anti-Pattern 2: Synchronous HTTP Calls in Event Handlers

**What developers do wrong:** Making blocking HTTP calls inside message queue consumers, blocking the consumer thread/loop.

```python
# BAD: requests.get blocks the asyncio event loop
async def handle_order_event(event: dict) -> None:
    user = requests.get(f"http://user-service/users/{event['user_id']}").json()
    await send_notification(user["email"], event)
```

**Why it fails:** `requests.get` is synchronous and blocks the entire asyncio event loop, preventing other coroutines from running. Consumer throughput collapses.

```python
# GOOD: use httpx.AsyncClient with a shared client instance
_http_client = httpx.AsyncClient(timeout=5.0)

async def handle_order_event(event: dict) -> None:
    resp = await _http_client.get(f"http://user-service/users/{event['user_id']}")
    resp.raise_for_status()
    user = resp.json()
    await send_notification(user["email"], event)
```

---

## Anti-Pattern 3: No Dead Letter Queue

**What developers do wrong:** Consumer crashes on a bad message and the message is requeued infinitely.

```python
# BAD: poison message loops forever, blocking the queue
async with queue.iterator() as q:
    async for message in q:
        async with message.process():
            await process_message(json.loads(message.body))
            # If this raises, message is nacked and requeued indefinitely
```

**Why it fails:** A single malformed message blocks the queue forever. All subsequent messages pile up behind it.

```python
# GOOD: limit retries, route to DLQ after max attempts
async with queue.iterator() as q:
    async for message in q:
        attempt = int(message.headers.get("x-retry-count", 0))
        try:
            async with message.process():
                await process_message(json.loads(message.body))
        except Exception as e:
            if attempt >= MAX_RETRIES:
                await dead_letter_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers={**message.headers, "x-failure-reason": str(e)},
                    ),
                    routing_key="dead_letter",
                )
                await message.ack()
            else:
                await message.nack(requeue=False)
                await retry_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers={**message.headers, "x-retry-count": str(attempt + 1)},
                        expiration=str(RETRY_DELAYS[attempt] * 1000),
                    ),
                    routing_key=message.routing_key,
                )
```

---

## Anti-Pattern 4: Distributed Transactions via Two-Phase Commit

**What developers do wrong:** Using 2PC across microservices for consistency.

```python
# BAD: 2PC creates tight coupling and blocking
async def create_order_with_2pc(order_data: dict) -> str:
    # Phase 1: prepare
    inv_prepared = await inventory_service.post("/prepare", json=order_data)
    pay_prepared = await payment_service.post("/prepare", json=order_data)

    if inv_prepared.ok and pay_prepared.ok:
        # Phase 2: commit
        await inventory_service.post("/commit", json={"tx_id": inv_prepared.json()["tx_id"]})
        await payment_service.post("/commit", json={"tx_id": pay_prepared.json()["tx_id"]})
```

**Why it fails:** If the coordinator crashes after Phase 1, both services are locked waiting for commit/abort. Services are tightly coupled; one slow service blocks all transactions.

```python
# GOOD: use Saga pattern with compensating transactions
class OrderSaga:
    async def execute(self, order_id: str, order_data: dict) -> bool:
        try:
            await inventory_service.post("/reserve", json={**order_data, "order_id": order_id})
        except Exception as e:
            logger.error("Inventory reservation failed", order_id=order_id, error=str(e))
            return False

        try:
            await payment_service.post("/charge", json={**order_data, "order_id": order_id})
        except Exception as e:
            # Compensate: release inventory
            await inventory_service.post("/release", json={"order_id": order_id})
            logger.error("Payment failed, inventory released", order_id=order_id, error=str(e))
            return False

        return True
```

---

## Anti-Pattern 5: Missing Connection Pool Limits

**What developers do wrong:** Creating one httpx or DB connection per request with no limits.

```python
# BAD: new client per request, unbounded connections
@router.post("/process")
async def process(payload: dict) -> dict:
    async with httpx.AsyncClient() as client:  # new connection each time
        result = await client.post("http://downstream/api", json=payload)
    return result.json()
```

**Why it fails:** Under load, hundreds of open connections exhaust downstream service connection limits, file descriptors, and memory. Cold TCP handshake on every request adds 50-200ms latency.

```python
# GOOD: shared client with connection pool, created at startup
# In lifespan:
app.state.http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    timeout=httpx.Timeout(connect=2.0, read=10.0),
)

@router.post("/process")
async def process(request: Request, payload: dict) -> dict:
    client: httpx.AsyncClient = request.app.state.http_client
    result = await client.post("http://downstream/api", json=payload)
    result.raise_for_status()
    return result.json()
```

---

## Anti-Pattern 6: Fire-and-Forget Without Error Handling

**What developers do wrong:** Using `asyncio.create_task` for critical operations and ignoring failures.

```python
# BAD: exceptions in background tasks are silently swallowed
async def create_order(order: Order) -> None:
    db.add(order)
    await db.commit()
    asyncio.create_task(notify_warehouse(order))  # if this fails, nobody knows
    asyncio.create_task(send_confirmation(order)) # same
```

**Why it fails:** Unhandled exceptions in `asyncio.Task` are logged at WARNING level and discarded. Critical side effects (warehouse notification, email) fail silently.

```python
# GOOD: handle exceptions; use queue for critical operations
async def create_order(order: Order, db: AsyncSession) -> None:
    db.add(order)
    # Critical: use outbox pattern for warehouse notification
    db.add(OutboxMessage(topic="warehouse", payload={"order_id": str(order.id)}))
    await db.commit()

    # Non-critical: fire-and-forget WITH error logging
    async def _notify_with_logging():
        try:
            await send_confirmation(order)
        except Exception:
            logger.exception("Confirmation email failed", order_id=str(order.id))

    asyncio.create_task(_notify_with_logging())
```

---

## Anti-Pattern 7: Shared Database Between Services

**What developers do wrong:** Microservices sharing a single database schema for convenience.

```python
# BAD: OrderService directly queries UserService's table
async def get_order_with_user(db: AsyncSession, order_id: UUID) -> dict:
    result = await db.execute(
        select(Order, User)
        .join(User, Order.user_id == User.id)
        .where(Order.id == order_id)
    )
    order, user = result.one()
    return {"order": order, "user": user}  # crosses service boundary in DB
```

**Why it fails:** Schema changes in UserService break OrderService silently. Both services must be deployed together. Violates bounded context isolation.

```python
# GOOD: service-to-service call or event-driven denormalization
async def get_order_with_user(order_id: UUID) -> dict:
    order = await order_repo.get(order_id)
    # Call UserService API — may be cached in Redis
    user = await user_service_client.get_user(order.user_id)
    return {"order": order, "user": user}

# Or: denormalize user name into order at creation time (eventual consistency)
# Order table stores: user_id, user_name (snapshot at order time)
```

---

## Anti-Pattern 8: Unbounded asyncio.gather

**What developers do wrong:** Using `asyncio.gather` on a large list without concurrency limits.

```python
# BAD: 10,000 concurrent HTTP requests overwhelm the downstream service
user_ids = list(range(10_000))
users = await asyncio.gather(*[fetch_user(uid) for uid in user_ids])
```

**Why it fails:** All 10,000 requests fire simultaneously, exhausting connection pool limits, triggering rate limits on the downstream service, and causing OOM from queued responses.

```python
# GOOD: use Semaphore to bound concurrency
async def fetch_all_users(user_ids: list[int], concurrency: int = 20) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    async def fetch_one(uid: int) -> dict:
        async with sem:
            return await fetch_user(uid)
    return await asyncio.gather(*[fetch_one(uid) for uid in user_ids])
```

# Distributed Systems -- Python Anti-Patterns

Python-specific mistakes that cause cascading failures, data loss, and race conditions. For language-agnostic anti-patterns, see `core-backend:distributed-systems`.

---

## Anti-Pattern 1: Retry Without Idempotency

```python
# BAD: charging the card multiple times on retry
@retry(stop=stop_after_attempt(3))
async def charge_customer(customer_id: str, amount: int) -> dict:
    return await payment_api.post("/charge", json={"customer_id": customer_id, "amount": amount})

# GOOD: use idempotency key
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

## Anti-Pattern 2: Blocking I/O in Async Event Handlers

```python
# BAD: requests.get blocks the asyncio event loop
async def handle_order_event(event: dict) -> None:
    user = requests.get(f"http://user-service/users/{event['user_id']}").json()
    await send_notification(user["email"], event)

# GOOD: use httpx.AsyncClient
_http_client = httpx.AsyncClient(timeout=5.0)

async def handle_order_event(event: dict) -> None:
    resp = await _http_client.get(f"http://user-service/users/{event['user_id']}")
    resp.raise_for_status()
    await send_notification(resp.json()["email"], event)
```

---

## Anti-Pattern 3: No Dead Letter Queue (aio-pika)

```python
# BAD: poison message loops forever
async with queue.iterator() as q:
    async for message in q:
        async with message.process():
            await process_message(json.loads(message.body))

# GOOD: limit retries, route to DLQ
async with queue.iterator() as q:
    async for message in q:
        attempt = int(message.headers.get("x-retry-count", 0))
        try:
            async with message.process():
                await process_message(json.loads(message.body))
        except Exception as e:
            if attempt >= MAX_RETRIES:
                await dead_letter_exchange.publish(
                    aio_pika.Message(body=message.body, headers={**message.headers, "x-failure-reason": str(e)}),
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

## Anti-Pattern 4: Missing Connection Pool Limits

```python
# BAD: new client per request
@router.post("/process")
async def process(payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        result = await client.post("http://downstream/api", json=payload)
    return result.json()

# GOOD: shared client with connection pool
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

## Anti-Pattern 5: Fire-and-Forget Without Error Handling

```python
# BAD: exceptions silently swallowed
async def create_order(order: Order) -> None:
    db.add(order)
    await db.commit()
    asyncio.create_task(notify_warehouse(order))
    asyncio.create_task(send_confirmation(order))

# GOOD: outbox for critical ops, error logging for non-critical
async def create_order(order: Order, db: AsyncSession) -> None:
    db.add(order)
    db.add(OutboxMessage(topic="warehouse", payload={"order_id": str(order.id)}))
    await db.commit()

    async def _notify_with_logging():
        try:
            await send_confirmation(order)
        except Exception:
            logger.exception("Confirmation email failed", order_id=str(order.id))
    asyncio.create_task(_notify_with_logging())
```

---

## Anti-Pattern 6: Unbounded asyncio.gather

```python
# BAD: 10,000 concurrent requests
users = await asyncio.gather(*[fetch_user(uid) for uid in range(10_000)])

# GOOD: use Semaphore to bound concurrency
async def fetch_all_users(user_ids: list[int], concurrency: int = 20) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    async def fetch_one(uid: int) -> dict:
        async with sem:
            return await fetch_user(uid)
    return await asyncio.gather(*[fetch_one(uid) for uid in user_ids])
```

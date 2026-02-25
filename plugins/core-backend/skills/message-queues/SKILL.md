---
name: core-backend:message-queues
description: "Message queue patterns for backend services: pub/sub vs point-to-point, message broker comparison (Redis Streams, RabbitMQ, Kafka), dead letter queues, exactly-once delivery challenges, event schemas and versioning, consumer group patterns, and message ordering guarantees. Load when designing or implementing asynchronous messaging."
user-invocable: false
---

# Message Queues -- Quick Reference

## Additional resources

- [queues-reference.md](queues-reference.md) -- Full patterns: broker-specific implementations, DLQ handling, schema evolution, consumer patterns

---

## Messaging Pattern Decision Matrix

| Need | Pattern | Trade-off |
|------|---------|-----------|
| Decouple producer/consumer | Point-to-point queue | Single consumer per message; simple |
| Fan-out to multiple consumers | Pub/sub (topic) | All subscribers receive every message |
| Competing consumers (load distribution) | Consumer groups | Need partition/queue affinity for ordering |
| Delayed/scheduled processing | Delayed queue / TTL | Extra infrastructure; timing not exact |
| Failed message handling | Dead letter queue (DLQ) | Need monitoring + manual reprocessing |
| Event replay / audit | Event log (Kafka) | Storage growth; retention policy needed |
| Lightweight task queue | Redis Streams or lists | Durability depends on Redis persistence config |

---

## Broker Comparison

| Feature | Redis Streams | RabbitMQ | Kafka |
|---------|--------------|----------|-------|
| Throughput | Medium-high | Medium | Very high |
| Ordering | Per-stream | Per-queue | Per-partition |
| Durability | AOF/RDB (configurable) | Disk-based (per-queue) | Replicated log |
| Consumer groups | Yes | Yes (competing consumers) | Yes (partition assignment) |
| Message retention | Capped by MAXLEN or MINID | Consumed = removed (unless DLQ) | Time/size-based retention |
| Replay | Yes (read from any ID) | No (once consumed, gone) | Yes (reset offset) |
| Dead letter queue | Manual (application logic) | Built-in (DLX) | Manual (produce to DLQ topic) |
| Best for | Lightweight queuing, caching layer already uses Redis | Complex routing, request-reply, priority queues | High-throughput event streaming, event sourcing |

---

## Delivery Guarantees

| Guarantee | Meaning | How to achieve |
|-----------|---------|---------------|
| At-most-once | Message may be lost, never duplicated | Fire and forget; no acks |
| At-least-once | Message delivered 1+ times; may duplicate | Ack after processing; retry on failure |
| Exactly-once | Message delivered exactly once | At-least-once + idempotent consumer |

**Exactly-once is not a broker feature -- it is an application-level guarantee:**
1. Broker delivers at-least-once (ack after processing)
2. Consumer stores a deduplication key (message ID or idempotency key)
3. Before processing, check if message was already handled
4. Process and store deduplication key in the same transaction

---

## Consumer Group Patterns

```
// Consumer group: multiple consumers sharing work from the same queue/topic
// Each message is delivered to exactly one consumer in the group

// Pattern 1: Round-robin (RabbitMQ default, Redis XREADGROUP)
//   Messages distributed evenly across consumers
//   No ordering guarantee across consumers

// Pattern 2: Partition-based (Kafka)
//   Each consumer owns one or more partitions
//   Ordering guaranteed within a partition
//   Rebalance when consumers join/leave

// Choosing a partition key (Kafka):
//   - Use entity ID (order_id, user_id) for per-entity ordering
//   - All events for the same entity go to the same partition
//   - Avoid hot partitions: don't use a key with low cardinality
```

---

## Message Acknowledgment

```
// At-least-once delivery requires explicit acknowledgment

// Pattern: ack AFTER successful processing
for message in consumer.receive():
    try:
        process(message)
        message.ack()           // remove from queue
    catch error:
        if is_retryable(error):
            message.nack()      // requeue for retry
        else:
            send_to_dlq(message, error)
            message.ack()       // remove from main queue

// NEVER ack before processing -- message will be lost if consumer crashes
// NEVER process without ack -- message will be redelivered endlessly
```

---

## Dead Letter Queue (DLQ)

```
// Messages that fail processing after max retries go to DLQ

function consume_with_dlq(queue, max_retries=3):
    for message in queue.receive():
        attempt = message.metadata.get("retry_count", 0)
        try:
            process(message)
            message.ack()
        catch error:
            if attempt >= max_retries:
                dlq.publish({
                    original_message: message.body,
                    error: error.message,
                    failed_at: now(),
                    attempts: attempt + 1,
                    source_queue: queue.name,
                })
                message.ack()  // remove from main queue
                log.error("Message sent to DLQ", error=error, attempts=attempt+1)
            else:
                // Requeue with incremented retry count and delay
                retry_queue.publish(
                    body=message.body,
                    metadata={...message.metadata, retry_count: attempt + 1},
                    delay=BACKOFF_DELAYS[attempt]   // e.g., 1s, 5s, 30s
                )
                message.ack()
```

**DLQ monitoring:** Alert when DLQ depth > 0. Dashboard showing message count, age, and error distribution. Provide tooling to inspect, replay, or purge DLQ messages.

---

## Event Schema and Versioning

### Schema structure

```
event_envelope = {
    event_id: uuid,               // unique per event
    event_type: string,           // "order.created", "order.shipped"
    event_version: int,           // schema version (1, 2, 3...)
    timestamp: iso8601,           // when event occurred
    source: string,               // producing service name
    correlation_id: string,       // trace across services
    payload: object,              // event-specific data
}
```

### Schema evolution rules

| Change | Compatibility | Action |
|--------|--------------|--------|
| Add optional field | Backward compatible | Old consumers ignore new fields |
| Add required field | BREAKING | Bump version; update all consumers first |
| Remove field | BREAKING | Deprecate first; remove after all consumers stop reading |
| Rename field | BREAKING | Add new name, keep old name, deprecate old |
| Change field type | BREAKING | Add new field with new type, deprecate old |

### Versioning strategy

```
// Option 1: version in event type — event_type: "order.created.v2"
// Option 2: version in envelope — event_version: 2

// Consumer handles multiple versions:
function handle_order_created(event):
    if event.version == 1:
        // Legacy format: items is a list of strings
        items = [{"name": item, "quantity": 1} for item in event.payload.items]
    else if event.version == 2:
        // Current format: items is a list of objects
        items = event.payload.items
    process_order(event.payload.order_id, items)
```

---

## Message Ordering

| Broker | Ordering guarantee |
|--------|-------------------|
| Redis Streams | Total order within a stream |
| RabbitMQ | FIFO within a single queue (with single consumer) |
| Kafka | Order within a partition (not across partitions) |

**When ordering matters:** State machine transitions, event sourcing, financial transactions.
**When ordering does NOT matter:** Notifications, analytics, independent events.

**Tip:** If you need ordering, route related messages to the same partition/queue using a consistent key (e.g., `order_id`). Accept that ordering across different keys is not guaranteed.

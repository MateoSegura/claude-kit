# Message Queues -- Full Reference

Comprehensive patterns for message queue implementation. All examples use pseudocode.

---

## Redis Streams -- Consumer Group Pattern

```
// Create a stream and consumer group
stream = "orders"
group = "order-processors"
redis.xgroup_create(stream, group, id="0", mkstream=true)

// Producer: add messages to stream
function publish_order_event(order_id, event_type, data):
    redis.xadd(stream, {
        event_type: event_type,
        order_id: order_id,
        payload: serialize(data),
        timestamp: now_iso8601(),
    }, maxlen=100000)  // cap stream length

// Consumer: read from consumer group
function consume_orders(consumer_name):
    while running:
        // ">" means read new messages only
        messages = redis.xreadgroup(
            group, consumer_name,
            streams={stream: ">"},
            count=10,
            block=5000   // block 5 seconds if no messages
        )
        for stream_name, entries in messages:
            for message_id, data in entries:
                try:
                    process_order_event(data)
                    redis.xack(stream, group, message_id)
                catch error:
                    log.error("Failed to process message",
                        message_id=message_id, error=error)
                    // Message remains in PEL (pending entries list)
                    // Will be reclaimed by claim_stale_messages()

// Reclaim messages from crashed consumers
function claim_stale_messages(consumer_name, idle_threshold=60000):
    // Find messages pending for more than idle_threshold ms
    pending = redis.xpending(stream, group, "-", "+", count=100)
    stale_ids = [
        entry.message_id for entry in pending
        if entry.idle_ms > idle_threshold
    ]
    if stale_ids:
        claimed = redis.xclaim(stream, group, consumer_name,
            min_idle_time=idle_threshold, ids=stale_ids)
        for message_id, data in claimed:
            process_order_event(data)
            redis.xack(stream, group, message_id)
```

---

## RabbitMQ -- Exchange Patterns

### Direct exchange (point-to-point routing)

```
// Publisher sends to exchange with routing key
// Consumer binds queue to exchange with matching routing key

// Setup
exchange = channel.declare_exchange("orders", type="direct", durable=true)
queue = channel.declare_queue("order-processing", durable=true)
queue.bind(exchange, routing_key="order.created")

// Publish
exchange.publish(
    message=Message(
        body=serialize(order_data),
        delivery_mode=PERSISTENT,
        headers={"x-retry-count": "0"},
        message_id=generate_uuid(),
    ),
    routing_key="order.created"
)

// Consume
function on_message(message):
    try:
        data = deserialize(message.body)
        process_order(data)
        message.ack()
    catch error:
        handle_failure(message, error)
```

### Topic exchange (pattern-based routing)

```
// Routing key patterns with wildcards:
//   * matches one word
//   # matches zero or more words

exchange = channel.declare_exchange("events", type="topic", durable=true)

// Queue binds with pattern
notification_queue.bind(exchange, routing_key="order.*")       // order.created, order.shipped
analytics_queue.bind(exchange, routing_key="#")                 // all events
payment_queue.bind(exchange, routing_key="order.payment.*")    // order.payment.success, etc.

// Publish with specific routing key
exchange.publish(message, routing_key="order.payment.success")
// -> Delivered to notification_queue, analytics_queue, and payment_queue
```

### Dead letter exchange (DLX)

```
// Setup: queue with dead-letter-exchange argument
dlx = channel.declare_exchange("orders.dlx", type="direct")
dlq = channel.declare_queue("orders.dlq", durable=true)
dlq.bind(dlx, routing_key="order-processing")

// Main queue points to DLX on rejection/expiry
main_queue = channel.declare_queue("order-processing",
    durable=true,
    arguments={
        "x-dead-letter-exchange": "orders.dlx",
        "x-dead-letter-routing-key": "order-processing",
        "x-message-ttl": 86400000,     // 24h max time in queue
    }
)

// Consumer: nack with requeue=false sends to DLX
function on_message(message):
    attempt = int(message.headers.get("x-retry-count", 0))
    try:
        process(message.body)
        message.ack()
    catch error:
        if attempt >= MAX_RETRIES:
            // Reject without requeue -> goes to DLX -> DLQ
            message.reject(requeue=false)
        else:
            // Republish with incremented retry count
            message.ack()
            exchange.publish(
                Message(
                    body=message.body,
                    headers={...message.headers, "x-retry-count": str(attempt + 1)},
                ),
                routing_key="order-processing"
            )
```

---

## Kafka -- Patterns

### Producer patterns

```
// Producer with key-based partitioning
producer = KafkaProducer(
    bootstrap_servers=["kafka-1:9092", "kafka-2:9092"],
    acks="all",              // wait for all replicas to acknowledge
    retries=3,               // retry on transient errors
    max_in_flight=5,         // max unacknowledged requests (enable idempotence if > 1)
    enable_idempotence=true, // prevents duplicate messages on retry
    compression="lz4",       // compress messages
)

function publish_event(topic, key, event):
    // Key determines partition: same key always goes to same partition
    producer.send(
        topic=topic,
        key=serialize(key),       // e.g., order_id for per-order ordering
        value=serialize(event),
        headers=[
            ("event-type", event.type),
            ("event-version", str(event.version)),
            ("correlation-id", event.correlation_id),
        ]
    )

// Batch publishing for throughput
producer.batch_size = 16384      // 16KB batch
producer.linger_ms = 5           // wait up to 5ms to fill batch
```

### Consumer group patterns

```
consumer = KafkaConsumer(
    topics=["orders"],
    bootstrap_servers=["kafka-1:9092"],
    group_id="order-processors",
    auto_offset_reset="earliest",    // start from beginning if no committed offset
    enable_auto_commit=false,        // manual commit for at-least-once
    max_poll_records=100,            // process in batches
)

function consume():
    while running:
        records = consumer.poll(timeout=1000)
        for record in records:
            try:
                process_event(record.value, record.headers)
            catch error:
                handle_failure(record, error)
        // Commit offsets after processing batch
        consumer.commit()

// Partition assignment:
// - Kafka assigns partitions to consumers in a group
// - Each partition is assigned to exactly one consumer
// - If consumers > partitions, some consumers are idle
// - If partitions > consumers, some consumers handle multiple partitions
// - Rebalance occurs when consumers join/leave
```

### Handling rebalances

```
// Rebalance listener: save state before partitions are revoked
class RebalanceHandler:
    function on_partitions_revoked(partitions):
        // Commit current offsets before losing partitions
        consumer.commit()
        // Flush any buffered state
        flush_processing_buffer()

    function on_partitions_assigned(partitions):
        // Initialize state for new partitions
        for partition in partitions:
            load_partition_state(partition)

consumer.subscribe(topics=["orders"], listener=RebalanceHandler())
```

---

## Event Schema Registry

```
// Central schema registry stores and validates event schemas
// Producers register schemas; consumers validate against registry

class SchemaRegistry:
    function register(event_type, version, schema):
        // Check compatibility with previous version
        if version > 1:
            previous = get_schema(event_type, version - 1)
            if not is_backward_compatible(previous, schema):
                raise IncompatibleSchemaError(
                    "Schema version {version} is not backward compatible"
                )
        store(event_type, version, schema)

    function validate(event_type, version, payload):
        schema = get_schema(event_type, version)
        if not schema:
            raise UnknownSchemaError(event_type, version)
        errors = schema.validate(payload)
        if errors:
            raise ValidationError(errors)

// Compatibility modes:
// BACKWARD: new schema can read old data (add optional fields, remove fields)
// FORWARD: old schema can read new data (add fields with defaults, remove optional fields)
// FULL: both backward and forward compatible
// NONE: no compatibility check (dangerous)
```

---

## Consumer Idempotency Pattern

```
// Ensure each message is processed exactly once using deduplication

class IdempotentConsumer:
    processed_store: KeyValueStore   // Redis, DB table, etc.
    ttl: duration = 7 days

    function process_if_new(message):
        message_id = message.headers.get("message-id")
        if not message_id:
            // No message ID: process without deduplication (at-least-once)
            return process(message)

        // Check if already processed
        if processed_store.exists("processed:" + message_id):
            log.info("Duplicate message skipped", message_id=message_id)
            return  // already processed

        // Process and mark as done atomically (if possible)
        result = process(message)
        processed_store.set("processed:" + message_id, "done", ttl=ttl)
        return result

// For stronger guarantees: use transactional outbox pattern
// Process message and store deduplication key in same DB transaction
function process_with_dedup(db, message):
    message_id = message.headers.get("message-id")
    within transaction(db):
        // Check if already processed
        existing = db.query(
            "SELECT 1 FROM processed_messages WHERE message_id = ?", message_id
        )
        if existing:
            return  // already processed

        // Process business logic
        handle_business_logic(db, message.payload)

        // Mark as processed
        db.insert("processed_messages", {
            message_id: message_id,
            processed_at: now(),
        })
    // Both committed atomically: no duplicates possible
```

---

## Monitoring and Alerting

### Key metrics to track

| Metric | Alert threshold | Meaning |
|--------|----------------|---------|
| Consumer lag | > 10,000 messages | Consumers falling behind producers |
| DLQ depth | > 0 | Messages are failing processing |
| Processing latency p99 | > SLA target | Consumers too slow |
| Consumer group size | < expected count | Consumer instances may be down |
| Message age (oldest unprocessed) | > 5 minutes | Processing is stuck or too slow |
| Error rate | > 1% of messages | Processing failures increasing |

### Consumer lag monitoring

```
function check_consumer_lag():
    for topic in monitored_topics:
        for partition in topic.partitions:
            latest_offset = get_latest_offset(topic, partition)
            committed_offset = get_committed_offset(group, topic, partition)
            lag = latest_offset - committed_offset
            metrics.gauge("consumer_lag",
                value=lag,
                tags={topic: topic.name, partition: partition, group: group}
            )
            if lag > LAG_ALERT_THRESHOLD:
                alert("Consumer lag critical",
                    topic=topic.name, partition=partition, lag=lag)
```

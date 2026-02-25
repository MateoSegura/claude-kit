# Database Patterns -- Full Reference

Comprehensive patterns for database design, optimization, and operations in backend services.

---

## Connection Pool Tuning Guide

### Sizing formula

```
// Maximum connections per application instance:
max_pool = (DB_max_connections - reserved_for_admin) / number_of_app_instances

// Example: DB allows 200 connections, 10 reserved for admin, 4 app instances
// max_pool = (200 - 10) / 4 = 47 per instance
```

### Pool configuration by workload type

```
// Web API (short-lived queries, high concurrency):
pool:
    min: 5
    max: 25
    idle_timeout: 300s
    max_lifetime: 3600s
    validation: on_checkout

// Background worker (long-running queries, low concurrency):
pool:
    min: 2
    max: 10
    idle_timeout: 600s
    max_lifetime: 3600s
    validation: on_checkout

// Mixed workload (separate pools for reads and writes):
write_pool:
    min: 3
    max: 15
    target: primary_host
read_pool:
    min: 5
    max: 30
    target: replica_host
```

### Monitoring pool health

Key metrics to track:
- **Active connections**: currently in use -- should not stay near max
- **Idle connections**: available in pool -- should stay above min
- **Wait count**: requests waiting for a connection -- should be near zero
- **Wait time**: average time waiting -- alert if > 100ms
- **Timeout count**: requests that failed to get a connection -- critical alert

---

## Migration Patterns for Zero-Downtime Deployments

### Pattern 1: Add a column safely

```
// Step 1: Add column as nullable (no lock, no rewrite)
ALTER TABLE orders ADD COLUMN discount_code VARCHAR(50) NULL;

// Step 2: Deploy code that writes to the new column
// Step 3: Backfill existing rows (in batches to avoid long locks)

// Pseudocode for batch backfill:
function backfill_discount_codes():
    batch_size = 1000
    last_id = 0
    loop:
        rows = db.query(
            "SELECT id FROM orders WHERE id > ? AND discount_code IS NULL
             ORDER BY id LIMIT ?", last_id, batch_size
        )
        if rows is empty:
            break
        ids = [row.id for row in rows]
        db.execute(
            "UPDATE orders SET discount_code = 'NONE'
             WHERE id IN (?)", ids
        )
        db.commit()
        last_id = rows[-1].id
        sleep(0.1)  // throttle to avoid overwhelming the DB

// Step 4: Add NOT NULL constraint (after all rows are backfilled)
ALTER TABLE orders ALTER COLUMN discount_code SET NOT NULL;
```

### Pattern 2: Rename a column safely (3-step deployment)

```
// Deployment 1: Add new column, write to both
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
UPDATE users SET full_name = name;  // backfill
// Code writes to both 'name' and 'full_name', reads from 'full_name'

// Deployment 2: Stop writing to old column
// Code only reads/writes 'full_name'

// Deployment 3: Drop old column
ALTER TABLE users DROP COLUMN name;
```

### Pattern 3: Add index without downtime

```
// PostgreSQL: CREATE INDEX CONCURRENTLY (does not lock the table)
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders (user_id);

// MySQL 5.6+: Online DDL (default behavior for most ALTER TABLE)
ALTER TABLE orders ADD INDEX idx_orders_user_id (user_id), ALGORITHM=INPLACE, LOCK=NONE;

// Monitor progress: check pg_stat_progress_create_index (Postgres)
// or SHOW PROCESSLIST (MySQL) for long-running DDL
```

---

## Indexing Deep Dive

### B-tree index characteristics

```
// B-tree indexes support:
//   =, <, >, <=, >=, BETWEEN, IN, IS NULL
//   ORDER BY (if index matches sort order)
//   MIN/MAX (index-only scan)
//
// B-tree does NOT efficiently support:
//   LIKE '%prefix'  (leading wildcard)
//   Functions on indexed column: WHERE LOWER(email) = ?
//     (use expression index instead: CREATE INDEX ON users (LOWER(email)))
//   NOT IN, != (must scan entire index)
```

### Partial indexes (Postgres)

```
// Index only rows that match a condition -- smaller, faster
CREATE INDEX idx_active_orders ON orders (created_at)
    WHERE status IN ('pending', 'processing');

// Useful for: soft deletes, status filtering, tenant isolation
CREATE INDEX idx_undeleted_users ON users (email) WHERE deleted_at IS NULL;
```

### Index-only scans (covering indexes)

```
// If all columns in the query are in the index, DB skips table lookup
// Postgres:
CREATE INDEX idx_orders_summary ON orders (user_id) INCLUDE (status, total, created_at);

// Query that benefits:
SELECT status, total, created_at FROM orders WHERE user_id = '123';
// -> Index-only scan, no heap fetch
```

### Diagnosing slow queries

```
// Always check the query plan before and after adding indexes:
EXPLAIN ANALYZE <your query>;

// Look for:
//   Seq Scan on large tables -> needs index
//   Nested Loop with inner Seq Scan -> missing join index
//   Sort with high cost -> consider index on ORDER BY columns
//   Rows Removed by Filter >> Rows output -> index not selective enough
```

---

## N+1 Solutions in Detail

### DataLoader pattern

```
// Batch and cache database lookups within a single request
class DataLoader:
    pending_keys: set
    cache: map[key -> value]
    batch_load_fn: function(keys) -> map[key -> value]

    function load(key) -> Future:
        if key in cache:
            return cache[key]
        pending_keys.add(key)
        // Schedule batch execution at end of current tick
        schedule_batch_if_needed()
        return future_for(key)

    function execute_batch():
        keys = pending_keys
        pending_keys = empty_set
        results = batch_load_fn(keys)
        for key, value in results:
            cache[key] = value
            resolve_future(key, value)

// Usage:
order_items_loader = DataLoader(
    batch_load_fn = function(order_ids):
        items = db.query("SELECT * FROM order_items WHERE order_id IN (?)", order_ids)
        return group_by(items, "order_id")
)

// Each call to load() batches automatically:
items_for_order_1 = order_items_loader.load(order_1_id)
items_for_order_2 = order_items_loader.load(order_2_id)
// Executes ONE query: SELECT * FROM order_items WHERE order_id IN (1, 2)
```

### Denormalization for read performance

```
// Store computed/aggregated data alongside the parent record
// Trade-off: write complexity increases, read performance improves dramatically

table orders:
    id: uuid
    user_id: uuid
    status: string
    item_count: int          // denormalized from COUNT(order_items)
    total_amount: decimal    // denormalized from SUM(order_items.price * quantity)
    user_name: string        // denormalized from users.name (snapshot at order time)

// Update denormalized fields when source data changes:
// Option A: Update in same transaction (strong consistency)
// Option B: Update via event handler (eventual consistency, less coupling)
```

---

## Transaction Patterns

### Optimistic concurrency control

```
// Use a version column to detect concurrent modifications
table accounts:
    id: uuid
    balance: decimal
    version: int (default 1)

function transfer(from_id, to_id, amount):
    from_account = db.query("SELECT * FROM accounts WHERE id = ?", from_id)
    to_account = db.query("SELECT * FROM accounts WHERE id = ?", to_id)

    if from_account.balance < amount:
        raise InsufficientFunds

    // Update with version check
    rows_affected = db.execute(
        "UPDATE accounts SET balance = balance - ?, version = version + 1
         WHERE id = ? AND version = ?",
        amount, from_id, from_account.version
    )
    if rows_affected == 0:
        raise ConcurrentModification("Account was modified by another transaction")

    db.execute(
        "UPDATE accounts SET balance = balance + ?, version = version + 1
         WHERE id = ? AND version = ?",
        amount, to_id, to_account.version
    )
    db.commit()
```

### Advisory locks

```
// Use advisory locks for operations that need mutual exclusion
// without holding row locks for extended periods

function process_payment(order_id):
    lock_key = hash(order_id)
    acquired = db.query("SELECT pg_try_advisory_lock(?)", lock_key)
    if not acquired:
        raise AlreadyProcessing("Payment for this order is already being processed")
    try:
        // ... process payment ...
    finally:
        db.query("SELECT pg_advisory_unlock(?)", lock_key)
```

---

## Read Replica Routing

```
// Middleware/decorator approach for automatic routing
class ReadReplicaRouter:
    primary_pool: ConnectionPool
    replica_pool: ConnectionPool
    sticky_duration: duration = 5s
    recent_writes: map[session_id -> timestamp]

    function get_connection(session_id, operation):
        if operation == WRITE:
            recent_writes[session_id] = now()
            return primary_pool.acquire()

        // Read-after-write: route to primary if recent write
        last_write = recent_writes.get(session_id)
        if last_write and elapsed(last_write) < sticky_duration:
            return primary_pool.acquire()

        return replica_pool.acquire()
```

**Replication lag monitoring:**
- Track `seconds_behind_master` (MySQL) or `replay_lag` (Postgres)
- Alert if lag exceeds acceptable threshold (typically 1-5 seconds)
- Consider circuit-breaking reads to replica if lag is too high

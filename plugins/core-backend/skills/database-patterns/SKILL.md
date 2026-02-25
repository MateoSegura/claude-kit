---
name: core-backend:database-patterns
description: "Database patterns for backend services: connection pooling, migration strategies, ORM vs query builder vs raw SQL tradeoffs, indexing strategy, N+1 problem detection and prevention, read replicas, sharding concepts, and transaction isolation levels. Load when designing database schemas, optimizing queries, or choosing data access strategies."
user-invocable: false
---

# Database Patterns -- Quick Reference

## Additional resources

- [database-reference.md](database-reference.md) -- Full patterns: connection pooling configuration, migration workflows, indexing strategies, N+1 solutions, read replica routing, sharding approaches

---

## Data Access Strategy Decision Matrix

| Need | Approach | Trade-off |
|------|----------|-----------|
| Rapid prototyping, simple CRUD | ORM | Magic can hide performance issues; migrations are simpler |
| Complex queries, reporting | Query Builder | More verbose than ORM; more readable than raw SQL |
| Maximum performance, complex joins | Raw SQL | No abstraction safety; harder to maintain |
| Type-safe queries at compile time | Code-generated query builder | Build step required; excellent safety |
| Testable data access | Repository Pattern | Extra abstraction; clean separation of concerns |

---

## Connection Pooling

```
// Pool configuration -- tune based on load testing
pool_config:
    min_connections: 5            // keep warm for baseline load
    max_connections: 20           // cap to prevent overwhelming DB
    max_overflow: 10              // temporary extra connections under burst
    connection_timeout: 30s       // max wait for connection from pool
    idle_timeout: 300s            // close idle connections after 5 min
    max_lifetime: 3600s           // recycle connections older than 1 hour
    validation_on_checkout: true  // test connection before use
```

**Rules:**
- Never create a new connection per request -- use a pool
- Set `max_connections` based on DB server limits divided by number of app instances
- Enable connection validation to catch stale connections (especially behind load balancers)
- Monitor pool exhaustion -- if requests wait for connections, increase pool size or optimize query duration

---

## Migration Strategy

### Forward-only migrations (recommended)

```
// Migration file naming: <timestamp>_<description>.<ext>
// Example: 20240115_120000_add_orders_table.sql

// Each migration is a single forward step. Never edit applied migrations.
// To undo, create a new migration that reverses the change.
```

### Safe migration patterns for zero-downtime deployments

| Operation | Safe approach |
|-----------|--------------|
| Add column | Add with DEFAULT or as nullable; backfill later |
| Remove column | Deploy code that stops reading it first; drop in next release |
| Rename column | Add new column, backfill, deploy code using new name, drop old |
| Add index | Use CONCURRENTLY (Postgres) or online DDL to avoid table locks |
| Change column type | Add new column with new type, migrate data, swap references |

**Rules:**
- Never drop a column that running code still reads
- Never rename a column in a single deployment
- Always test migrations against a copy of production data
- Keep migrations small and independently deployable

---

## Indexing Strategy

### When to add an index

- Columns in WHERE clauses used frequently
- Columns in JOIN conditions
- Columns in ORDER BY / GROUP BY
- Foreign key columns (often missed)

### When NOT to add an index

- Tables with very few rows (full scan is faster)
- Columns with very low cardinality (e.g., boolean) unless combined in composite index
- Write-heavy tables where index maintenance outweighs read benefit

### Composite index ordering

```
// Index on (A, B, C) supports queries on:
//   WHERE A = ?
//   WHERE A = ? AND B = ?
//   WHERE A = ? AND B = ? AND C = ?
//
// It does NOT efficiently support:
//   WHERE B = ?          (skips leading column)
//   WHERE B = ? AND C = ? (skips leading column)
//
// Rule: order columns by selectivity (most selective first)
// unless the query pattern requires a different order for range scans
```

### Covering indexes

```
// Include all columns needed by the query to avoid table lookup
// Postgres: CREATE INDEX idx_name ON orders (user_id) INCLUDE (status, total);
// MySQL: CREATE INDEX idx_name ON orders (user_id, status, total);
```

---

## N+1 Problem

### Detection

```
// Symptom: loading a list of items, then loading related data one-by-one
orders = db.query("SELECT * FROM orders WHERE user_id = ?", user_id)
for order in orders:
    // N additional queries -- one per order!
    items = db.query("SELECT * FROM order_items WHERE order_id = ?", order.id)
```

### Solutions

| Approach | How |
|----------|-----|
| Eager loading / JOIN | Load related data in the same query |
| Batch loading | Collect IDs, load all related data in one IN query |
| DataLoader pattern | Automatically batch and cache within a request |
| Denormalization | Store aggregated data alongside the parent record |

```
// GOOD: batch loading
orders = db.query("SELECT * FROM orders WHERE user_id = ?", user_id)
order_ids = [order.id for order in orders]
items = db.query("SELECT * FROM order_items WHERE order_id IN (?)", order_ids)
// Group items by order_id in application code
```

---

## Transaction Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Use Case |
|-------|-----------|-------------------|-------------|----------|
| READ UNCOMMITTED | Possible | Possible | Possible | Almost never -- analytics on approximate data |
| READ COMMITTED | No | Possible | Possible | Default for most apps (Postgres default) |
| REPEATABLE READ | No | No | Possible | Financial calculations within a transaction |
| SERIALIZABLE | No | No | No | Critical operations (account transfers, inventory) |

**Rules:**
- Use READ COMMITTED as default -- it prevents dirty reads without excessive locking
- Use SERIALIZABLE only for operations that require absolute consistency (and accept lower throughput)
- Prefer optimistic concurrency (version column) over SERIALIZABLE for better performance
- Always set explicit transaction boundaries -- never rely on auto-commit for multi-step operations

---

## Read Replicas

```
// Route reads to replica, writes to primary
function get_connection(operation_type):
    if operation_type == READ:
        return replica_pool.acquire()
    else:
        return primary_pool.acquire()

// Caution: replication lag means replicas may be seconds behind
// For read-after-write consistency:
//   1. Read from primary immediately after write
//   2. Or use session-level routing (sticky to primary for N seconds after write)
```

---

## Sharding Concepts

| Strategy | How | Best for |
|----------|-----|----------|
| Range-based | Shard by ID range (1-1M, 1M-2M) | Sequential access, time-series data |
| Hash-based | hash(key) % shard_count | Uniform distribution, random access |
| Geography | Shard by region (US, EU, APAC) | Data locality, compliance requirements |
| Tenant-based | One shard per tenant | Multi-tenant SaaS, isolation requirements |

**Rules:**
- Avoid cross-shard queries -- they are expensive and complex
- Choose a shard key that distributes data evenly and aligns with query patterns
- Plan for rebalancing -- adding shards should not require full data migration
- Consider starting with read replicas before sharding -- sharding adds significant complexity

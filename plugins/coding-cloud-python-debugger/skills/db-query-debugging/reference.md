# DB Query Debugging — Deep Reference

## pg_stat_statements

### Setup

```sql
-- Enable extension (requires superuser; add to postgresql.conf)
-- shared_preload_libraries = 'pg_stat_statements'  ← in postgresql.conf

-- Enable in database
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Verify it's active
SELECT * FROM pg_stat_statements LIMIT 1;
```

### Useful Queries

```sql
-- Top queries by total execution time (last reset period)
SELECT
    left(query, 100) AS query_snippet,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round((total_exec_time / calls)::numeric, 2) AS avg_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Queries with high variance (intermittent slow queries)
SELECT
    left(query, 100) AS query_snippet,
    calls,
    round((total_exec_time / calls)::numeric, 2) AS avg_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    round((stddev_exec_time / NULLIF(total_exec_time / calls, 0))::numeric, 2) AS cv
FROM pg_stat_statements
WHERE calls > 100
ORDER BY cv DESC
LIMIT 10;

-- Queries with most I/O (buffer reads)
SELECT
    left(query, 100) AS query_snippet,
    calls,
    shared_blks_read + local_blks_read AS total_disk_reads,
    shared_blks_hit + local_blks_hit AS total_cache_hits,
    round(100.0 * (shared_blks_hit) /
          NULLIF(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_pct
FROM pg_stat_statements
ORDER BY total_disk_reads DESC
LIMIT 10;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

---

## Lock Contention Analysis

### Find Current Blocking Locks

```sql
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS blocked_duration
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking
    ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.wait_event_type = 'Lock';
```

### Lock Types and Their Contenders

| Lock Mode | Conflicts With | Common Cause |
|-----------|---------------|--------------|
| `AccessShareLock` | `AccessExclusiveLock` | SELECT vs DDL (ALTER TABLE) |
| `RowShareLock` | `ExclusiveLock`, `AccessExclusiveLock` | SELECT FOR UPDATE vs lock/DDL |
| `RowExclusiveLock` | `ShareLock`, `ExclusiveLock`, etc. | INSERT/UPDATE/DELETE vs VACUUM FULL |
| `ExclusiveLock` | Most modes | Explicit LOCK TABLE |
| `AccessExclusiveLock` | All | ALTER TABLE, TRUNCATE, VACUUM FULL, DROP INDEX |

### Deadlock Detection

```sql
-- PostgreSQL logs deadlocks automatically when log_lock_waits = on
-- Check log for: "ERROR:  deadlock detected"

-- Find long-running transactions (potential lock holders)
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND (now() - pg_stat_activity.query_start) > interval '30 seconds'
ORDER BY duration DESC;

-- Kill a blocking query (use with caution)
SELECT pg_cancel_backend(<pid>);   -- send SIGINT (graceful)
SELECT pg_terminate_backend(<pid>); -- send SIGTERM (hard kill)
```

### Deadlock Pattern (asyncpg)

```python
# Deadlock scenario:
# Task A: UPDATE users SET x=1 WHERE id=1; then UPDATE orders SET y=2 WHERE id=1;
# Task B: UPDATE orders SET y=3 WHERE id=1; then UPDATE users SET x=4 WHERE id=1;

# Fix: always acquire locks in the same order
# Both tasks: UPDATE users first, then UPDATE orders

# OR: use SELECT FOR UPDATE to lock both rows at start of transaction
async with pool.acquire() as conn:
    async with conn.transaction():
        # Lock in consistent order
        await conn.fetchrow("SELECT id FROM users WHERE id=$1 FOR UPDATE", user_id)
        await conn.fetchrow("SELECT id FROM orders WHERE id=$1 FOR UPDATE", order_id)
        # Now safe to update both
        await conn.execute("UPDATE users SET x=$1 WHERE id=$2", x, user_id)
        await conn.execute("UPDATE orders SET y=$1 WHERE id=$2", y, order_id)
```

---

## Connection Pool Exhaustion

### Scenario Analysis

**Scenario 1: Long-running transactions holding connections**

```sql
-- Check for idle-in-transaction connections
SELECT pid, usename, application_name, state, query,
       now() - state_change AS idle_duration
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY idle_duration DESC;
```

Fix: set `idle_in_transaction_session_timeout` in PostgreSQL:

```sql
-- Kill sessions idle in transaction for > 30s
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
SELECT pg_reload_conf();
```

**Scenario 2: Connections not returned after exception**

```python
# BUG: connection not released on exception
async def bad_handler():
    conn = await pool.acquire()
    result = await conn.fetch("SELECT ...")  # raises → connection leaked!
    await pool.release(conn)
    return result

# FIX: always use context manager
async def good_handler():
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT ...")  # auto-released on exit
```

**Scenario 3: Pool size too small for concurrency**

Rule of thumb: `max_size = num_workers × avg_concurrent_db_ops_per_worker × 1.2`

For asyncio apps: `max_size` can be much smaller than thread pools because tasks yield during I/O. Typical: 10-20 connections for 100-200 concurrent requests.

---

## Transaction Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Use Case |
|-------|-----------|--------------------|--------------|----|
| READ UNCOMMITTED | Possible (PG: no) | Possible | Possible | N/A in PostgreSQL |
| READ COMMITTED (default) | No | Possible | Possible | Most OLTP |
| REPEATABLE READ | No | No | Possible (PG: no) | Consistent snapshots |
| SERIALIZABLE | No | No | No | Financial transactions |

```python
# asyncpg — set isolation level
async with pool.acquire() as conn:
    async with conn.transaction(isolation='repeatable_read'):
        # Consistent snapshot throughout this transaction
        snapshot1 = await conn.fetchval("SELECT count(*) FROM orders")
        await asyncio.sleep(0)  # yields; other coroutines run
        snapshot2 = await conn.fetchval("SELECT count(*) FROM orders")
        # snapshot1 == snapshot2 guaranteed under REPEATABLE READ
        assert snapshot1 == snapshot2
```

---

## asyncpg-Specific Issues

### Prepared Statement Cache Conflicts

asyncpg caches prepared statements per connection. If a table schema changes between queries (e.g., during migration), the cached plan becomes invalid.

```
asyncpg.exceptions.InvalidCachedStatementError: cached plan must not change result type
```

Fix:

```python
# Option 1: disable prepared statement cache on pool
pool = await asyncpg.create_pool(dsn, statement_cache_size=0)

# Option 2: use fetch with explicit type annotation
await conn.fetch("SELECT id::int, name::text FROM users")
```

### Type Codec Registration

asyncpg maps PostgreSQL types to Python types. Custom types need explicit registration:

```python
# Register UUID codec (returns uuid.UUID instead of str)
import uuid
await conn.set_type_codec(
    'uuid', encoder=str, decoder=uuid.UUID, schema='pg_catalog', format='text'
)

# Register JSONB codec
import json
await conn.set_type_codec(
    'jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog', format='text'
)
```

### Parameter Type Mismatches

```python
# asyncpg uses $1, $2, ... placeholders (PostgreSQL protocol)
# Type is inferred from Python type — pass explicitly if needed:
await conn.fetch("SELECT * FROM users WHERE id = $1", 42)        # int → int4
await conn.fetch("SELECT * FROM users WHERE id = $1::bigint", 42) # force int8

# GOTCHA: Python int can be int2, int4, or int8 — PostgreSQL infers from context
# If column is BIGINT but you pass a small int, use explicit cast
```

---

## Alembic Migration Debugging

### Common Migration Failures

**Lock timeout during migration on live DB**

```python
# In alembic/env.py — set lock timeout before migration
def run_migrations_online():
    with engine.connect() as conn:
        conn.execute(text("SET lock_timeout = '5s'"))
        conn.execute(text("SET statement_timeout = '120s'"))
        context.configure(connection=conn, ...)
        with context.begin_transaction():
            context.run_migrations()
```

**Check current migration state**

```bash
# Show current revision
alembic current

# Show pending migrations
alembic history --indicate-current

# Show SQL for a migration without executing
alembic upgrade head --sql > migration.sql
```

**Detect autogenerate drift**

```bash
# Show what alembic would generate for current model state
alembic revision --autogenerate --dry-run
# If this produces unexpected changes → models and DB are out of sync
```

**Repair broken migration chain**

```bash
# Mark a migration as applied without running it (emergency fix)
alembic stamp <revision>

# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>
```

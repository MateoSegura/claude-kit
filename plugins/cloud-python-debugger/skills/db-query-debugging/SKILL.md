---
name: cloud-python-debugger:db-query-debugging
description: "Quick reference for debugging Python database performance — EXPLAIN ANALYZE interpretation, slow query patterns, asyncpg connection pool diagnostics, SQLAlchemy 2.0 session pitfalls, and N+1 detection techniques."
user-invocable: false
---

# DB Query Debugging — Quick Reference

For pg_stat_statements, lock contention, connection pool exhaustion, transaction isolation, asyncpg-specific issues, and alembic migration debugging, see [reference.md](reference.md).

## EXPLAIN ANALYZE — Reading Output

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
```

### Key Numbers

| Field | Meaning | What to Look For |
|-------|---------|------------------|
| `cost=X..Y` | Planner estimate (not real time) | Large Y = planner thinks it's expensive |
| `actual time=X..Y` | Real execution time (ms) | actual >> cost estimate → stale statistics |
| `rows=N` | Actual rows returned | rows >> estimated rows → run `ANALYZE` |
| `Buffers: hit=N` | Pages read from cache | Low hit % → I/O bound query |
| `Buffers: read=N` | Pages read from disk | High read → missing cache or bad index |

### Node Types and What They Mean

| Node | Meaning | Performance Signal |
|------|---------|-------------------|
| `Seq Scan` | Full table scan | Problematic on large tables; add index |
| `Index Scan` | Uses B-tree index | Good for selective queries |
| `Index Only Scan` | Reads only index, no heap | Best case — no heap access |
| `Bitmap Heap Scan` | Bulk fetch via bitmap | Normal for moderate selectivity |
| `Hash Join` | Hash table join | Good for large joins |
| `Nested Loop` | Row-by-row join | Problematic with large inner set |
| `Sort` | In-memory or disk sort | Large sort → add ORDER BY index |
| `Hash` | Building hash table | Memory pressure if large |

### Reading a Slow Query Plan

```
Nested Loop  (cost=0.43..8992.03 rows=500 width=64)
             (actual time=0.048..4521.3 rows=500 loops=1)
  ->  Seq Scan on orders  (actual time=0.02..1.1 rows=500 loops=1)
        Filter: (status = 'pending')
        Rows Removed by Filter: 9500    ← 95% filtered → add index on status
  ->  Index Scan on users  (actual time=0.008..0.009 rows=1 loops=500)
        Index Cond: (id = orders.user_id)
        ← 500 index scans → N+1 pattern; use JOIN instead
```

---

## Slow Query Patterns

| Pattern | Symptom in EXPLAIN | Fix |
|---------|-------------------|-----|
| Missing index | `Seq Scan` on large table | `CREATE INDEX CONCURRENTLY` |
| Stale statistics | estimated rows << actual rows | `ANALYZE tablename` |
| N+1 in ORM | Many identical queries in logs | `selectinload()` / `joinedload()` |
| LIKE with leading wildcard | `Seq Scan` despite index | Use full-text search or `pg_trgm` GIN index |
| Function on indexed column | Index not used | Index the expression: `CREATE INDEX ON t (lower(col))` |
| Implicit type cast | Index not used | Match types: avoid `WHERE int_col = '42'` |
| Large offset pagination | `Sort + Limit` with high offset | Keyset pagination: `WHERE id > last_id` |

---

## asyncpg Connection Pool Diagnostics

### Pool Parameters

```python
pool = await asyncpg.create_pool(
    dsn,
    min_size=5,           # connections created at startup
    max_size=20,          # hard limit on connections
    max_inactive_connection_lifetime=300,  # close idle conns after 5min
    command_timeout=30,   # per-query timeout (seconds)
    max_queries=50000,    # max queries before conn is recycled
)
```

### Inspect Pool State

```python
# asyncpg does not expose pool internals directly via public API.
# Use these workarounds:

# Check connections in pg_stat_activity
async with pool.acquire() as conn:
    rows = await conn.fetch("""
        SELECT count(*), state, wait_event_type, wait_event
        FROM pg_stat_activity
        WHERE application_name = 'myapp'
        GROUP BY state, wait_event_type, wait_event
    """)
    for r in rows:
        print(r)
```

### Pool Exhaustion Symptoms

- `asyncio.TimeoutError` from `pool.acquire(timeout=N)` — no free connection in N seconds
- Requests queue up; p99 latency spikes
- `pg_stat_activity` shows `max_size` connections for your app, all `active` or `idle in transaction`

### Connection Leak Detection

```python
# Override acquire to track callers
import traceback, time
_active_conns = {}

class TrackedPool:
    def __init__(self, pool):
        self._pool = pool

    async def acquire(self, **kw):
        conn = await self._pool.acquire(**kw)
        _active_conns[id(conn)] = {
            'stack': traceback.extract_stack(),
            'acquired_at': time.monotonic(),
        }
        return conn

    async def release(self, conn, **kw):
        _active_conns.pop(id(conn), None)
        await self._pool.release(conn, **kw)

    def dump_leaked(self, threshold_sec=30):
        now = time.monotonic()
        for cid, info in _active_conns.items():
            held = now - info['acquired_at']
            if held > threshold_sec:
                print(f"Connection {cid} held {held:.1f}s:")
                print("".join(traceback.format_list(info['stack'])))
```

---

## SQLAlchemy 2.0 Session Pitfalls

### See Generated SQL

```python
# Method 1: echo=True (all queries to stderr)
engine = create_async_engine(url, echo=True)

# Method 2: compile statement without executing
from sqlalchemy.dialects import postgresql
stmt = select(User).where(User.id == 42)
print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

# Method 3: event listener for slow query logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.monotonic())

@event.listens_for(Engine, "after_cursor_execute")
def after_execute(conn, cursor, statement, params, context, executemany):
    total = time.monotonic() - conn.info['query_start_time'].pop()
    if total > 0.5:  # log queries slower than 500ms
        print(f"SLOW QUERY ({total:.3f}s): {statement[:200]}")
```

### N+1 Detection

```python
# BAD: N+1 — loads each user's orders separately
async with AsyncSession(engine) as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
    for user in users:
        # Each access triggers a separate SELECT — N+1!
        print(user.orders)

# GOOD: eager load with selectinload
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(User).options(selectinload(User.orders))
)
users = result.scalars().all()
# One SELECT for users + one SELECT for all orders — 2 queries total
```

### Common SQLAlchemy 2.0 Async Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `MissingGreenlet` error | Exception on attribute access | Use `selectinload` / `joinedload` before leaving session |
| `DetachedInstanceError` | Attribute access after session closes | Access lazy attributes before `session.close()` |
| Transaction never committed | Data not persisted | Ensure `await session.commit()` is called |
| Connection leak | Pool exhaustion over time | Always use `async with AsyncSession(engine) as session` |
| `lazy='raise'` not set | Silent N+1 in tests | Set `lazy='raise'` on relationships to detect at test time |

---

## N+1 Quick Detection

```bash
# Count queries per request using SQLAlchemy events + counter
# Look for: many identical SELECT queries in logs (same SQL, different WHERE clause)

# pg_stat_statements — top queries by call count
SELECT query, calls, total_exec_time / calls AS avg_ms, rows / calls AS avg_rows
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 20;
```

## Additional Resources

- [reference.md](reference.md) — pg_stat_statements setup and queries, lock contention analysis, connection pool exhaustion scenarios, transaction isolation levels and deadlocks, asyncpg-specific issues, alembic migration debugging

# Profiling Analysis — Deep Reference

## Flame Graph Interpretation Patterns

### CPU Flame Graph Patterns (py-spy)

**Pattern: Wide Plateau at Top**

```
  [json.loads]██████████████████████████████████
  [parse_body]██████████████████████████████████
  [handle_request]██████████████████████████████
```

Interpretation: A single function dominates CPU time. Direct optimization target.
Action: Rewrite hot path, use faster library (e.g., `orjson` instead of `json`), or cache results.

**Pattern: Tall Narrow Stacks (Many Calls)**

```
  [str.format]█[str.format]█[str.format]█[str.format]█
  [log_line] █ [log_line] █ [log_line] █ [log_line] █
  [process]  █████████████████████████████████████████
```

Interpretation: Many short-lived function calls — likely serialization or string formatting in a hot loop.
Action: Batch operations, use f-strings instead of `.format()`, reduce logging in hot paths.

**Pattern: Asyncio Selector Everywhere**

```
  [select]████████████████████████████████████████████
  [_run_once]█████████████████████████████████████████
```

Interpretation: The event loop is mostly idle — waiting on I/O. CPU is not the bottleneck.
Action: Profile I/O latency instead (check DB query times, HTTP call latency, network round-trips).

**Pattern: GIL Contention (--gil flag)**

```bash
py-spy record -o gil-profile.svg --pid <PID> --gil
```

With `--gil`: shows only samples where GIL was held. Compare to without `--gil`:
- If `--gil` profile is similar to full profile → mostly CPU-bound Python
- If `--gil` profile is much smaller → significant time waiting for GIL (contention or C extension releasing GIL)
- Large gap between total and GIL-held samples in a supposedly CPU-bound app → another thread holds the GIL (numpy, C extension doing work)

---

## GIL Contention Detection

### Symptoms

- Multiple Python threads, but throughput does not scale with thread count
- `py-spy top` shows threads "waiting" rather than "running"
- CPU usage across all cores looks balanced but total CPU < 100% × thread_count

### Diagnosis

```bash
# Record with thread IDs to see per-thread time
sudo py-spy record -o profile.svg --pid <PID> --threads --duration 30

# Compare GIL-held vs total
sudo py-spy record -o gil.svg --pid <PID> --gil --duration 30
sudo py-spy record -o total.svg --pid <PID> --duration 30
# Open both SVGs and compare widths of same functions
```

### Common GIL Holders

| Library | GIL behaviour |
|---------|--------------|
| `json` (stdlib) | Holds GIL; use `orjson` (releases during C encoding) |
| `re` (stdlib) | Holds GIL for pure-Python regex; C path releases briefly |
| `numpy` | Releases GIL for most array operations |
| `pandas` | Mixed — groupby/apply often holds GIL |
| `cryptography` | Releases GIL for crypto operations |
| `asyncpg` | Releases GIL for I/O wait |
| `PIL/Pillow` | Releases GIL for image decode/encode |

### Solutions

```python
# 1. Use ProcessPoolExecutor for CPU-bound work
from concurrent.futures import ProcessPoolExecutor

async def cpu_intensive_handler(data):
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, process_data, data)
    return result

# 2. Use ThreadPoolExecutor for I/O-bound work that doesn't have async API
result = await loop.run_in_executor(None, blocking_io_call, args)

# 3. Use Cython/C extensions that release GIL
# e.g., orjson.dumps releases GIL; json.dumps does not
```

---

## asyncio Idle Time in Profiles

### Problem

py-spy records wall-clock time by default. In an asyncio app, a large portion of samples will show the event loop sleeping in `select()` / `epoll_wait()`. This inflates the apparent cost of I/O-related frames.

### Filtering Idle Time

```bash
# speedscope format — supports filtering and timeline view
py-spy record -o profile.speedscope --pid <PID> --format speedscope
# Open at speedscope.app — use "Left Heavy" view to see only CPU-active frames
```

### Interpreting asyncio Profiles

Relevant frames and what they mean:

| Frame | Meaning |
|-------|---------|
| `select` / `epoll_wait` in `_run_once` | Loop waiting for I/O — idle time |
| `asyncio/tasks.py __step` | Coroutine executing (real work) |
| `asyncio/futures.py __schedule_callbacks` | Future resolving — tiny overhead |
| `asyncio/streams.py` | Stream I/O (read/write buffering) |
| `ssl.py` | TLS handshake or record processing |

Rule of thumb: if `select`/`epoll_wait` > 70% of samples, your app is I/O-bound, not CPU-bound. Optimize query latency, connection pooling, or add caching rather than optimising Python code.

---

## memray Allocation Tree Interpretation

### Tree View Output

```
Total memory usage: 245.3 MB (peak)

╔══════════════════════════════════════════════════════╗
║ handle_request (app/server.py:42)   150.2 MB (61.2%) ║
╠══════════════════════════════════════════════════════╣
║   db.fetch (db/client.py:88)         98.4 MB (40.1%) ║
║     asyncpg.Record.__init__           98.1 MB (40.0%) ║  ← leak suspect
║   json.loads (parser.py:15)          34.5 MB (14.1%) ║
╚══════════════════════════════════════════════════════╝
```

Reading the tree:
- Percentage = share of peak total memory
- Deep allocation lines with high % = likely accumulation point
- `asyncpg.Record` objects accumulating → result sets not being freed (possibly stored in class attribute or module-level cache)

### Common Python Memory Patterns

**Pattern: List/dict accumulation**

```python
# BAD: cache grows unbounded
_cache = {}
def get_data(key):
    if key not in _cache:
        _cache[key] = fetch_from_db(key)
    return _cache[key]
```

memray shows: large allocation in `dict.__setitem__` from `get_data`, growing over time.

Fix: `functools.lru_cache(maxsize=1000)` or explicit eviction.

**Pattern: Circular references**

Python's reference counter cannot collect cycles involving `__del__`. Use `gc.get_objects()` to find:

```python
import gc
gc.collect()
# Objects with referrers beyond what's expected:
suspects = [obj for obj in gc.get_objects()
            if isinstance(obj, MyClass) and len(gc.get_referrers(obj)) > 2]
```

**Pattern: String interning / large string accumulation**

tracemalloc showing large `str` allocations:

```python
# Find who holds the string references
import sys
large_strings = [(sys.getsizeof(obj), obj[:50])
                 for obj in gc.get_objects()
                 if isinstance(obj, str) and sys.getsizeof(obj) > 1024]
large_strings.sort(reverse=True)
```

---

## tracemalloc: Taking Diffs in Production

### Adding a Diagnostic Endpoint (FastAPI example)

```python
import tracemalloc
from fastapi import FastAPI

app = FastAPI()
tracemalloc.start(25)
_baseline: tracemalloc.Snapshot | None = None

@app.post("/debug/memory/baseline")
async def take_baseline():
    global _baseline
    _baseline = tracemalloc.take_snapshot()
    return {"status": "baseline set"}

@app.get("/debug/memory/diff")
async def memory_diff(top: int = 20):
    if _baseline is None:
        return {"error": "No baseline — POST /debug/memory/baseline first"}
    current = tracemalloc.take_snapshot()
    stats = current.compare_to(_baseline, 'lineno')
    return {
        "top_growth": [
            {
                "file": str(s.traceback[0]),
                "size_kb": round(s.size / 1024, 2),
                "size_delta_kb": round(s.size_diff / 1024, 2),
                "count": s.count,
                "count_delta": s.count_diff,
            }
            for s in stats[:top]
        ]
    }
```

### Performance Overhead

| Setting | Overhead |
|---------|----------|
| `tracemalloc.start(1)` | ~5% memory, ~10% CPU |
| `tracemalloc.start(25)` | ~20% memory, ~15% CPU |
| `tracemalloc.start(50)` | ~35% memory, ~20% CPU |

Use `tracemalloc.start(1)` in production; increase frames for debugging sessions.

---

## C Extension Opacity Workarounds

py-spy with `--native` resolves C extension frames using debug symbols. Without symbols:

```bash
# Check if library has debug symbols
objdump --syms /usr/lib/python3/dist-packages/numpy/core/_multiarray_umath.cpython-311-x86_64-linux-gnu.so | head -20

# Install debug symbols (Debian/Ubuntu)
apt-get install python3-numpy-dbgsym

# Install debug symbols (from conda)
conda install -c conda-forge numpy=<version>=*_dbg
```

For wheels without debug info, use `py-spy record --format speedscope` and look at the frames just BELOW the opaque C frames to infer what Python code triggered the extension call.

# asyncio Debugging — Deep Reference

## Task Tree Reconstruction from Stack Traces

### Reading a py-spy / faulthandler Dump

A stack dump of an asyncio process shows frames for every live coroutine. Key identifiers:

```
Thread 0x7f4a... (idle):
  File "asyncio/base_events.py", line 1898, in _run_once
  File "asyncio/events.py", line 80, in _run
  File "app/server.py", line 42, in handle_request
    result = await db.fetch(query)         # ← suspended here
  File "asyncio/tasks.py", line 304, in __step
```

Reading the dump:
- `asyncio/base_events.py _run_once` — the event loop's own selector; this thread IS the loop.
- `asyncio/tasks.py __step` — a task is executing its next coroutine step.
- Your application frame after `__step` is the coroutine currently running.

### Reconstructing Awaiting Chains

Python 3.12+ added `Task.get_coro()` and coroutine `.cr_await` chaining:

```python
def awaiting_chain(task):
    """Walk the chain: task → coro → awaiting coro → ..."""
    coro = task.get_coro()
    chain = []
    while coro is not None:
        chain.append(coro)
        coro = getattr(coro, 'cr_await', None)
    return chain

# Usage
for task in asyncio.all_tasks():
    chain = awaiting_chain(task)
    print(f"{task.get_name()}: {' → '.join(str(c) for c in chain)}")
```

### Parent-Child Task Relationships

`asyncio` does NOT track task parent-child relationships natively (unlike Trio). To reconstruct:

```python
import contextvars

_current_task_id: contextvars.ContextVar[str] = contextvars.ContextVar('task_id', default='root')

def create_tracked_task(coro, name=None):
    parent_id = _current_task_id.get()
    async def wrapper():
        token = _current_task_id.set(name or id(coro))
        try:
            return await coro
        finally:
            _current_task_id.reset(token)
    task = asyncio.create_task(wrapper(), name=name)
    print(f"[TASK] {name} spawned by {parent_id}")
    return task
```

---

## shield() / cancel() Edge Cases

### The Orphaned-Task Problem with shield()

```python
# DANGEROUS PATTERN
async def dangerous():
    inner = asyncio.create_task(expensive_work())
    try:
        result = await asyncio.shield(inner)
    except asyncio.CancelledError:
        # outer task was cancelled. inner keeps running ORPHANED.
        raise  # re-raise to propagate cancellation

# SAFE PATTERN
async def safe():
    inner = asyncio.create_task(expensive_work())
    try:
        result = await asyncio.shield(inner)
    except asyncio.CancelledError:
        inner.cancel()          # explicitly cancel the inner task
        await asyncio.gather(inner, return_exceptions=True)  # wait for cleanup
        raise
```

### Cancellation Count (Python 3.11+)

```python
task.cancelling()
# Returns integer: number of cancel() calls that have not been unscheduled.
# Non-zero means the task is in "being cancelled" state.
# A task that catches CancelledError and does NOT re-raise should call
# task.uncancel() to decrement this counter.
```

Anti-pattern — suppressing cancellation without `uncancel()`:

```python
# BAD: leaks cancellation state
async def bad_cleanup():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass  # swallows cancel, but .cancelling() still returns 1

# GOOD: properly handled cleanup with uncancel
async def good_cleanup():
    task = asyncio.current_task()
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        if task.cancelling() > 0:
            task.uncancel()
        # do cleanup work here
        # do NOT re-raise → task continues
```

---

## uvloop vs Default Event Loop

| Aspect | Default (selector) | uvloop |
|--------|-------------------|--------|
| Underlying impl | Python `selectors` module | libuv (C, same as Node.js) |
| Throughput | ~50k req/s (typical FastAPI) | ~100k req/s |
| Installation | Built-in | `pip install uvloop` |
| Compatibility | All platforms | Linux + macOS (not Windows) |
| Debug mode | `PYTHONASYNCIODEBUG=1` works | Works |
| Subprocess support | Yes | Yes |
| SSL | Yes | Yes, faster |

```python
# Activate uvloop globally
import uvloop
uvloop.install()  # call before asyncio.run()

# Or per-run
asyncio.run(main(), loop_factory=uvloop.new_event_loop)  # Python 3.12+
```

Debugging difference: `uvloop` uses libuv's internal timer; debug callbacks like `slow_callback_duration` still work but C-level I/O frames are opaque in stack dumps.

---

## Python 3.11 vs 3.12 Behavioural Changes

### 3.11 Additions

| Feature | Description |
|---------|-------------|
| `asyncio.TaskGroup` | Structured concurrency; raises `ExceptionGroup` |
| `asyncio.timeout()` | Context manager timeout (replaces `wait_for` for most cases) |
| `asyncio.timeout_at(when)` | Absolute deadline version |
| `Task.cancelling()` | Returns cancel request count |
| `Task.uncancel()` | Decrements cancel count |
| `except*` syntax | Unwrap `ExceptionGroup` branches |

### 3.12 Changes and Known Issues

- `asyncio.Runner` class added (replaces manual loop setup in scripts).
- `asyncio.wait_for` bug: in edge cases involving nested cancellation (e.g., a `wait_for` inside a `TaskGroup`), a `CancelledError` can escape to the outer scope as a `TimeoutError`. Fixed in 3.13. Workaround: use `asyncio.timeout()` instead of `wait_for`.
- Task step tracing improved: `Task.__step_run_and_handle_result` separated for cleaner stack traces.
- `loop.run_in_executor` with `None` (default executor) respects the new `ThreadPoolExecutor` size heuristic (`min(32, os.cpu_count() + 4)`).

### 3.13 Changes

- `asyncio.wait_for` `CancelledError` leak fixed.
- `asyncio.Queue.shutdown()` added for clean producer termination.
- `TaskGroup` `__aexit__` cancellation behaviour clarified: external cancellation is now consistently represented as `BaseExceptionGroup` wrapping `CancelledError`.

---

## ExceptionGroup Internals

### Structure

```
ExceptionGroup("group message", [
    ValueError("bad value"),
    IOError("file not found"),
    ExceptionGroup("nested", [TypeError("type mismatch")])
])
```

- `.message` — string label
- `.exceptions` — list of contained exceptions (may include nested `ExceptionGroup`)
- `.subgroup(type)` — returns a new group containing only matching exceptions
- `.split(type)` — returns `(matching_group, rest_group)`

### Logging All Exceptions in a Group

```python
import traceback

def log_exception_group(eg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}ExceptionGroup: {eg.message}")
    for exc in eg.exceptions:
        if isinstance(exc, ExceptionGroup):
            log_exception_group(exc, indent + 1)
        else:
            tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            print(f"{prefix}  {tb_str}")
```

### except* Matching Rules

```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(raises_value_error())
        tg.create_task(raises_io_error())
except* ValueError as eg:
    # eg.exceptions contains only the ValueError(s)
    pass
except* IOError as eg:
    # eg.exceptions contains only the IOError(s)
    pass
# Any unmatched exception types propagate as a new ExceptionGroup
```

---

## Detecting Event Loop Blocking in Production

### Method 1: PYTHONASYNCIODEBUG

```bash
PYTHONASYNCIODEBUG=1 python -m uvicorn app:app
# Logs: "Executing <Task ...> took X.XXX seconds"
# Threshold: 0.1s (configurable via loop.slow_callback_duration)
```

### Method 2: Custom Watchdog Thread

```python
import asyncio, threading, time

class LoopWatchdog(threading.Thread):
    """Detects event loop blocking by polling from a separate thread."""
    def __init__(self, loop, threshold=0.5):
        super().__init__(daemon=True)
        self.loop = loop
        self.threshold = threshold
        self._last_ping = time.monotonic()

    def ping(self):
        self._last_ping = time.monotonic()

    def run(self):
        while True:
            time.sleep(self.threshold / 2)
            lag = time.monotonic() - self._last_ping
            if lag > self.threshold:
                print(f"WARNING: Event loop blocked for {lag:.2f}s")

async def watchdog_task(watchdog):
    while True:
        watchdog.ping()
        await asyncio.sleep(0.05)  # ping every 50ms
```

### Method 3: py-spy Native Stack Sampling

```bash
# Profile for 30s, output flame graph — shows blocking system calls
py-spy record -o profile.svg --pid <PID> --duration 30 --native

# Check for synchronous I/O calls (read, write, connect blocking without async)
# Look for: time.sleep, socket.connect, open(), requests.get in flame graph
```

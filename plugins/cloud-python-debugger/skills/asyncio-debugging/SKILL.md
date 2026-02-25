---
name: cloud-python-debugger:asyncio-debugging
description: "Quick reference for debugging Python asyncio programs — common exception patterns, task lifecycle states, cancellation semantics, event loop blocking detection, and structured concurrency (TaskGroup / ExceptionGroup) error propagation."
user-invocable: false
---

# asyncio Debugging — Quick Reference

For detailed internals, version-specific edge cases, and stack trace reconstruction, see [reference.md](reference.md).

## Task Lifecycle States

| State | `done()` | `cancelled()` | `exception()` |
|-------|----------|---------------|---------------|
| Pending | False | False | raises `InvalidStateError` |
| Running | False | False | raises `InvalidStateError` |
| Cancelled | True | True | raises `CancelledError` |
| Exception | True | False | returns exception |
| Result | True | False | returns None |

```python
task = asyncio.current_task()
all_tasks = asyncio.all_tasks()  # all non-done tasks in current loop
```

## Common Exception Patterns

| Exception | Root Cause | Diagnostic |
|-----------|-----------|------------|
| `CancelledError` in unexpected place | External cancel, timeout, TaskGroup child failure | Check `.cancelling()` count |
| `RuntimeError: Event loop is closed` | Loop used after shutdown or in thread | Check thread/loop ownership |
| `RuntimeError: no running event loop` | Calling coroutine from sync context | Use `asyncio.run()` or `loop.run_until_complete()` |
| `RuntimeError: Task attached to a different loop` | Task created on loop A, awaited on loop B | Never share tasks across loops |
| `TimeoutError` | `asyncio.wait_for()` exceeded deadline | Check if timeout wraps blocking I/O |
| `ExceptionGroup` | `TaskGroup` child(ren) raised | Use `except*` syntax to unwrap |

## Cancellation Semantics

```python
# Check if a task has been asked to cancel
task.cancelling()  # returns count of pending cancel() calls (Python 3.11+)

# Cancellation propagation rule:
# CancelledError re-raised inside except block → propagates upward
# CancelledError swallowed inside except block → suppressed (task continues)

# Shield from cancellation — outer cancel does NOT cancel inner:
result = await asyncio.shield(some_coroutine())
# WARNING: if outer task is cancelled while shield is pending, shield's
# inner task keeps running orphaned. You must track and cancel it manually.
```

## Event Loop Blocking Detection

```python
# Enable slow callback warning (logs callbacks taking > threshold seconds)
import asyncio
loop = asyncio.get_event_loop()
loop.slow_callback_duration = 0.1  # 100ms threshold

# Debug mode — enables ALL blocking detection + resource tracking
asyncio.run(main(), debug=True)
# OR
PYTHONASYNCIODEBUG=1 python app.py

# Find blocking calls in running app (py-spy)
# py-spy top --pid <PID>   ← look for threads stuck in non-async I/O
```

## TaskGroup / ExceptionGroup (Python 3.11+)

```python
# Basic TaskGroup pattern
async def run():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(child_a())
        t2 = tg.create_task(child_b())
    # Both tasks complete here; ExceptionGroup raised if any failed

# Catching individual exception types from a group
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(might_fail())
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"ValueError: {exc}")
except* IOError as eg:
    for exc in eg.exceptions:
        print(f"IOError: {exc}")
```

### ExceptionGroup Propagation Rules

- If ANY child task raises, ALL other children are cancelled.
- The `TaskGroup.__aexit__` waits for all cancellations to complete.
- Then raises `ExceptionGroup` wrapping every non-`CancelledError` exception.
- If the group itself is externally cancelled, raises `BaseExceptionGroup`.

## Quick Diagnostics

```python
# Dump all running tasks with their current stack
import asyncio, traceback

def dump_tasks():
    for task in asyncio.all_tasks():
        print(f"\n--- Task: {task.get_name()} ---")
        task.print_stack()

# In production, attach to SIGUSR1
import signal
signal.signal(signal.SIGUSR1, lambda *_: dump_tasks())
```

```bash
# From outside the process (py-spy)
py-spy dump --pid <PID>          # one-shot stack dump
py-spy top --pid <PID>           # live top-style view
```

## asyncio.timeout vs asyncio.wait_for (Python 3.11+)

```python
# Preferred: asyncio.timeout (Python 3.11+)
async with asyncio.timeout(5.0):
    await long_operation()
# Raises TimeoutError on expiry; CancelledError is NOT leaked to caller

# Legacy: asyncio.wait_for — can leak CancelledError in Python 3.12 edge cases
result = await asyncio.wait_for(long_operation(), timeout=5.0)
```

## Additional Resources

- [reference.md](reference.md) — Task tree reconstruction from stack traces, shield/cancel edge cases, uvloop vs default loop, Python 3.11/3.12 changelog, ExceptionGroup internals

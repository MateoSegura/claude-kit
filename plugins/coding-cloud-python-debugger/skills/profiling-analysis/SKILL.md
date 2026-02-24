---
name: coding-cloud-python-debugger:profiling-analysis
description: "Quick reference for profiling Python applications — py-spy invocation (attach to PID, flame graph, top mode), memray CLI (run, attach, flamegraph, tree), tracemalloc snapshots, and a triage decision matrix for CPU vs memory vs I/O problems."
user-invocable: false
---

# Profiling Analysis — Quick Reference

For flame graph interpretation, memray allocation trees, tracemalloc diffs, and GIL/asyncio pitfalls, see [reference.md](reference.md).

## Triage Decision Matrix

| Symptom | Likely Problem | Tool |
|---------|---------------|------|
| High CPU, low throughput | Hot loop, inefficient algorithm | py-spy record (flame graph) |
| CPU near 100% but Python slow | GIL contention, C extension holding GIL | py-spy --native |
| Memory grows over time | Leak: reference cycle, cache, unclosed resource | memray attach OR tracemalloc |
| Memory spike on requests | Allocating large objects per-request | memray run or live |
| Slow response, low CPU | Blocking I/O, DB wait, network latency | py-spy top (check for I/O frames) |
| asyncio event loop blocked | Sync call in async path | PYTHONASYNCIODEBUG=1 + py-spy |
| OOMKilled in K8s | Container memory limit breach | memray + container resource review |

---

## py-spy

### Attach to Running Process (Flame Graph)

```bash
# Record 60s flame graph, attach by PID (requires sudo or ptrace perms)
sudo py-spy record -o profile.svg --pid <PID> --duration 60

# With native extension frames (C/Cython/Rust)
sudo py-spy record -o profile.svg --pid <PID> --duration 60 --native

# Include subprocesses (e.g., Celery workers spawned from master)
sudo py-spy record -o profile.svg --pid <PID> --subprocesses

# Non-blocking (sampling doesn't pause the process)
sudo py-spy record -o profile.svg --pid <PID> --nonblocking
```

### Launch New Process

```bash
# No sudo needed when py-spy creates the process
py-spy record -o profile.svg -- python -m uvicorn app:app
```

### Top Mode (Live View)

```bash
sudo py-spy top --pid <PID>         # live, refreshes every second
sudo py-spy top --pid <PID> --rate 50   # 50 samples/s (default: 100)
```

### One-Shot Stack Dump

```bash
sudo py-spy dump --pid <PID>        # print current stack of all threads
sudo py-spy dump --pid <PID> --json # machine-readable
```

### Key CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-r, --rate` | 100 | Samples per second |
| `-d, --duration` | until Ctrl-C | Recording duration (seconds) |
| `--native` | off | Include C/Cython frames |
| `--nonblocking` | off | Don't pause process during sampling |
| `--subprocesses` | off | Profile child processes too |
| `--format` | flamegraph | Output format: `flamegraph`, `raw`, `speedscope` |
| `--gil` | off | Only sample when GIL is held (CPU-only view) |
| `--threads` | off | Show thread IDs in output |

---

## memray

### Run New Process

```bash
# Run script and write allocation binary to output.bin
python -m memray run -o output.bin my_script.py

# Run ASGI app (capture all allocations during startup + requests)
python -m memray run -o output.bin -m uvicorn app:app --host 0.0.0.0 --port 8000

# Include native (C extension) allocations
python -m memray run -o output.bin --native my_script.py
```

### Attach to Running Process

```bash
# Inject into PID (process continues running; allocation tracking begins)
python -m memray attach <PID>

# Detach when done
python -m memray detach <PID>
# Output: memray-attach-<PID>.bin in current directory
```

### Generate Reports

```bash
# HTML flame graph (peak memory usage)
python -m memray flamegraph output.bin
# → memray-flamegraph-output.html

# Terminal tree view
python -m memray tree output.bin

# Terminal summary (top allocating functions)
python -m memray summary output.bin

# HTML table (all allocation records)
python -m memray table output.bin

# Live TUI (during run — requires --live flag)
python -m memray run --live my_script.py
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--native` | Track C/C++ allocations too |
| `--live` | Real-time TUI (run only) |
| `--live-port N` | TUI on TCP port (for remote processes) |
| `--follow-fork` | Track child processes |
| `--trace-python-allocators` | Track Python small-object allocator |
| `-o, --output` | Output file path |

---

## tracemalloc (stdlib — No Extra Dependencies)

```python
import tracemalloc

# Start tracing — keep last N frames per allocation (deeper = more accurate)
tracemalloc.start(25)

# ... run your code ...

snapshot1 = tracemalloc.take_snapshot()

# ... run more code or wait for requests ...

snapshot2 = tracemalloc.take_snapshot()

# Compare: what grew between snapshot1 and snapshot2?
top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
# Output: <filename>:<lineno>: size=<bytes> (+<delta>) count=<N> (+<delta>)

# Save to disk (for offline analysis)
snapshot2.dump('/tmp/snap2.pickle')
# Reload:
snap = tracemalloc.Snapshot.load('/tmp/snap2.pickle')
```

### Environment / Command-Line Activation

```bash
# Start tracing from process startup with 25 frames
PYTHONTRACEMALLOC=25 python app.py
# OR
python -X tracemalloc=25 app.py
```

### Filter Snapshots to Your Code

```python
filters = [
    tracemalloc.Filter(True, "*/mypackage/*"),   # include only your code
    tracemalloc.Filter(False, "<frozen importlib*"),  # exclude stdlib
]
filtered = snapshot2.filter_traces(filters)
stats = filtered.statistics('traceback')
for stat in stats[:5]:
    print(f"{stat.size / 1024:.1f} KB — {stat.count} blocks")
    for line in stat.traceback.format():
        print("   ", line)
```

---

## Reading Output Quickly

### py-spy Flame Graph (SVG)

- X-axis = proportion of time (width = how often a frame appears in samples)
- Y-axis = call stack depth (top of flame = where time is actually spent)
- Wide frames near the top = hotspots to fix
- Flat top = CPU bound; tall narrow stacks = many short-lived calls

### memray Flame Graph (HTML)

- Top-down: allocation site at bottom, callers above
- Width = proportion of memory allocated through that frame
- Hover to see exact bytes and call count

### tracemalloc Diff

- Positive `+delta` = growth since last snapshot
- Large `count` with small `size` = many small objects (fragmentation risk)
- Large `size` with small `count` = large allocations (buffers, caches)

## Additional Resources

- [reference.md](reference.md) — Flame graph interpretation patterns, GIL contention detection, asyncio idle time in profiles, C extension opacity workarounds, Python-specific allocator behaviour

---
name: cloud-python-debugger:container-crash-analysis
description: Investigation methodology and reference for container and pod crash analysis in Docker and Kubernetes environments, covering exit codes, CrashLoopBackOff, OOMKilled, probe failures, and Python-specific container issues.
user-invocable: false
---

# Container Crash Analysis

Quick-reference for diagnosing container and pod crashes. See [reference.md](reference.md) for complete kubectl/docker command examples and deeper investigation patterns.

---

## Exit Code Classification

| Exit Code | Signal / Cause | Immediate Action |
|-----------|---------------|-----------------|
| `0` | Clean exit — process finished normally | Check why the container is not intended to exit (e.g., supervisor loop missing) |
| `1` | Application error — unhandled exception or `sys.exit(1)` | Read logs: `kubectl logs <pod> --previous` |
| `137` | OOMKilled — container hit memory limit (`128 + 9 = SIGKILL`) | Check `kubectl describe pod` for `OOMKilled` under `Last State`; check memory metrics |
| `139` | SIGSEGV — segmentation fault (C extension crash, e.g., numpy, grpcio) | Check for native dependency version mismatch; inspect coredump if available |
| `143` | SIGTERM — process received termination signal (graceful shutdown or eviction) | Check if uvicorn/gunicorn handled SIGTERM; check for node pressure or preemption |
| `2` | Shell error or misuse (e.g., bad `ENTRYPOINT` script syntax) | Inspect Dockerfile `ENTRYPOINT`/`CMD`; check the shell script for syntax errors |

---

## CrashLoopBackOff Diagnosis Flowchart

```
CrashLoopBackOff detected
       |
       v
1. kubectl logs <pod> --previous   ← Get the crash log FIRST
       |
       +-- Log shows Python traceback? → Classify error → route to relevant specialist
       |
       +-- Log is empty or "Killed"?   → Likely OOMKilled → check exit code 137 path
       |
       +-- Log shows "exec format error"? → Wrong container arch (arm64 vs amd64)
       |
       +-- Log shows missing .so or import error? → Missing system dep in slim image
       |
       v
2. kubectl describe pod <pod>      ← Check Last State exit code + reason
       |
       +-- Reason: OOMKilled        → See OOMKilled section below
       +-- Reason: Error (exit 1)   → App crash — check logs above
       +-- Reason: Completed (exit 0) → Missing restart supervisor or wrong command
       |
       v
3. Check liveness probe configuration
       |
       +-- Probe failing before app starts? → initialDelaySeconds too short
       +-- Probe endpoint not responding?   → App not binding on expected port/path
       |
       v
4. Check init containers (if any)
       kubectl logs <pod> -c <init-container-name>
```

---

## OOMKilled Detection

Three-step confirmation:

1. `kubectl describe pod <pod-name>` — look for `OOMKilled` in `Last State` under `Containers`
2. `kubectl top pod <pod-name> --containers` — compare current vs limit
3. Check node-level OOM: `kubectl describe node <node-name>` → look for `MemoryPressure`

Python-specific causes:
- **Unbounded in-memory caches** — `functools.lru_cache` with no `maxsize`, growing dicts
- **Large dataframe operations** — pandas/polars loading entire CSV into memory
- **Celery prefetch** — worker pulling too many tasks × payload size
- **Memory leak in C extensions** — numpy, grpcio, lxml reference cycle bugs

Resource limit tuning: Set `limits.memory` to 150% of observed peak. Set `requests.memory` to observed steady-state. See [reference.md](reference.md#resource-limit-tuning) for methodology.

---

## Liveness and Readiness Probe Failures

Common patterns:

| Symptom | Likely Cause | Fix Direction |
|---------|-------------|---------------|
| Pod restarts every N seconds, app logs show normal operation | `initialDelaySeconds` too short — probe fires before app is ready | Increase `initialDelaySeconds` or use a startup probe |
| Pod in `Running` but never `Ready`, no traffic routed | Readiness probe path returns non-200 or endpoint does not exist | Verify probe path exists and returns 200 on healthy app |
| Pod restarts under load | Liveness probe times out during high CPU (GIL contention) | Increase `timeoutSeconds`; consider `/healthz` endpoint that bypasses slow path |
| Init containers hang | External dependency (DB, secret, DNS) not yet available | Add retry logic or use `initContainers` with `restartPolicy: Always` |

Timing fields to tune: `initialDelaySeconds`, `periodSeconds`, `timeoutSeconds`, `failureThreshold`, `successThreshold`.

---

## Python-Specific Container Issues

### Signal Handling with Uvicorn

Uvicorn must receive SIGTERM to shut down gracefully. When running as PID 1 in a container, Linux does not deliver signals to PID 1 by default unless the process explicitly handles them. Use `tini` or `dumb-init` as the PID 1 supervisor:

```dockerfile
# Dockerfile
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Alternatively, use `CMD ["python", "-m", "uvicorn", ...]` — Python's signal handling is sufficient when Python is PID 1 and the event loop is running.

### PID 1 Zombie Reaping

Without a proper init process, child processes of Python (subprocess calls, multiprocessing workers) become zombies when they exit, consuming PID table slots. This eventually causes `fork` to fail (`EAGAIN: resource temporarily unavailable`). Use `tini` or `dumb-init`.

### /tmp Exhaustion

Python uses `/tmp` for tempfile, some logging handlers, and libraries like `matplotlib`. In K8s, the container's `/tmp` is the container filesystem overlay, which shares the node's `nodefs`. Heavy temp file usage can exhaust node disk space and trigger eviction. Mount `/tmp` as an `emptyDir` volume to use node scratch space with an explicit `sizeLimit`.

### Missing System Dependencies in Slim Images

`python:3.x-slim` strips many system libraries. Common missing deps:

| Library | Missing dep | Package to add |
|---------|-------------|----------------|
| `psycopg2` | `libpq` | `libpq5` |
| `grpcio` | `libstdc++` | `libstdc++6` |
| `lxml` | `libxml2`, `libxslt` | `libxml2 libxslt1.1` |
| `Pillow` | `libjpeg`, `zlib` | `libjpeg62-turbo zlib1g` |
| `cryptography` | `libssl` | `libssl3` |

---

## Image Pull Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ErrImagePull` / `ImagePullBackOff` | Registry unreachable or auth failure | Check `imagePullSecrets` in pod spec; verify registry credentials |
| `manifest unknown` | Tag does not exist in registry | Verify image tag was pushed; check spelling |
| `no space left on device` | Node disk exhausted from image layers | Run `kubectl describe node` → check `DiskPressure`; prune old images |
| `exec format error` | Architecture mismatch (amd64 vs arm64) | Rebuild image with `--platform linux/amd64` |

---

## Init Container Failure Chains

Init containers run sequentially. If init container N fails, containers N+1 through end never start. The pod shows `Init:CrashLoopBackOff` or `Init:Error`.

Diagnostic commands:
```bash
# List all init containers and their status
kubectl describe pod <pod> | grep -A 20 "Init Containers:"

# Get logs from a specific failing init container
kubectl logs <pod> -c <init-container-name>

# Get previous attempt logs
kubectl logs <pod> -c <init-container-name> --previous
```

Common init container failures: DB migration scripts failing, secret mounts not populated yet, DNS not yet resolving the dependency service.

---

## Additional Resources

- [reference.md](reference.md) — Complete kubectl and docker diagnostic command cheat sheet, ephemeral debug containers, multi-stage build debugging, service mesh sidecar issues, docker-compose vs K8s differences, uvicorn graceful shutdown patterns, and concrete examples for each crash type

# Container Crash Analysis — Deep Reference

## Exit Code Classification

| Exit Code | Signal | Common Cause |
|-----------|--------|-------------|
| 0 | — | Normal exit (unexpected if pod restarts) |
| 1 | — | Application error (unhandled exception, config error) |
| 2 | — | Misuse of shell command (bad entrypoint) |
| 137 | SIGKILL (9) | OOMKilled or `kubectl delete pod --force` |
| 143 | SIGTERM (15) | Graceful shutdown requested (preStop hook, scaling down) |
| 139 | SIGSEGV (11) | Segmentation fault (C extension crash, corrupted memory) |
| 134 | SIGABRT (6) | Abort signal (assertion failure in C code) |

## OOMKilled Diagnosis

### Detection
```bash
# Check if OOMKilled
kubectl describe pod <pod> -n <ns> | grep -A 5 "Last State"
# Look for: Reason: OOMKilled

# Check container memory at kill time
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'

# Check node-level OOM events
kubectl get events -n <ns> --field-selector reason=OOMKilling --sort-by='.lastTimestamp'
```

### Classification
1. **Spike**: Single request allocates excessive memory (large payload, unbounded query result)
2. **Leak**: Memory grows monotonically over time (unclosed clients, growing caches, circular refs)
3. **Baseline too high**: Container starts near its limit (too many pre-loaded models, large dependency tree)

### Investigation with memray
```bash
# Attach to running container (before it OOMs)
kubectl exec -it <pod> -n <ns> -- python -m memray attach <pid>

# Or run with memray from the start
kubectl exec -it <pod> -n <ns> -- python -m memray run --output /tmp/profile.bin app/main.py

# Generate flamegraph
python -m memray flamegraph /tmp/profile.bin -o /tmp/memray.html
```

## CrashLoopBackOff Diagnosis

### Phase 1: Classify the crash type
```bash
# Get restart count and exit code
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.containerStatuses[0].restartCount}'
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'

# Get logs from the PREVIOUS crash (not current)
kubectl logs <pod> -n <ns> --previous
```

### Phase 2: Common causes by exit code
- **Exit 1**: Check `--previous` logs for Python traceback. Common: missing env var, bad DB connection string, import error
- **Exit 137**: OOMKilled during startup. Check if memory limit is too low for import-heavy apps
- **Exit 143**: Liveness probe killing the container before it's ready. Check probe timing

### Phase 3: Probe-induced restarts
```bash
# Check probe configuration
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[0].livenessProbe}'
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[0].readinessProbe}'

# Common misconfigurations:
# - initialDelaySeconds too short (app not ready yet)
# - periodSeconds too aggressive
# - failureThreshold too low
# - Liveness probe on a path that depends on external services
```

## Pending Pod Troubleshooting

```bash
# Check why pod is Pending
kubectl describe pod <pod> -n <ns> | grep -A 10 "Events"

# Common reasons:
# - Insufficient CPU/memory (check resource requests vs node capacity)
kubectl describe nodes | grep -A 5 "Allocated resources"

# - PVC not bound
kubectl get pvc -n <ns>

# - Node selector or affinity not matching
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.nodeSelector}'

# - Image pull failures
kubectl get events -n <ns> --field-selector reason=Failed
```

## Ephemeral Debug Containers

```bash
# Attach a debug container to a running pod (K8s 1.23+)
kubectl debug -it <pod> -n <ns> --image=python:3.12-slim --target=<container>

# Debug a CrashLoopBackOff pod by copying it with a different entrypoint
kubectl debug <pod> -n <ns> --copy-to=debug-pod --container=<container> -- sleep infinity
kubectl exec -it debug-pod -n <ns> -- /bin/bash
```

## Docker-Compose vs K8s Differences

| Behavior | docker-compose | Kubernetes |
|----------|---------------|------------|
| Restart policy | `restart: unless-stopped` | `restartPolicy: Always` (default) |
| Health check | `healthcheck:` in compose | `livenessProbe:` / `readinessProbe:` |
| Log access | `docker logs` | `kubectl logs` (may lose logs on restart) |
| Resource limits | `deploy.resources.limits` | `resources.limits` in container spec |
| Signal handling | Direct SIGTERM | SIGTERM with `terminationGracePeriodSeconds` |
| DNS | Service name resolution | ClusterIP + CoreDNS |

## Python-Specific Container Issues

### Signal Handling with Uvicorn
```python
# uvicorn handles SIGTERM by default, but only if PID 1
# In Docker, use exec form in CMD:
# GOOD: CMD ["uvicorn", "app.main:app"]
# BAD:  CMD uvicorn app.main:app  (runs under /bin/sh, signals not forwarded)
```

### PID 1 Zombie Reaping
```dockerfile
# If using shell form or running multiple processes, use tini:
RUN apt-get install -y tini
ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### /tmp tmpfs Exhaustion
```yaml
# K8s mounts /tmp as emptyDir by default (memory-backed if medium: Memory)
# Python writes to /tmp for: multiprocessing, tempfile, some C extensions
# If your app writes large temp files, mount a volume:
volumes:
  - name: tmp-volume
    emptyDir:
      sizeLimit: 500Mi
```

### Graceful Shutdown Pattern
```python
import signal
import asyncio

async def shutdown(app):
    """Drain connections and clean up before exit."""
    # Close DB pools
    await app.state.db_pool.close()
    # Close HTTP clients
    await app.state.http_client.aclose()
    # Close Redis
    await app.state.redis.aclose()

# FastAPI lifespan pattern (preferred)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    app.state.db_pool = await create_pool()
    yield
    # Shutdown
    await app.state.db_pool.close()
```

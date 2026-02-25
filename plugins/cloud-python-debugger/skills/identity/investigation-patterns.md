# Investigation Patterns -- Step-by-Step Workflows

Concrete, step-by-step investigation workflows for the most common debugging scenarios. Each pattern follows the triage-first methodology and produces a structured finding.

---

## Pattern 1: Latency Spike Investigation

**Trigger**: P99 latency increases beyond baseline, or timeouts reported by clients.

### Steps

1. **Triage -- bound the problem (60 seconds max):**
   ```bash
   # Which pods are affected?
   kubectl top pods -n <ns> --sort-by=cpu
   # Is it one pod or all replicas?
   kubectl get pods -n <ns> -l app=<service> -o wide
   # When did it start?
   # Check deployment history:
   kubectl rollout history deployment/<service> -n <ns>
   ```

2. **Check if it is a single-service or cascading issue:**
   - Query Grafana for request duration by service: if only one service shows elevated latency, the problem is local. If multiple services spike at the same time, find the root -- the service whose latency spiked FIRST.

3. **Identify the slow phase within the service:**
   - Pull a trace for a slow request from Grafana Tempo/Jaeger.
   - Compare span durations: is the latency in application code, database, downstream HTTP/gRPC call, or queuing?

4. **Drill into the slow phase:**
   - **If DB**: Run the DB query debugging pattern (see debugging-methodology.md, section 4).
   - **If downstream call**: Check the downstream service. Is it healthy? Is the connection pool exhausted? Is the circuit breaker open?
   - **If application code**: Attach py-spy for a 30s profile:
     ```bash
     kubectl exec <pod> -n <ns> -- py-spy record --pid 1 --duration 30 --format speedscope -o /tmp/profile.json
     kubectl cp <ns>/<pod>:/tmp/profile.json ./profile.json
     ```
   - **If queuing (gap between spans)**: Check if the event loop is blocked. Run `py-spy dump --pid 1` to see what the main thread is doing.

5. **Produce finding** with the structured format from the identity SKILL.

---

## Pattern 2: OOMKilled Pod Investigation

**Trigger**: Pod terminated with reason `OOMKilled`, exit code 137.

### Steps

1. **Confirm OOMKill and get baseline:**
   ```bash
   kubectl describe pod <pod-name> -n <ns> | grep -A5 "Last State"
   kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].resources.limits.memory}'
   ```

2. **Classify: spike vs leak:**
   - Check memory time series in Grafana (`container_memory_rss`):
     - **Linear growth**: Memory leak. RSS increases steadily regardless of traffic.
     - **Spike on specific requests**: Payload-driven allocation. Identify the endpoint.
     - **Plateau then OOM**: Limit too low for steady-state. Measure true steady-state RSS.

3. **For memory leak (linear growth):**
   - Check if `tracemalloc` is available (env var `PYTHONTRACEMALLOC=1`).
   - If available, take two snapshots 5 minutes apart and compare:
     ```bash
     # Via a diagnostic endpoint or debugpy
     # Snapshot comparison shows which lines allocated the most new memory
     ```
   - If not available, use `memray attach`:
     ```bash
     kubectl exec <pod> -n <ns> -- memray attach <PID> -o /tmp/memray.bin -d 60
     kubectl cp <ns>/<pod>:/tmp/memray.bin ./memray.bin
     memray summary ./memray.bin
     memray flamegraph ./memray.bin -o mem-flame.html
     ```
   - Look for: unbounded caches, unclosed clients, accumulating lists in global scope, loggers with dynamic names.

4. **For payload-driven spike:**
   - Correlate OOM timestamp with access logs to identify the triggering request.
   - Check payload size -- is a client sending unexpectedly large data?
   - Check if the endpoint loads entire response into memory (e.g., `response.json()` on a 500MB response instead of streaming).

5. **For baseline too high:**
   - Profile steady-state RSS with realistic traffic.
   - Recommend adjusting `resources.limits.memory` to 1.5-2x steady-state RSS.

6. **Produce finding.**

---

## Pattern 3: CrashLoopBackOff Investigation

**Trigger**: Pod stuck in `CrashLoopBackOff`, unable to reach ready state.

### Steps

1. **Get crash context:**
   ```bash
   kubectl describe pod <pod-name> -n <ns>
   kubectl get events -n <ns> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'
   kubectl logs <pod-name> -n <ns> --previous --tail=200
   ```

2. **Classify by exit code:**
   - **Exit 1 + Python traceback**: Application startup error. Read the traceback.
   - **Exit 137 (SIGKILL)**: OOM during startup. Follow Pattern 2.
   - **Exit 143 (SIGTERM) + quick restart**: Liveness probe killing the pod before startup completes. Check probe timing.
   - **No logs at all**: Container cannot start. Check image pull status, entrypoint, and `command`/`args` in the pod spec.

3. **For application startup errors:**
   Common causes:
   - Missing environment variable (`KeyError` or Pydantic `ValidationError` in `Settings`)
   - Database connection failure (wrong `DATABASE_URL`, DB not ready, network policy blocking)
   - Port conflict (another process on the same port)
   - Missing dependency (import error from a package not in requirements)

   ```bash
   # Check if required config is present
   kubectl get configmap <name> -n <ns> -o yaml
   kubectl get secret <name> -n <ns> -o jsonpath='{.data}' | base64 -d
   # Test DB connectivity from the pod network
   kubectl run debug --rm -it --image=python:3.12-slim -n <ns> -- \
     python -c "import socket; socket.create_connection(('db-host', 5432), timeout=5); print('OK')"
   ```

4. **For probe-induced restarts:**
   ```bash
   kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].startupProbe}'
   kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].livenessProbe}'
   ```
   - If no `startupProbe` exists and `livenessProbe.initialDelaySeconds` is less than the application's startup time, the probe kills the pod before it is ready.
   - Recommended: add `startupProbe` with `failureThreshold * periodSeconds > max startup time`.

5. **Produce finding.**

---

## Pattern 4: gRPC Error Chain Investigation

**Trigger**: Elevated gRPC error rate (UNAVAILABLE, DEADLINE_EXCEEDED, INTERNAL) in a call chain.

### Steps

1. **Triage -- identify the failing hop:**
   ```bash
   # Check if the direct service is healthy
   kubectl get pods -n <ns> -l app=<service>
   kubectl logs -n <ns> -l app=<service> --tail=50
   ```

2. **Test each service in the chain independently:**
   ```bash
   # Port-forward to service B
   kubectl port-forward svc/<service-b> 50051:50051 -n <ns>
   # Call service B directly
   grpcurl -plaintext localhost:50051 list
   grpcurl -plaintext localhost:50051 <package>.<Service>/<Method> -d '<json>'
   ```
   Repeat for each service in the chain until you find the one that returns the error.

3. **For UNAVAILABLE:**
   - Check if the target pod is running and the gRPC server is listening.
   - Check Kubernetes Service selector matches pod labels.
   - Check if a NetworkPolicy is blocking traffic.
   - Check DNS resolution:
     ```bash
     kubectl exec <calling-pod> -n <ns> -- nslookup <target-service>.<ns>.svc.cluster.local
     ```

4. **For DEADLINE_EXCEEDED:**
   - Measure actual call latency with `grpcurl` and `time`:
     ```bash
     time grpcurl -plaintext -connect-timeout 5 localhost:50051 <package>.<Service>/<Method> -d '<json>'
     ```
   - Check if the deadline is being propagated (not reset) at each hop.
   - Check if an interceptor is adding unexpected latency.

5. **For INTERNAL:**
   - This means an unhandled exception on the server side. Check server logs for the traceback.
   - Common causes: `NoneType` attribute access, serialization error (field type mismatch in protobuf), uncaught DB exception.

6. **Produce finding.**

---

## Pattern 5: Connection Pool Exhaustion Investigation

**Trigger**: Timeouts or errors indicating no available connections (DB pool, HTTP client pool, gRPC channel limit).

### Steps

1. **Identify which pool is exhausted.** Check error messages:
   - `asyncpg.exceptions.TooManyConnectionsError` or SQLAlchemy pool timeout: DB pool
   - `httpx.PoolTimeout`: HTTP connection pool
   - gRPC: channel limit reached (less common; usually manifests as RESOURCE_EXHAUSTED)

2. **Check current pool state:**
   For SQLAlchemy:
   ```python
   # Via diagnostic endpoint
   pool = engine.pool
   print(f"size={pool.size()}, checkedout={pool.checkedout()}, overflow={pool.overflow()}, checkedin={pool.checkedin()}")
   ```
   For httpx:
   ```python
   # Check client limits
   print(f"limits={client._pool._max_connections}, active={len(client._pool._connections)}")
   ```

3. **Find the leak source.** Connections are "leaked" when they are checked out but never returned:
   - **DB**: Session not closed on exception. Check if the FastAPI dependency uses `try/finally` with `session.close()`.
   - **HTTP**: `httpx.AsyncClient` response body not consumed. `.read()` or `.json()` must be called, or use `async with client.stream()`.
   - **Long-running transactions**: A single request holding a DB session across multiple awaits prevents pool return.

4. **Check pool configuration:**
   ```python
   # SQLAlchemy
   engine = create_async_engine(url, pool_size=20, max_overflow=0, pool_timeout=10, pool_pre_ping=True)
   # pool_size + max_overflow = maximum concurrent connections
   ```
   Is the pool sized for the workload? If the service handles 100 concurrent requests and each holds a DB connection for the duration, `pool_size=20` is too small.

5. **Check the database side:**
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE datname = '<db>';
   SHOW max_connections;
   ```
   If `count(*)` is near `max_connections`, the DB itself is the bottleneck, not the pool.

6. **Produce finding.**

---

## Pattern 6: Structured Log Analysis for Error Correlation

**Trigger**: Elevated error rate in metrics, need to find the common factor across errors.

### Steps

1. **Pull recent error logs:**
   ```bash
   kubectl logs -n <ns> -l app=<service> --tail=500 | grep '"level":"error"'
   # Or for structlog JSON output:
   kubectl logs -n <ns> -l app=<service> --tail=500 | python -m json.tool --no-ensure-ascii | grep -B5 '"level": "error"'
   ```

2. **Extract common fields.** In structlog JSON logs, look for:
   - `event`: The log message (group errors by event type)
   - `request_id`: Correlate with traces
   - `user_id` or `tenant_id`: Is it affecting all users or a specific subset?
   - `endpoint`: Is it concentrated on one route?
   - `error_type` / `exc_info`: The exception class

3. **Group errors by pattern:**
   ```bash
   # Count errors by event type
   kubectl logs -n <ns> -l app=<service> --tail=5000 | \
     python3 -c "
   import sys, json
   from collections import Counter
   errors = Counter()
   for line in sys.stdin:
       try:
           log = json.loads(line)
           if log.get('level') == 'error':
               errors[log.get('event', 'unknown')] += 1
       except json.JSONDecodeError:
           pass
   for event, count in errors.most_common(10):
       print(f'{count:5d}  {event}')
   "
   ```

4. **Find the first occurrence.** The first error in a cascade is usually the root cause. Subsequent errors are often consequences (circuit breaker opens, connection pool empties, health check fails).

5. **Cross-reference with deployment timeline.** If the first error timestamp is within 5 minutes of a deployment, the deployment is the prime suspect. Check:
   ```bash
   kubectl rollout history deployment/<service> -n <ns>
   ```

6. **Produce finding.**

---

## Anti-Pattern: Investigation Without Triage

The following workflow is WRONG and must be avoided:

1. User reports "the service is slow"
2. Immediately attach py-spy and collect a CPU profile
3. Spend 20 minutes analyzing flame graph
4. Discover that CPU is fine and the bottleneck is a downstream DB query
5. Start over with DB investigation

The correct workflow:

1. User reports "the service is slow"
2. **Triage (60 seconds)**: Check `kubectl top pods` (CPU normal), pull one trace (DB span is 4 seconds, everything else is <50ms)
3. Proceed directly to DB query debugging pattern
4. Total investigation time: 10 minutes instead of 30

Triage is not optional. It is the first step of every investigation, every time.

# Debugging Methodology -- Scenario Reference

Detailed methodology for each of the six core debug scenarios. Each section defines what to look for, which tools to use, the diagnostic sequence, and common pitfalls.

---

## 1. Asyncio Exception Debugging

### When to use
- Unhandled exceptions in coroutines (`Task exception was never retrieved`)
- `asyncio.CancelledError` propagation issues
- `RuntimeError: Event loop is closed` or `RuntimeError: no running event loop`
- `asyncio.TimeoutError` cascades
- `RuntimeWarning: coroutine was never awaited`

### Diagnostic sequence

1. **Reproduce the exception path.** Check structlog output for the full traceback. Pay attention to the `Task` that raised -- `asyncio` traceback frames often point to `gather()` or `create_task()` rather than the actual failure site.

2. **Identify the exception origin vs propagation path.** The frame where the exception was RAISED is different from where it was OBSERVED. Trace backward from the log entry:
   - If `Task exception was never retrieved` -- find the `create_task()` call. The task's result was never awaited or its exception was never handled.
   - If `CancelledError` -- trace the cancellation source. Common causes: `asyncio.timeout()` context exit, `TaskGroup` cancellation on first failure, manual `task.cancel()`.

3. **Check for blocking calls in async context.** Search for sync I/O in async functions:
   - `requests.get/post` (should be `httpx`)
   - `time.sleep` (should be `asyncio.sleep`)
   - `open()` without `aiofiles`
   - `cursor.execute()` without async driver
   These block the event loop thread and manifest as intermittent timeouts in unrelated coroutines.

4. **Check structured concurrency patterns.** Python 3.11+ `TaskGroup` vs bare `create_task()`:
   - `TaskGroup` cancels sibling tasks on first exception -- is this the intended behavior?
   - Bare `create_task()` lets exceptions go unobserved until GC collects the Task object.

5. **Inspect event loop state.** If the service is running, use `debugpy` remote attach or `py-spy`:
   ```bash
   py-spy dump --pid <PID>
   ```
   This shows all Python threads and their current call stacks, revealing blocked coroutines.

### Common pitfalls
- **Swallowed exceptions in `gather(return_exceptions=True)`**: Results list contains exception objects that are never checked.
- **Signal handler races**: `asyncio.run()` installs signal handlers; if `uvicorn` also installs them, shutdown is non-deterministic.
- **`await` inside `except` block**: If the awaited coroutine raises, the original exception context is lost.

---

## 2. CPU and Memory Profiling

### When to use
- CPU utilization consistently above 80% on pods
- Memory growth over time (potential leak)
- OOMKilled events in Kubernetes
- Slow request handling with no obvious I/O bottleneck

### CPU profiling sequence

1. **Identify the hot process.** In K8s:
   ```bash
   kubectl top pods -n <namespace> --sort-by=cpu
   ```
   In docker-compose:
   ```bash
   docker stats --no-stream
   ```

2. **Attach py-spy for a sampling profile.** Does not stop the process:
   ```bash
   # From inside the container (kubectl exec or docker exec)
   py-spy record --pid <PID> --duration 30 --format flamegraph --output /tmp/profile.svg
   ```
   Or from outside (K8s requires `SYS_PTRACE` capability or `shareProcessNamespace: true`):
   ```bash
   kubectl exec -n <ns> <pod> -- py-spy record --pid 1 --duration 30 --format speedscope --output /tmp/profile.json
   ```

3. **Analyze the flame graph.** Look for:
   - Wide bars at the top = functions consuming the most CPU time
   - `_run_once` dominating = event loop overhead, possibly too many scheduled callbacks
   - `json.loads`/`json.dumps` = serialization bottleneck, consider `orjson`
   - `re.match`/`re.search` = regex compilation in a hot path (should be `re.compile` at module level)
   - `Pydantic` validation dominating = model validation on high-cardinality data

4. **Correlate with request patterns.** Check if CPU spike correlates with:
   - A specific endpoint (check access logs or OTEL span metrics)
   - A specific payload size
   - A specific time-of-day traffic pattern

### Memory profiling sequence

1. **Confirm memory growth.** Check if RSS is growing over time:
   ```bash
   kubectl top pods -n <ns> --sort-by=memory
   # Or check container metrics in Grafana: container_memory_rss
   ```

2. **Take tracemalloc snapshots.** If the service has tracemalloc enabled (`PYTHONTRACEMALLOC=1`):
   ```python
   # Via debugpy or a diagnostic endpoint
   import tracemalloc
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:20]:
       print(stat)
   ```

3. **Use memray for allocation tracking.** Attach to a running process:
   ```bash
   memray attach <PID> --output /tmp/memray.bin
   # After collection:
   memray flamegraph /tmp/memray.bin -o /tmp/mem-flamegraph.html
   memray summary /tmp/memray.bin
   ```

4. **Check for common Python memory leak patterns:**
   - **Unbounded caches**: `lru_cache` without `maxsize`, growing dicts used as caches without eviction
   - **Unclosed resources**: `httpx.AsyncClient` never `.aclose()`-d, DB sessions not returned to pool
   - **Circular references with `__del__`**: Prevent garbage collection
   - **Global lists/dicts accumulating per-request data**: Often in middleware or background tasks
   - **Logging handlers accumulating**: `logging.getLogger()` called with dynamic names creates unbounded loggers

5. **Compare two snapshots.** Take snapshot A, wait for memory to grow, take snapshot B:
   ```python
   stats = snapshot_b.compare_to(snapshot_a, 'lineno')
   for stat in stats[:10]:
       print(stat)
   ```
   Focus on allocations that grew between snapshots -- these are the leak candidates.

### Common pitfalls
- **Container memory limits vs Python heap**: `memory_limit` in K8s counts RSS, not just Python heap. Shared libraries, mmap'd files, and thread stacks all count.
- **`gc.collect()` does not mean no leak**: If objects are still reachable (referenced from a global), GC cannot free them.
- **py-spy in Alpine containers**: Alpine uses musl, which can interfere with py-spy. Use slim (glibc) images.

---

## 3. Distributed Trace Analysis

### When to use
- Latency spikes that span multiple services
- Requests timing out at the gateway but the backend service reports no errors
- Inconsistent behavior between service versions during canary rollout
- Need to understand the full call graph of a request

### Diagnostic sequence

1. **Obtain the trace ID.** From the client error response (if `X-Request-ID` or `traceparent` is echoed), from structured logs (search by request ID or user ID), or from Grafana/Jaeger search by service name + time range + latency threshold.

2. **Visualize the full trace.** In Jaeger/Grafana Tempo, load the trace by ID. Examine:
   - Total trace duration vs individual span durations
   - Which span is the bottleneck (longest duration relative to its children)
   - Gaps between spans (network latency, queuing, or missing instrumentation)
   - Error flags on spans (red spans indicate exceptions)

3. **Check span attributes and events.** Look for:
   - `http.status_code` on HTTP spans
   - `rpc.grpc.status_code` on gRPC spans
   - `db.statement` on database spans (reveals slow queries)
   - `exception.type` and `exception.message` on error spans
   - Custom span events added by the application

4. **Identify missing spans.** If the trace has a gap:
   - Check if the downstream service has OpenTelemetry instrumentation
   - Check if trace context propagation headers are being forwarded (`traceparent` for HTTP, metadata for gRPC)
   - Check if an intermediary (load balancer, service mesh sidecar) is stripping headers

5. **Cross-reference with metrics.** Compare the trace timeline with:
   - Pod CPU/memory at the same timestamps
   - Database connection pool utilization
   - Queue depth (Redis, RabbitMQ, Kafka consumer lag)

### Common pitfalls
- **Clock skew between services**: Spans from different hosts may have slightly misaligned timestamps. Jaeger/Tempo compensates, but manual correlation with logs requires awareness of this.
- **Sampling**: If the trace exporter uses probabilistic sampling, the specific failing request may not have been sampled. Switch to tail-based sampling or force-sample on error responses.
- **Async task spans**: `asyncio.create_task()` does not automatically propagate trace context. The application must explicitly set the parent span context on new tasks.

---

## 4. Database Query Debugging

### When to use
- Slow endpoint where latency is concentrated in the DB span
- Connection pool exhaustion (`asyncpg.exceptions.TooManyConnectionsError` or pool timeout)
- Deadlocks (`asyncpg.exceptions.DeadlockDetectedError`)
- N+1 query patterns visible in trace waterfalls

### Diagnostic sequence

1. **Identify the slow query.** From OTEL trace spans (`db.statement` attribute), from SQLAlchemy logging (`echo=True` or `SQLALCHEMY_ECHO=1`), or from PostgreSQL `pg_stat_statements`:
   ```sql
   SELECT query, calls, mean_exec_time, total_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 20;
   ```

2. **Run EXPLAIN ANALYZE on the slow query:**
   ```sql
   EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>;
   ```
   Look for:
   - **Seq Scan** on large tables (missing index)
   - **Nested Loop** with high row estimates (N+1 pattern)
   - **Sort** with high memory usage (missing index for ORDER BY)
   - **Hash Join** with large build table (consider materialized view or denormalization)

3. **Check connection pool state.** For SQLAlchemy async:
   ```python
   # Via diagnostic endpoint or debugpy
   pool = engine.pool
   print(f"Pool size: {pool.size()}")
   print(f"Checked out: {pool.checkedout()}")
   print(f"Overflow: {pool.overflow()}")
   print(f"Checked in: {pool.checkedin()}")
   ```
   If `checkedout == pool_size + max_overflow`, the pool is exhausted. Investigate: are sessions being held across await points? Is a long-running transaction blocking returns?

4. **Check for lock contention:**
   ```sql
   SELECT pid, usename, state, query, wait_event_type, wait_event
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY query_start;
   ```
   ```sql
   SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query,
          blocking.pid AS blocking_pid, blocking.query AS blocking_query
   FROM pg_stat_activity blocked
   JOIN pg_locks bl ON bl.pid = blocked.pid
   JOIN pg_locks kl ON kl.locktype = bl.locktype AND kl.database = bl.database
        AND kl.relation = bl.relation AND kl.pid != bl.pid
   JOIN pg_stat_activity blocking ON blocking.pid = kl.pid
   WHERE NOT bl.granted;
   ```

5. **Check for N+1 patterns.** In the trace waterfall, look for repeated identical DB spans within a single request. Count spans with `db.system = "postgresql"` -- if there are 50+ per request, it is likely an N+1. Check if `selectinload()` or `joinedload()` should replace lazy loading.

### Common pitfalls
- **`expire_on_commit=True` (SQLAlchemy default)**: After commit, accessing any attribute triggers a new SELECT. Set `expire_on_commit=False` in `async_sessionmaker`.
- **Implicit autoflush**: SQLAlchemy flushes before every query by default. A read query after a write within the same session triggers a flush, which can cause lock contention.
- **Connection leak on exception**: If the session dependency does not rollback+close in a `finally` block, exceptions leak connections from the pool.

---

## 5. gRPC Chain Debugging

### When to use
- `UNAVAILABLE` or `DEADLINE_EXCEEDED` errors in gRPC call chains
- Latency in multi-hop gRPC services (A calls B calls C)
- Metadata/header propagation failures
- Streaming RPC hangs or unexpected closures

### Diagnostic sequence

1. **Identify which hop is failing.** Use distributed traces to pinpoint the specific gRPC span where the error occurs. If traces are unavailable, use `grpcurl` to test each service independently:
   ```bash
   # Test service directly via port-forward
   kubectl port-forward svc/user-svc 50051:50051 -n <ns>
   grpcurl -plaintext localhost:50051 user.v1.UserService/GetUser \
     -d '{"user_id": "test-123"}'
   ```

2. **Check gRPC status codes.** Map the status code to its meaning:
   - `UNAVAILABLE` = service is down, DNS failure, or connection refused
   - `DEADLINE_EXCEEDED` = timeout (check deadline propagation -- does each hop subtract its own processing time from the remaining deadline?)
   - `RESOURCE_EXHAUSTED` = rate limiting or server-side resource limit
   - `INTERNAL` = unhandled server exception (check server logs for traceback)
   - `UNIMPLEMENTED` = wrong service version or missing method

3. **Check deadline propagation.** In gRPC chains, the deadline must be propagated from caller to callee. If service A sets a 10s deadline, and service B takes 3s before calling C, service C should receive a ~7s deadline. Check:
   - Is `timeout=` set on the client stub call?
   - Is the server passing the incoming context's deadline to its outgoing calls?
   - Does any hop reset the deadline instead of propagating it?

4. **Check interceptors.** gRPC interceptors (logging, auth, metrics) add latency. If total interceptor overhead per hop is 10ms and there are 5 hops, that is 50ms baseline. Check:
   - Are interceptors doing I/O (DB lookup for auth, HTTP call for token validation)?
   - Is the logging interceptor serializing large protobuf messages to string?

5. **Check connection management.** gRPC channels maintain persistent HTTP/2 connections:
   - Is the channel using keepalive (`grpc.keepalive_time_ms`)?
   - Is a load balancer terminating idle connections before the client's keepalive fires?
   - In K8s, is headless service used for client-side load balancing, or is a ClusterIP service forcing all traffic through a single connection?

6. **Test streaming RPCs separately.** For server-streaming or bidirectional RPCs:
   ```bash
   grpcurl -plaintext localhost:50051 user.v1.UserService/ListUsers \
     -d '{"page_size": 10}'
   ```
   Watch for: stream hangs (server not closing stream), flow control pressure (client not consuming fast enough), and metadata loss between stream messages.

### Common pitfalls
- **Channel reuse**: Creating a new `grpc.aio.insecure_channel()` per request is catastrophically expensive. Channels must be long-lived.
- **Missing `await context.abort()`**: In async gRPC servers, `context.abort()` must be awaited. Without `await`, the response is sent before the abort status is set.
- **Reflection not enabled**: `grpcurl` cannot discover services without `grpc_reflection` enabled on the server.

---

## 6. Container and Pod Crash Analysis

### When to use
- Pod in `CrashLoopBackOff` state
- `OOMKilled` termination reason
- Container exits with non-zero code
- Pod stuck in `Pending` or `ContainerCreating`
- Readiness/liveness probe failures causing restarts

### Diagnostic sequence

1. **Get pod status and events:**
   ```bash
   kubectl describe pod <pod-name> -n <ns>
   kubectl get events -n <ns> --sort-by='.lastTimestamp' --field-selector involvedObject.name=<pod-name>
   ```
   Key fields: `Last State` (exit code, reason, signal), `Restart Count`, `Conditions`, `Events`.

2. **Classify the crash reason:**
   - **Exit code 137 (SIGKILL)**: OOMKilled or external kill. Check `Last State.reason`. If `OOMKilled`, the container exceeded its memory limit.
   - **Exit code 1**: Application error. Check logs for traceback.
   - **Exit code 143 (SIGTERM)**: Graceful shutdown requested but handler may have failed.
   - **Reason: `CrashLoopBackOff`**: Container keeps crashing. The backoff delay increases exponentially. Check previous container logs.

3. **Retrieve logs from the crashed container:**
   ```bash
   # Current container logs
   kubectl logs <pod-name> -n <ns> --tail=200
   # Previous (crashed) container logs
   kubectl logs <pod-name> -n <ns> --previous --tail=200
   ```

4. **For OOMKilled:**
   - Compare container memory limit (`resources.limits.memory`) with actual usage at crash time (`kubectl top pod` or Grafana `container_memory_rss`).
   - Check if the limit is simply too low for the workload, or if there is a memory leak (see CPU/Memory Profiling above).
   - Check `dmesg` on the node for kernel OOM killer logs:
     ```bash
     kubectl exec -it <pod-name> -n <ns> -- dmesg | grep -i oom
     ```
   - If RSS is growing linearly over time, it is a leak. If it spikes on specific requests, it is a payload size issue.

5. **For probe failures:**
   ```bash
   # Check probe configuration
   kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].livenessProbe}'
   kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].readinessProbe}'
   ```
   - Is `initialDelaySeconds` sufficient for the application startup time?
   - Is the probe endpoint (`/health/live`, `/health/ready`) actually responding?
   - Test the probe endpoint directly:
     ```bash
     kubectl exec <pod-name> -n <ns> -- curl -s http://localhost:8000/health/live
     ```
   - Check if the probe is timing out (default 1s may be too short for a startup probe).

6. **For Pending pods:**
   ```bash
   kubectl describe pod <pod-name> -n <ns>
   ```
   Check events for: `FailedScheduling` (insufficient resources on nodes), `ImagePullBackOff` (wrong image tag or registry auth failure), `FailedMount` (volume/secret not found).

7. **For docker-compose crashes (local environment):**
   ```bash
   docker logs <container-name> --tail 200
   docker inspect <container-name> --format '{{.State}}'
   docker stats --no-stream
   ```

### Common pitfalls
- **Memory limit too close to baseline RSS**: Python's garbage collector needs headroom. If baseline RSS is 400MB, a 512MB limit leaves only 112MB for request processing and GC overhead. Set limits to at least 1.5x steady-state RSS.
- **Startup probe missing**: Without a startup probe, the liveness probe fires during startup and restarts the pod before it finishes initializing. Use `startupProbe` with generous `failureThreshold`.
- **Signal handling in Python**: `uvicorn` handles SIGTERM, but if the application registers its own signal handlers incorrectly, graceful shutdown fails and the container is SIGKILL-ed after `terminationGracePeriodSeconds`.

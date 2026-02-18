---
name: design-patterns
description: Zephyr firmware architecture patterns and anti-patterns — subsystem decomposition, initialization orchestration, state machines, memory management, error handling, communication patterns, and common architectural anti-patterns to avoid
user-invocable: false
---

# Zephyr Firmware Design Patterns

Higher-level architectural patterns for structuring Zephyr-based firmware systems. These build on kernel-level concurrency primitives to create maintainable, testable, and portable embedded applications.

For thread-level concurrency patterns (producer-consumer, ISR-safe signaling, work queues), see [zephyr-kernel/concurrency-patterns.md](../zephyr-kernel/concurrency-patterns.md).

## Architecture Principles

**Microservices thinking:** Decompose firmware into loosely coupled subsystems communicating via queues/events, not shared state.

**Subsystem characteristics:**
- Single responsibility, public API via header, private implementation
- Owns OS primitives (threads, queues, heaps), runtime initialization
- Testable in isolation

**Layered architecture:** Application → Subsystem → Driver → HAL → Hardware (devicetree)

**Dependency rules:**
- Upper layers depend on lower, never reverse
- Never skip layers (no app code directly accessing HAL)
- Drivers cannot call app callbacks (use events/queues)

**Module boundaries:**
- Public header with Doxygen API, all state `static` (file-scoped)
- Only header functions non-static
- OS primitives owned by module, initialized in init function

**Portability mandate:** Switching SoCs requires changing ONLY overlays/Kconfig, never `src/` code. Use `DEVICE_DT_GET(DT_NODELABEL(...))`, read hardware from devicetree, abstract board differences behind subsystem APIs.

## Initialization Patterns

**SYS_INIT levels:** `PRE_KERNEL_1/2`, `POST_KERNEL`, `APPLICATION`. Lower priority = earlier execution within level.

```c
static int sensor_subsystem_init(void) { return sensor_manager_init(); }
SYS_INIT(sensor_subsystem_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
```

**Runtime init function pattern:** Every subsystem provides init function creating all OS primitives:

```c
static K_THREAD_STACK_DEFINE(sensor_stack, 2048);
static struct k_thread sensor_thread;
static struct k_msgq sensor_queue;

int sensor_manager_init(void)
{
    k_msgq_init(&sensor_queue, buffer, sizeof(msg), 10);
    k_tid_t tid = k_thread_create(&sensor_thread, sensor_stack, ...);
    if (!tid) { return -ENOMEM; }
    return 0;
}
```

**Init dependency resolution:**
- Use SYS_INIT priority ordering for subsystem dependencies
- Use `device_is_ready()` for device dependencies, fail-fast if critical

**Init error propagation:**
- Critical subsystems: fail-fast, return error, abort
- Non-critical: log warning, graceful degradation

## State Machine Patterns

**Event-driven state machine:** Message queue delivers events, state handlers process them:

```c
enum state { IDLE, CONNECTING, CONNECTED };
enum event { CONNECT_REQ, CONNECTED, DISCONNECT };

struct sm {
    enum state current_state;
    struct k_msgq event_queue;
};

void sm_run(void) {
    enum event event;
    while (1) {
        k_msgq_get(&sm.event_queue, &event, K_FOREVER);
        switch (sm.current_state) {
        case IDLE:
            if (event == CONNECT_REQ) { sm.current_state = CONNECTING; }
            break;
        /* ... */
        }
    }
}
```

Events drive transitions (not polling), state is explicit and logged, single thread processes state machine.

For hierarchical states, transition tables, guard conditions, see [patterns-reference.md](patterns-reference.md).

## Memory Management Patterns

**Static buffer pool:** Fixed-size, bounded-count buffers use `K_MEM_SLAB`:

```c
K_MEM_SLAB_DEFINE(buffer_pool, 128, 8, 4);
void *buf;
k_mem_slab_alloc(&buffer_pool, &buf, K_MSEC(100));
/* use */
k_mem_slab_free(&buffer_pool, buf);
```

Constant-time alloc/free, no fragmentation, bounded pool size.

**Private heap:** Variable-size allocations within module:

```c
K_HEAP_DEFINE(data_heap, 4096);
void *ptr = k_heap_alloc(&data_heap, size, K_MSEC(100));
/* use */
k_heap_free(&data_heap, ptr);
```

Per-module accounting, bounded heap size. Never use system heap (`k_malloc`/`k_free`).

**Zero-copy buffer passing:** Pass buffer ownership via message queue:

```c
/* Producer allocates, consumer frees */
k_mem_slab_alloc(&pool, &buf, K_FOREVER);
fill_data(buf);
k_msgq_put(&queue, &buf, K_FOREVER);  /* Pass pointer */

/* Consumer */
k_msgq_get(&queue, &buf, K_FOREVER);
process(buf);
k_mem_slab_free(&pool, buf);  /* Consumer owns buffer, must free */
```

**Memory budget per module:** Define via Kconfig:

```kconfig
config APP_SENSOR_HEAP_SIZE
    int "Sensor heap size (bytes)"
    default 4096
```

Use: `K_HEAP_DEFINE(sensor_heap, CONFIG_APP_SENSOR_HEAP_SIZE);`

**Stack sizing:** Enable `CONFIG_THREAD_ANALYZER=y`, measure with `k_thread_stack_space_get()`, add 25% margin.

## Error Handling Patterns

**errno propagation chain:** Every fallible function returns negative errno, caller checks:

```c
int sensor_read(struct reading *out) {
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));
    if (!device_is_ready(dev)) {
        LOG_ERR("Sensor not ready");
        return -ENODEV;
    }
    int ret = sensor_sample_fetch(dev);
    if (ret < 0) {
        LOG_ERR("Fetch failed: %d", ret);
        return ret;  /* Propagate */
    }
    return 0;
}

/* Caller checks */
int ret = sensor_read(&sample);
if (ret < 0) { /* handle error */ }
```

Never silently ignore errors. Log and decide: propagate, recover, or degrade.

**Error recovery strategies:**

- **Retry with backoff:** I2C NAK, SPI timeout — retry with exponential backoff, max retry count
- **Graceful degradation:** Non-critical subsystem fails — continue with reduced functionality
- **Watchdog reset:** Critical subsystem fails — trigger watchdog reset (last resort)

**Health monitoring:** Low-priority thread checks queue depths, heap usage, stack margins. Logs warnings before failures occur.

```c
void health_monitor(void) {
    while (1) {
        if (k_msgq_num_used_get(&queue) > threshold) { LOG_WRN("Queue high"); }
        size_t unused;
        k_thread_stack_space_get(&thread, &unused);
        if (unused < 256) { LOG_ERR("Stack critical"); }
        k_sleep(K_SECONDS(10));
    }
}
```

## Communication Patterns

**Publish-subscribe (k_event):** One producer, many consumers:

```c
static struct k_event system_events;

void producer(void) { k_event_post(&system_events, EVENT_SENSOR_DATA); }

void consumer1(void) {
    while (1) {
        k_event_wait(&system_events, EVENT_SENSOR_DATA, false, K_FOREVER);
        update_display();
    }
}

void consumer2(void) {
    while (1) {
        k_event_wait(&system_events, EVENT_SENSOR_DATA, false, K_FOREVER);
        log_data();
    }
}
```

All subscribers wake when event raised. No direct coupling.

**Request-response over queues:** Synchronous request-response:

```c
struct request {
    enum type type;
    void *data;
    struct k_sem response_sem;
    int result;
};

int send_request(enum type type, void *data) {
    struct request req = { .type = type, .data = data };
    k_sem_init(&req.response_sem, 0, 1);
    k_msgq_put(&request_queue, &req, K_FOREVER);
    k_sem_take(&req.response_sem, K_FOREVER);  /* Wait for response */
    return req.result;
}

void worker(void) {
    struct request req;
    while (1) {
        k_msgq_get(&request_queue, &req, K_FOREVER);
        req.result = handle_request(req.type, req.data);
        k_sem_give(&req.response_sem);  /* Signal completion */
    }
}
```

**Observer pattern for sensor distribution:**

```c
typedef void (*sensor_callback_t)(const struct reading *r);
static sensor_callback_t observers[MAX_OBSERVERS];
static int num_observers = 0;

void sensor_register_observer(sensor_callback_t cb) {
    observers[num_observers++] = cb;
}

void sensor_notify(const struct reading *r) {
    for (int i = 0; i < num_observers; i++) {
        observers[i](r);
    }
}
```

## Common Anti-Patterns to Avoid

**Architectural:**
- God Module: all logic in one file → decompose into subsystems
- Circular Dependencies: A calls B, B calls A → use event-based decoupling
- Leaky Abstraction: app directly accesses registers → use HAL APIs
- Monolithic Init: single init function, no error handling → per-subsystem init with error propagation

**Concurrency:**
- Global Shared State: threads share variables without sync → use message queues
- Priority Inversion: high-priority blocked by low-priority → use mutex (priority inheritance)
- Blocking in ISR: `k_sleep()`, I2C in ISR → defer to thread via semaphore/work queue
- Busy-Wait Polling: while (!flag) → block on semaphore/k_poll

**Memory:**
- System Heap Abuse: `k_malloc()`/`k_free()` → private `k_heap` per module
- Unbounded Allocation: allocate in loop, no limit → use `K_MEM_SLAB` (bounded pool)
- Stack Overflow: guessed stack size → measure with `CONFIG_THREAD_ANALYZER`, add 25% margin
- VLA Usage: variable-length arrays → fixed-size arrays or heap allocation

**Error Handling:**
- Silent Failure: ignore return values → check every return, log and propagate
- Assert in Production: `__ASSERT()` on hardware failure → return `-errno`, log error
- Panic on Recoverable Error: `sys_reboot()` on BLE send failure → retry with backoff
- Missing `device_is_ready()`: use device without check → always check after `DEVICE_DT_GET()`

**Configuration:**
- ifdef Spaghetti: `#ifdef CONFIG_*` → use `IS_ENABLED(CONFIG_*)`
- Hardcoded Hardware: pin numbers in C code → use devicetree (`DEVICE_DT_GET`, `DT_NODELABEL`)
- Missing Kconfig Dependencies: code assumes symbols enabled → explicitly list in `prj.conf`
- Late MCUboot Integration: add bootloader later → use `--sysbuild` from day one

For complete pattern implementations with full code examples, see [patterns-reference.md](patterns-reference.md).

For detailed anti-pattern catalog with BAD/GOOD code pairs, see [anti-patterns.md](anti-patterns.md).

## Additional Resources

- [patterns-reference.md](patterns-reference.md) — Complete pattern implementations (subsystem module, hierarchical state machine, event-driven architecture, zero-copy pipeline, health monitor, retry with backoff)
- [anti-patterns.md](anti-patterns.md) — Catalog of common anti-patterns with BAD/GOOD code pairs
- [zephyr-kernel/concurrency-patterns.md](../zephyr-kernel/concurrency-patterns.md) — Thread-level concurrency patterns (producer-consumer, ISR-safe signaling, work queues, k_poll, zero-copy buffer passing, mutex with priority inheritance, cooperative yielding, condition variables)

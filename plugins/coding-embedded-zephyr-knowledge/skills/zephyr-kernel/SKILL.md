---
name: zephyr-kernel
description: Zephyr RTOS kernel primitives — threads, scheduling, synchronization, timers, memory management, device driver model, logging, and power management
user-invocable: false
---

# Zephyr Kernel Quick Reference

## Runtime vs. Compile-Time Initialization

**CRITICAL**: Prefer runtime initialization functions over compile-time macros for flexibility and dynamic system configuration.

| Primitive | Runtime (preferred) | Compile-time (static) |
|-----------|---------------------|----------------------|
| Thread | `k_thread_create()` | `K_THREAD_DEFINE()` |
| Semaphore | `k_sem_init()` | `K_SEM_DEFINE()` |
| Mutex | `k_mutex_init()` | `K_MUTEX_DEFINE()` |
| Message queue | `k_msgq_init()` | `K_MSGQ_DEFINE()` |
| Timer | `k_timer_init()` | `K_TIMER_DEFINE()` |
| Work queue | `k_work_init()` | (no compile-time equivalent) |

Runtime initialization allows dynamic configuration, easier testing, and better integration with device lifecycle management.

## Thread Creation (Runtime)

```c
K_THREAD_STACK_DEFINE(my_stack, 1024);
struct k_thread my_thread;

k_tid_t tid = k_thread_create(
    &my_thread,                  /* Thread control block */
    my_stack,                    /* Stack buffer */
    K_THREAD_STACK_SIZEOF(my_stack),
    entry_fn,                    /* Entry point */
    NULL, NULL, NULL,            /* Up to 3 arguments */
    K_PRIO_PREEMPT(7),          /* Priority */
    0,                          /* Options (0, K_ESSENTIAL, K_USER) */
    K_NO_WAIT                   /* Start delay */
);
```

**Priority ranges:**
- Meta-IRQ: `-CONFIG_NUM_METAIRQ_PRIORITIES` to -1 (highest, uninterruptible)
- Cooperative: 0 to `CONFIG_NUM_COOP_PRIORITIES - 1` (non-preemptible)
- Preemptible: `CONFIG_NUM_COOP_PRIORITIES` to `CONFIG_NUM_PREEMPT_PRIORITIES - 1` (lowest)

**Helper macros:** `K_PRIO_COOP(x)`, `K_PRIO_PREEMPT(x)`

## Synchronization Primitives (Runtime)

### Semaphore

```c
struct k_sem my_sem;
k_sem_init(&my_sem, 0, 10);  /* initial=0, limit=10 */

k_sem_give(&my_sem);
int ret = k_sem_take(&my_sem, K_MSEC(100));  /* 0=success, -EAGAIN=timeout */
```

**ISR-safe:** `k_sem_give()` can be called from ISR context.

### Mutex

```c
struct k_mutex my_mutex;
k_mutex_init(&my_mutex);

k_mutex_lock(&my_mutex, K_FOREVER);
/* critical section */
k_mutex_unlock(&my_mutex);
```

**Priority inheritance:** Automatic to prevent priority inversion.

### Message Queue

```c
char __aligned(4) msgq_buffer[10 * sizeof(struct my_msg)];
struct k_msgq my_msgq;

k_msgq_init(&my_msgq, msgq_buffer, sizeof(struct my_msg), 10);

k_msgq_put(&my_msgq, &msg, K_NO_WAIT);
k_msgq_get(&my_msgq, &msg, K_FOREVER);
```

## Timers and Work Queues

### Timer (one-shot or periodic)

```c
struct k_timer my_timer;

void timer_expired(struct k_timer *timer) {
    /* Called in ISR context */
}

k_timer_init(&my_timer, timer_expired, NULL);
k_timer_start(&my_timer, K_MSEC(100), K_MSEC(100));  /* delay, period */
k_timer_stop(&my_timer);
```

### Work Queue (defer processing to thread context)

```c
struct k_work my_work;

void work_handler(struct k_work *work) {
    /* Called in work queue thread context */
}

k_work_init(&my_work, work_handler);
k_work_submit(&my_work);  /* Submit to system work queue */
```

### Delayable Work

```c
struct k_work_delayable my_delayed_work;

k_work_init_delayable(&my_delayed_work, work_handler);
k_work_schedule(&my_delayed_work, K_MSEC(500));
```

## Memory Management

### Private Heap

```c
K_HEAP_DEFINE(my_heap, 2048);

void *ptr = k_heap_alloc(&my_heap, 128, K_NO_WAIT);
k_heap_free(&my_heap, ptr);
```

### Memory Slab (fixed-size blocks)

```c
K_MEM_SLAB_DEFINE(my_slab, 64, 10, 4);  /* block_size, num_blocks, align */

void *block;
k_mem_slab_alloc(&my_slab, &block, K_NO_WAIT);
k_mem_slab_free(&my_slab, block);
```

## Device Driver Model

### Obtaining Device References (Zephyr 3.x+)

```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(my_sensor));

if (!device_is_ready(dev)) {
    LOG_ERR("Device not ready");
    return -ENODEV;
}
```

**Deprecated:** `device_get_binding()` — removed in Zephyr 3.x. Always use `DEVICE_DT_GET()`.

### Sensor API

```c
sensor_sample_fetch(dev);
sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val);
```

### GPIO API

```c
const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);

gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
gpio_pin_set_dt(&led, 1);
gpio_pin_get_dt(&button);

gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_RISING);
```

## Logging

```c
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(my_module, LOG_LEVEL_INF);

LOG_INF("Sensor value: %d", value);
LOG_WRN("Low battery: %d mV", voltage);
LOG_ERR("Device init failed: %d", ret);
LOG_DBG("Debug info: %p", ptr);
```

**Log levels:** `LOG_LEVEL_NONE`, `LOG_LEVEL_ERR`, `LOG_LEVEL_WRN`, `LOG_LEVEL_INF`, `LOG_LEVEL_DBG`

**Module-specific control:** Set via Kconfig or runtime with `log_filter_set()`.

## Power Management

### Device Power Management

```c
#include <zephyr/pm/device.h>

pm_device_action_run(dev, PM_DEVICE_ACTION_SUSPEND);
pm_device_action_run(dev, PM_DEVICE_ACTION_RESUME);
```

### System Power Management

```c
#include <zephyr/pm/pm.h>

/* Requires CONFIG_PM=y */
/* System will automatically enter low-power states when idle */
```

**States:** `PM_STATE_ACTIVE`, `PM_STATE_RUNTIME_IDLE`, `PM_STATE_SUSPEND_TO_IDLE`, `PM_STATE_STANDBY`, `PM_STATE_SUSPEND_TO_RAM`, `PM_STATE_SOFT_OFF`

## Common Error Codes

| Code | Value | Meaning | Common cause |
|------|-------|---------|--------------|
| `0` | 0 | Success | Operation completed |
| `-EAGAIN` | -11 | Try again | Timeout on non-blocking call |
| `-EBUSY` | -16 | Device busy | Resource in use |
| `-EINVAL` | -22 | Invalid argument | Bad parameter value |
| `-ENODEV` | -19 | No such device | Device not found or not ready |
| `-ENOSYS` | -88 | Not implemented | Operation not supported |
| `-ENOMEM` | -12 | Out of memory | Allocation failed |

## Additional resources

- For complete API signatures with all parameters, return types, and detailed behavior, see [kernel-api-reference.md](kernel-api-reference.md)
- For idiomatic concurrency patterns and worked examples, see [concurrency-patterns.md](concurrency-patterns.md)

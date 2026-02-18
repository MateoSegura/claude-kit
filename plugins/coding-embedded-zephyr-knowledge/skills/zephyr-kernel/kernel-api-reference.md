# Zephyr Kernel API — Complete Reference

## Thread API

### k_thread_create

```c
k_tid_t k_thread_create(
    struct k_thread *new_thread,    /* Thread control block */
    k_thread_stack_t *stack,        /* Stack buffer */
    size_t stack_size,              /* Stack size in bytes */
    k_thread_entry_t entry,         /* Entry point function */
    void *p1, void *p2, void *p3,  /* Entry point args (can be NULL) */
    int prio,                       /* Thread priority */
    uint32_t options,               /* Thread options */
    k_timeout_t delay               /* Start delay */
);
```

**Returns:** Thread ID (`k_tid_t`) — always succeeds.

**Options flags:**
- `0` — Normal thread
- `K_ESSENTIAL` — Thread abort causes system fatal error
- `K_USER` — User-mode thread (requires CONFIG_USERSPACE=y and MPU)
- `K_INHERIT_PERMS` — Inherit parent thread permissions (user mode)

**Entry point signature:**
```c
void entry_fn(void *p1, void *p2, void *p3);
```

### k_thread_start

```c
void k_thread_start(k_tid_t thread);
```

Starts a thread that was created with a non-zero delay. No effect if thread already started.

### k_thread_join

```c
int k_thread_join(struct k_thread *thread, k_timeout_t timeout);
```

**Returns:**
- `0` — Thread exited successfully
- `-EAGAIN` — Timeout occurred
- `-EDEADLK` — Thread attempted to join itself
- `-EINVAL` — Thread is not joinable (essential thread)

**Note:** Thread must have exited via `return` or `k_thread_abort()`.

### k_thread_abort

```c
void k_thread_abort(k_tid_t thread);
```

Immediately terminates thread. Cannot abort essential threads without triggering fatal error. Thread cannot be restarted.

### k_thread_suspend / k_thread_resume

```c
void k_thread_suspend(k_tid_t thread);
void k_thread_resume(k_tid_t thread);
```

Suspend prevents scheduling until resumed. Multiple suspends require equal resumes.

### k_sleep / k_msleep / k_usleep

```c
int32_t k_sleep(k_timeout_t timeout);
int32_t k_msleep(int32_t ms);
int32_t k_usleep(int32_t us);
```

**Returns:** Time remaining if interrupted, 0 otherwise.

### k_yield

```c
void k_yield(void);
```

Cooperative yield to equal or higher priority threads.

### k_thread_priority_set / k_thread_priority_get

```c
void k_thread_priority_set(k_tid_t thread, int prio);
int k_thread_priority_get(k_tid_t thread);
```

### k_thread_name_set / k_thread_name_get

```c
int k_thread_name_set(k_tid_t thread, const char *name);
const char *k_thread_name_get(k_tid_t thread);
```

Requires `CONFIG_THREAD_NAME=y`.

### k_current_get

```c
k_tid_t k_current_get(void);
```

Returns current thread ID. Can be called from ISR (returns NULL if no current thread).

## Semaphore API

### k_sem_init

```c
int k_sem_init(struct k_sem *sem, unsigned int initial_count, unsigned int limit);
```

**Returns:** `0` on success.

**Note:** Can be called multiple times on same semaphore, but waiters may be orphaned.

### k_sem_give

```c
void k_sem_give(struct k_sem *sem);
```

**ISR-safe:** Yes. Increments count, wakes one waiting thread.

### k_sem_take

```c
int k_sem_take(struct k_sem *sem, k_timeout_t timeout);
```

**Returns:**
- `0` — Success
- `-EAGAIN` — Timeout
- `-EBUSY` — Non-blocking (`K_NO_WAIT`) and unavailable

### k_sem_reset

```c
void k_sem_reset(struct k_sem *sem);
```

Resets count to 0. Does not wake waiters.

### k_sem_count_get

```c
unsigned int k_sem_count_get(struct k_sem *sem);
```

## Mutex API

### k_mutex_init

```c
int k_mutex_init(struct k_mutex *mutex);
```

**Returns:** `0` on success.

### k_mutex_lock

```c
int k_mutex_lock(struct k_mutex *mutex, k_timeout_t timeout);
```

**Returns:**
- `0` — Success
- `-EAGAIN` — Timeout
- `-EBUSY` — Non-blocking and locked

**Priority inheritance:** Automatic. If low-priority thread holds mutex and high-priority thread waits, low-priority thread temporarily inherits high priority.

**Recursive locking:** Supported. Lock count must be balanced with unlock count.

### k_mutex_unlock

```c
int k_mutex_unlock(struct k_mutex *mutex);
```

**Returns:** `0` on success, `-EPERM` if not owner.

## Condition Variable API

### k_condvar_init

```c
int k_condvar_init(struct k_condvar *condvar);
```

### k_condvar_wait

```c
int k_condvar_wait(struct k_condvar *condvar, struct k_mutex *mutex, k_timeout_t timeout);
```

**Returns:**
- `0` — Signaled
- `-EAGAIN` — Timeout

Atomically unlocks mutex and waits. Reacquires mutex before returning.

### k_condvar_signal / k_condvar_broadcast

```c
int k_condvar_signal(struct k_condvar *condvar);
int k_condvar_broadcast(struct k_condvar *condvar);
```

`signal` wakes one waiter. `broadcast` wakes all waiters.

## Message Queue API

### k_msgq_init

```c
void k_msgq_init(struct k_msgq *msgq, char *buffer, size_t msg_size, uint32_t max_msgs);
```

**Buffer alignment:** Must be 4-byte aligned (use `__aligned(4)`).

**Buffer size:** `max_msgs * msg_size`

### k_msgq_put

```c
int k_msgq_put(struct k_msgq *msgq, const void *data, k_timeout_t timeout);
```

**Returns:**
- `0` — Success
- `-EAGAIN` — Timeout
- `-ENOMSG` — Immediate return (`K_NO_WAIT`) and queue full

Copies `msg_size` bytes from `data`.

### k_msgq_get

```c
int k_msgq_get(struct k_msgq *msgq, void *data, k_timeout_t timeout);
```

**Returns:**
- `0` — Success
- `-EAGAIN` — Timeout
- `-ENOMSG` — Immediate return and queue empty

Copies `msg_size` bytes to `data`.

### k_msgq_peek / k_msgq_peek_at

```c
int k_msgq_peek(struct k_msgq *msgq, void *data);
int k_msgq_peek_at(struct k_msgq *msgq, void *data, uint32_t idx);
```

Read without removing. `peek` reads oldest, `peek_at` reads at index.

### k_msgq_purge

```c
void k_msgq_purge(struct k_msgq *msgq);
```

Discards all messages.

### k_msgq_num_used_get / k_msgq_num_free_get

```c
uint32_t k_msgq_num_used_get(struct k_msgq *msgq);
uint32_t k_msgq_num_free_get(struct k_msgq *msgq);
```

## Timer API

### k_timer_init

```c
void k_timer_init(struct k_timer *timer, k_timer_expiry_t expiry_fn, k_timer_stop_t stop_fn);
```

**Callback signatures:**
```c
void expiry_fn(struct k_timer *timer);  /* Called in ISR context */
void stop_fn(struct k_timer *timer);    /* Called when stopped */
```

### k_timer_start

```c
void k_timer_start(struct k_timer *timer, k_timeout_t duration, k_timeout_t period);
```

**Parameters:**
- `duration` — Initial expiry delay
- `period` — Repeat interval (`K_NO_WAIT` or `K_FOREVER` for one-shot)

### k_timer_stop

```c
void k_timer_stop(struct k_timer *timer);
```

Calls `stop_fn` if set.

### k_timer_status_get / k_timer_status_sync

```c
uint32_t k_timer_status_get(struct k_timer *timer);
uint32_t k_timer_status_sync(struct k_timer *timer);
```

`status_get` returns and resets expiry count. `status_sync` blocks until next expiry.

### k_timer_remaining_get

```c
uint32_t k_timer_remaining_get(struct k_timer *timer);
```

Returns milliseconds until next expiry.

## Work Queue API

### k_work_init

```c
void k_work_init(struct k_work *work, k_work_handler_t handler);
```

**Handler signature:**
```c
void handler(struct k_work *work);
```

### k_work_submit / k_work_submit_to_queue

```c
int k_work_submit(struct k_work *work);
int k_work_submit_to_queue(struct k_work_q *queue, struct k_work *work);
```

`k_work_submit` uses system work queue. Returns:
- `0` — Work already submitted
- `1` — Work newly submitted
- `-EBUSY` — Work being processed

**ISR-safe:** Yes.

### k_work_init_delayable

```c
void k_work_init_delayable(struct k_work_delayable *dwork, k_work_handler_t handler);
```

### k_work_schedule / k_work_reschedule

```c
int k_work_schedule(struct k_work_delayable *dwork, k_timeout_t delay);
int k_work_reschedule(struct k_work_delayable *dwork, k_timeout_t delay);
```

`schedule` does nothing if already scheduled. `reschedule` cancels and resubmits.

### k_work_cancel / k_work_cancel_delayable

```c
int k_work_cancel(struct k_work *work);
int k_work_cancel_delayable(struct k_work_delayable *dwork);
```

**Returns:** `0` if not submitted, `1` if canceled.

**Note:** May return after work starts executing but before completion.

### k_work_cancel_sync / k_work_cancel_delayable_sync

```c
bool k_work_cancel_sync(struct k_work *work, struct k_work_sync *sync);
bool k_work_cancel_delayable_sync(struct k_work_delayable *dwork, struct k_work_sync *sync);
```

Waits for work to complete if executing. Cannot be called from work queue thread.

### k_work_queue_init / k_work_queue_start

```c
void k_work_queue_init(struct k_work_q *queue);
void k_work_queue_start(struct k_work_q *queue, k_thread_stack_t *stack,
                        size_t stack_size, int prio, const struct k_work_queue_config *cfg);
```

Create custom work queue with dedicated thread.

## Memory Management API

### k_heap_init

```c
void k_heap_init(struct k_heap *heap, void *mem, size_t bytes);
```

### k_heap_alloc / k_heap_aligned_alloc

```c
void *k_heap_alloc(struct k_heap *heap, size_t bytes, k_timeout_t timeout);
void *k_heap_aligned_alloc(struct k_heap *heap, size_t align, size_t bytes, k_timeout_t timeout);
```

**Returns:** Pointer or NULL on failure/timeout.

### k_heap_free

```c
void k_heap_free(struct k_heap *heap, void *mem);
```

### k_heap_realloc

```c
void *k_heap_realloc(struct k_heap *heap, void *ptr, size_t bytes, k_timeout_t timeout);
```

**New in Zephyr 3.7.**

### k_malloc / k_free / k_calloc / k_realloc

```c
void *k_malloc(size_t size);
void k_free(void *ptr);
void *k_calloc(size_t nmemb, size_t size);
void *k_realloc(void *ptr, size_t size);
```

Uses kernel heap. Requires `CONFIG_HEAP_MEM_POOL_SIZE > 0`.

### k_mem_slab_init

```c
int k_mem_slab_init(struct k_mem_slab *slab, void *buffer, size_t block_size, uint32_t num_blocks);
```

### k_mem_slab_alloc

```c
int k_mem_slab_alloc(struct k_mem_slab *slab, void **mem, k_timeout_t timeout);
```

**Returns:** `0` on success, `-EAGAIN` on timeout, `-ENOMEM` if immediate and unavailable.

### k_mem_slab_free

```c
void k_mem_slab_free(struct k_mem_slab *slab, void *mem);
```

## Polling API

### k_poll

```c
int k_poll(struct k_poll_event *events, int num_events, k_timeout_t timeout);
```

**Event types:**
```c
struct k_poll_event {
    int type;           /* K_POLL_TYPE_SEM_AVAILABLE, K_POLL_TYPE_SIGNAL, ... */
    int state;          /* K_POLL_STATE_NOT_READY, K_POLL_STATE_SEM_AVAILABLE, ... */
    int mode;           /* K_POLL_MODE_NOTIFY_ONLY */
    void *obj;          /* Pointer to sem, signal, etc. */
};
```

**Initializer:**
```c
K_POLL_EVENT_INITIALIZER(type, mode, obj);
```

**Returns:** `0` on event ready, `-EAGAIN` on timeout, `-EINTR` on signal.

### k_poll_signal_init / k_poll_signal_raise / k_poll_signal_check

```c
void k_poll_signal_init(struct k_poll_signal *signal);
int k_poll_signal_raise(struct k_poll_signal *signal, int result);
void k_poll_signal_check(struct k_poll_signal *signal, unsigned int *signaled, int *result);
```

## Device Driver API

### DEVICE_DT_GET / DEVICE_DT_GET_OR_NULL

```c
const struct device *dev = DEVICE_DT_GET(node_id);
const struct device *dev = DEVICE_DT_GET_OR_NULL(node_id);
```

**Compile-time binding.** `DEVICE_DT_GET` generates build error if node not found. `_OR_NULL` returns NULL.

### device_is_ready

```c
bool device_is_ready(const struct device *dev);
```

**ALWAYS call before using device.** Returns true if device initialized successfully.

### device_get_by_dt_nodelabel (Zephyr 3.7+)

```c
const struct device *device_get_by_dt_nodelabel(const char *label);
```

Human-friendly runtime lookup by devicetree nodelabel. Returns NULL if not found.

## Sensor API

### sensor_sample_fetch / sensor_sample_fetch_chan

```c
int sensor_sample_fetch(const struct device *dev);
int sensor_sample_fetch_chan(const struct device *dev, enum sensor_channel chan);
```

Triggers device to update internal sample buffers.

### sensor_channel_get

```c
int sensor_channel_get(const struct device *dev, enum sensor_channel chan, struct sensor_value *val);
```

Reads previously fetched sample.

**Common channels:**
- `SENSOR_CHAN_AMBIENT_TEMP`
- `SENSOR_CHAN_HUMIDITY`
- `SENSOR_CHAN_ACCEL_XYZ`
- `SENSOR_CHAN_GYRO_XYZ`
- `SENSOR_CHAN_LIGHT`
- `SENSOR_CHAN_PRESS`

### sensor_value structure

```c
struct sensor_value {
    int32_t val1;  /* Integer part */
    int32_t val2;  /* Fractional part in millionths */
};
```

**Conversion:**
```c
double value = val.val1 + val.val2 / 1000000.0;
```

## GPIO API

### gpio_pin_configure_dt

```c
int gpio_pin_configure_dt(const struct gpio_dt_spec *spec, gpio_flags_t extra_flags);
```

**Flags:** `GPIO_OUTPUT`, `GPIO_INPUT`, `GPIO_OUTPUT_ACTIVE`, `GPIO_OUTPUT_INACTIVE`, `GPIO_ACTIVE_LOW`, `GPIO_ACTIVE_HIGH`, `GPIO_PULL_UP`, `GPIO_PULL_DOWN`

### gpio_pin_set_dt / gpio_pin_get_dt / gpio_pin_toggle_dt

```c
int gpio_pin_set_dt(const struct gpio_dt_spec *spec, int value);
int gpio_pin_get_dt(const struct gpio_dt_spec *spec);
int gpio_pin_toggle_dt(const struct gpio_dt_spec *spec);
```

### gpio_pin_interrupt_configure_dt

```c
int gpio_pin_interrupt_configure_dt(const struct gpio_dt_spec *spec, gpio_flags_t flags);
```

**Flags:** `GPIO_INT_DISABLE`, `GPIO_INT_EDGE_RISING`, `GPIO_INT_EDGE_FALLING`, `GPIO_INT_EDGE_BOTH`, `GPIO_INT_LEVEL_LOW`, `GPIO_INT_LEVEL_HIGH`

### gpio_init_callback / gpio_add_callback

```c
void gpio_init_callback(struct gpio_callback *callback, gpio_callback_handler_t handler, gpio_port_pins_t pin_mask);
int gpio_add_callback(const struct device *port, struct gpio_callback *callback);
```

**Handler signature:**
```c
void handler(const struct device *port, struct gpio_callback *cb, gpio_port_pins_t pins);
```

**Called in ISR context.**

## Logging API

### LOG_MODULE_REGISTER / LOG_MODULE_DECLARE

```c
LOG_MODULE_REGISTER(module_name, log_level);  /* In one .c file */
LOG_MODULE_DECLARE(module_name, log_level);   /* In other .c files */
```

**Levels:** `LOG_LEVEL_NONE`, `LOG_LEVEL_ERR`, `LOG_LEVEL_WRN`, `LOG_LEVEL_INF`, `LOG_LEVEL_DBG`

### LOG_* Macros

```c
LOG_ERR(fmt, ...);   /* Error */
LOG_WRN(fmt, ...);   /* Warning */
LOG_INF(fmt, ...);   /* Info */
LOG_DBG(fmt, ...);   /* Debug */
LOG_HEXDUMP_DBG(data, length, "description");
LOG_HEXDUMP_INF(data, length, "description");
```

**Deferred logging:** Default. Formatted in separate thread. Requires `CONFIG_LOG=y`.

**Immediate logging:** Set `CONFIG_LOG_MODE_IMMEDIATE=y`. Formatted at call site (slower, ISR-safe).

### LOG_PRINTK

```c
LOG_PRINTK("Message\n");
```

Alias for `printk()` when logging enabled, direct `printk()` otherwise.

## Power Management API

### pm_device_action_run

```c
int pm_device_action_run(const struct device *dev, enum pm_device_action action);
```

**Actions:**
- `PM_DEVICE_ACTION_SUSPEND` — Put device in low-power state
- `PM_DEVICE_ACTION_RESUME` — Restore device to active state
- `PM_DEVICE_ACTION_TURN_OFF` — Complete power off
- `PM_DEVICE_ACTION_TURN_ON` — Power on from off state

### pm_device_state_get / pm_device_state_set

```c
int pm_device_state_get(const struct device *dev, enum pm_device_state *state);
```

**States:** `PM_DEVICE_STATE_ACTIVE`, `PM_DEVICE_STATE_SUSPENDED`, `PM_DEVICE_STATE_OFF`

### System Power Management Hooks

```c
void pm_state_set(enum pm_state state, uint8_t substate_id);
void pm_state_exit_post_ops(enum pm_state state, uint8_t substate_id);
```

Application implements these to control system-wide power state transitions. Requires `CONFIG_PM=y`.

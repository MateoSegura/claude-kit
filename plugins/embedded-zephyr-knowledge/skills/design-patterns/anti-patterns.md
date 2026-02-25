# Zephyr Firmware Anti-Patterns

Catalog of common embedded firmware anti-patterns with BAD/GOOD code pairs. Each entry shows what NOT to do, why it's problematic, and the correct approach following Zephyr best practices.

## Architectural Anti-Patterns

### Anti-Pattern: God Module

**Description:** Single monolithic file containing all application logic — sensor handling, BLE, storage, display, state management.

**BAD:**

```c
/* main.c - 2000+ lines of everything */

static struct k_thread sensor_thread;
static struct k_thread ble_thread;
static struct k_msgq sensor_queue;
static struct k_msgq ble_queue;
static struct k_mutex storage_mutex;
static struct k_heap app_heap;
static bool connected = false;
static int current_state = 0;
static uint8_t sensor_data[128];

void sensor_init(void) { /* ... */ }
void ble_init(void) { /* ... */ }
void storage_init(void) { /* ... */ }
void display_init(void) { /* ... */ }
void sensor_thread_fn(void) { /* ... */ }
void ble_thread_fn(void) { /* ... */ }
void process_sensor_data(void) { /* ... */ }
void update_display(void) { /* ... */ }
/* ...hundreds more lines... */

int main(void)
{
    sensor_init();
    ble_init();
    storage_init();
    display_init();
    /* ... */
}
```

**Why it's bad:**
- All state is global and accessible from anywhere — no encapsulation
- Testing requires bringing up entire application, cannot test subsystems in isolation
- Multiple developers cannot work on the same file without merge conflicts
- No clear module boundaries, high coupling between unrelated features
- Impossible to reason about ownership of OS primitives (who creates/destroys what?)

**GOOD:**

```c
/* Decomposed into subsystem modules */

/* sensor_manager.h */
int sensor_manager_init(void);
int sensor_manager_get_reading(struct sensor_reading *out, k_timeout_t timeout);

/* ble_connection.h */
int ble_connection_init(void);
int ble_connection_send_data(const uint8_t *data, size_t len);

/* storage_manager.h */
int storage_manager_init(void);
int storage_manager_write(const void *data, size_t len);

/* display_manager.h */
int display_manager_init(void);
int display_manager_update(const struct sensor_reading *reading);

/* main.c - orchestration only */
int main(void)
{
    int ret;

    ret = sensor_manager_init();
    if (ret < 0) {
        LOG_ERR("Sensor init failed: %d", ret);
        return ret;
    }

    ret = ble_connection_init();
    if (ret < 0) {
        LOG_ERR("BLE init failed: %d", ret);
        return ret;
    }

    ret = storage_manager_init();
    if (ret < 0) {
        LOG_WRN("Storage init failed, running without persistence");
    }

    ret = display_manager_init();
    if (ret < 0) {
        LOG_WRN("Display init failed, headless mode");
    }

    LOG_INF("Application initialized");
    return 0;
}
```

Each subsystem lives in `sensor_manager.c`, `ble_connection.c`, etc., with all state private (static) to that file.

**Cross-reference:** Non-negotiable #2 (Subsystem decomposition), Architecture Principles section

---

### Anti-Pattern: Circular Dependencies

**Description:** Module A calls module B, module B calls module A. Creates tight coupling and prevents independent testing.

**BAD:**

```c
/* sensor_manager.c */
#include "network_manager.h"

void sensor_data_ready(const struct sensor_reading *reading)
{
    /* Sensor directly calls network — tight coupling */
    network_send_sensor_data(reading);
}

/* network_manager.c */
#include "sensor_manager.h"

void network_connected(void)
{
    /* Network directly calls sensor — circular dependency */
    sensor_start_streaming();
}
```

**Why it's bad:**
- Cannot compile `sensor_manager.c` without `network_manager.h` and vice versa
- Cannot test sensor manager without linking network manager
- Changes to network API require recompiling sensor manager
- Creates fragile, tightly coupled architecture

**GOOD:**

```c
/* Use event-based decoupling via message queue or k_event */

/* sensor_manager.c */
#include "event_dispatcher.h"

void sensor_data_ready(const struct sensor_reading *reading)
{
    struct event event = {
        .type = EVENT_SENSOR_DATA,
        .data = reading,
    };

    event_publish(&event);  /* Publish to event bus */
}

/* network_manager.c */
#include "event_dispatcher.h"

static void network_event_handler(const struct event *event)
{
    if (event->type == EVENT_SENSOR_DATA) {
        const struct sensor_reading *reading = event->data;
        network_send_data(reading, sizeof(*reading));
    }
}

int network_manager_init(void)
{
    /* Subscribe to sensor events */
    event_subscribe(network_event_handler, (1 << EVENT_SENSOR_DATA));
    return 0;
}
```

Sensor and network modules never reference each other's headers. They communicate through the event dispatcher.

**Cross-reference:** Communication Patterns section (Publish-Subscribe)

---

### Anti-Pattern: Leaky Abstraction

**Description:** Application code reaches through abstraction layers to directly access hardware registers or driver internals.

**BAD:**

```c
/* Application directly manipulates GPIO registers */
#include <nrf52840.h>  /* SoC-specific header */

void set_led_state(bool on)
{
    if (on) {
        NRF_P0->OUTSET = (1 << 13);  /* Direct register write */
    } else {
        NRF_P0->OUTCLR = (1 << 13);
    }
}
```

**Why it's bad:**
- Hardcoded pin number (13) — not configurable via devicetree
- Direct register access — breaks portability to other SoCs
- Bypasses Zephyr GPIO driver — no power management integration
- Cannot switch boards without changing application code

**GOOD:**

```c
/* Use Zephyr HAL abstraction */
#include <zephyr/drivers/gpio.h>
#include <zephyr/devicetree.h>

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);

int led_init(void)
{
    if (!gpio_is_ready_dt(&led)) {
        LOG_ERR("LED GPIO not ready");
        return -ENODEV;
    }

    return gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
}

void set_led_state(bool on)
{
    gpio_pin_set_dt(&led, on ? 1 : 0);
}
```

Pin configuration comes from devicetree. Code is portable across any board with an `led0` nodelabel.

**Cross-reference:** Non-negotiable #2 (HAL APIs only), Portability Mandate section

---

### Anti-Pattern: Monolithic Init

**Description:** Single massive init function that initializes everything in a fixed order, with no error handling or dependency resolution.

**BAD:**

```c
void init_everything(void)
{
    /* No error checking, rigid order, no modularity */
    i2c_init();
    sensor_init();
    spi_init();
    display_init();
    ble_init();
    storage_init();
    /* If any of these fail, no way to know which one */
}

int main(void)
{
    init_everything();
    /* Assume everything worked */
}
```

**Why it's bad:**
- No error handling — failures are silent
- Rigid initialization order — cannot express dependencies
- Monolithic function — cannot selectively init subsystems for testing
- Cannot gracefully degrade if non-critical subsystem fails

**GOOD:**

```c
/* Use SYS_INIT for automatic ordering + explicit init from main */

/* sensor_manager.c */
static int sensor_manager_early_init(void)
{
    /* Early hardware init that must happen before APPLICATION level */
    return sensor_hw_setup();
}
SYS_INIT(sensor_manager_early_init, POST_KERNEL, 10);

/* main.c */
int main(void)
{
    int ret;

    /* Critical subsystems — fail fast */
    ret = sensor_manager_init();
    if (ret < 0) {
        LOG_ERR("Critical: sensor init failed: %d", ret);
        return ret;
    }

    ret = ble_connection_init();
    if (ret < 0) {
        LOG_ERR("Critical: BLE init failed: %d", ret);
        return ret;
    }

    /* Non-critical subsystems — graceful degradation */
    ret = storage_manager_init();
    if (ret < 0) {
        LOG_WRN("Storage unavailable, running in volatile mode: %d", ret);
    }

    ret = display_manager_init();
    if (ret < 0) {
        LOG_WRN("Display unavailable, headless mode: %d", ret);
    }

    LOG_INF("Application initialized (some subsystems degraded)");
    return 0;
}
```

**Cross-reference:** Initialization Patterns section

---

## Concurrency Anti-Patterns

### Anti-Pattern: Global Shared State

**Description:** Modules communicate by reading/writing global variables without synchronization or with inadequate locking.

**BAD:**

```c
/* Global shared variables */
static int current_temperature = 0;  /* Written by sensor thread, read by display thread */
static bool ble_connected = false;   /* Written by BLE thread, read by app thread */

/* Sensor thread */
void sensor_thread(void)
{
    while (1) {
        current_temperature = read_sensor();  /* RACE: multiple readers/writers */
        k_sleep(K_MSEC(100));
    }
}

/* Display thread */
void display_thread(void)
{
    while (1) {
        int temp = current_temperature;  /* RACE: may read partial update */
        update_display(temp);
        k_sleep(K_MSEC(200));
    }
}
```

**Why it's bad:**
- Race condition: sensor writes, display reads, no synchronization
- No atomic guarantee: `int` write/read may not be atomic on all platforms
- Implicit coupling: modules share state without explicit contract
- Cannot test modules independently — shared global state

**GOOD:**

```c
/* Use message queue for inter-thread communication */

static struct k_msgq sensor_queue;
static char __aligned(4) queue_buffer[5 * sizeof(int)];

/* Sensor thread */
void sensor_thread(void)
{
    while (1) {
        int temp = read_sensor();
        k_msgq_put(&sensor_queue, &temp, K_NO_WAIT);  /* Explicit communication */
        k_sleep(K_MSEC(100));
    }
}

/* Display thread */
void display_thread(void)
{
    int temp;

    while (1) {
        if (k_msgq_get(&sensor_queue, &temp, K_NO_WAIT) == 0) {
            update_display(temp);
        }
        k_sleep(K_MSEC(200));
    }
}

int init(void)
{
    k_msgq_init(&sensor_queue, queue_buffer, sizeof(int), 5);
    /* Create threads */
}
```

Message queue provides synchronization, explicit data flow, and clear ownership.

**Cross-reference:** Non-negotiable #4 (Message queues over shared state)

---

### Anti-Pattern: Priority Inversion Without Mitigation

**Description:** High-priority thread blocked waiting for resource held by low-priority thread, medium-priority thread prevents low-priority from running.

**BAD:**

```c
/* Using spinlock (no priority inheritance) */
static struct k_spinlock resource_lock;

void low_priority_task(void)
{
    k_spinlock_key_t key = k_spin_lock(&resource_lock);

    /* Long operation while holding lock */
    process_slow_operation();

    k_spin_unlock(&resource_lock, key);
}

void high_priority_task(void)
{
    /* High-priority thread blocks here if low-priority holds lock */
    k_spinlock_key_t key = k_spin_lock(&resource_lock);

    /* If medium-priority thread is runnable, low-priority may never finish */
    access_resource();

    k_spin_unlock(&resource_lock, key);
}
```

**Why it's bad:**
- Spinlock does not implement priority inheritance
- High-priority thread can be blocked indefinitely by low-priority thread
- Classic priority inversion scenario
- Spinlocks should only be used for very short critical sections (microseconds)

**GOOD:**

```c
/* Use mutex (automatic priority inheritance) */
static struct k_mutex resource_mutex;

void low_priority_task(void)
{
    k_mutex_lock(&resource_mutex, K_FOREVER);

    /* Low-priority thread inherits high-priority if high-priority waits */
    process_slow_operation();

    k_mutex_unlock(&resource_mutex);
}

void high_priority_task(void)
{
    k_mutex_lock(&resource_mutex, K_FOREVER);

    /* If low-priority holds mutex, it temporarily inherits this thread's priority */
    access_resource();

    k_mutex_unlock(&resource_mutex);
}

int init(void)
{
    k_mutex_init(&resource_mutex);
}
```

Mutex automatically implements priority inheritance, preventing unbounded priority inversion.

**Cross-reference:** zephyr-kernel/concurrency-patterns.md (Mutex with Priority Inheritance)

---

### Anti-Pattern: Blocking in ISR

**Description:** ISR performs blocking operations (semaphore wait, mutex lock, sleep, I2C/SPI transaction).

**BAD:**

```c
void gpio_interrupt_handler(const struct device *dev,
                             struct gpio_callback *cb,
                             gpio_port_pins_t pins)
{
    /* WRONG: blocking operations in ISR context */
    k_sleep(K_MSEC(50));  /* Debounce delay — BLOCKS ISR */

    uint8_t data[4];
    i2c_read(i2c_dev, data, sizeof(data), 0x48);  /* Blocking I2C read in ISR */

    k_mutex_lock(&data_mutex, K_FOREVER);  /* Mutex lock in ISR — undefined behavior */
    process_data(data);
    k_mutex_unlock(&data_mutex);
}
```

**Why it's bad:**
- ISRs cannot block — `k_sleep()`, `k_mutex_lock()`, `k_sem_take()` are illegal
- I2C/SPI transactions are blocking — cannot be called from ISR
- ISR should be fast (microseconds) — long operations delay other interrupts
- Undefined behavior — may cause system crash or deadlock

**GOOD:**

```c
/* ISR signals semaphore, defers work to thread context */

static struct k_sem data_ready_sem;

void gpio_interrupt_handler(const struct device *dev,
                             struct gpio_callback *cb,
                             gpio_port_pins_t pins)
{
    /* ISR does minimal work — just signal semaphore */
    k_sem_give(&data_ready_sem);  /* ISR-safe */
}

void data_handler_thread(void)
{
    while (1) {
        k_sem_take(&data_ready_sem, K_FOREVER);

        /* Thread context — can block, sleep, use I2C/SPI */
        k_sleep(K_MSEC(50));  /* Debounce delay */

        uint8_t data[4];
        i2c_read(i2c_dev, data, sizeof(data), 0x48);

        k_mutex_lock(&data_mutex, K_FOREVER);
        process_data(data);
        k_mutex_unlock(&data_mutex);
    }
}
```

ISR signals semaphore (ISR-safe), thread context handles blocking operations.

**Cross-reference:** zephyr-kernel/concurrency-patterns.md (ISR-Safe Signaling)

---

### Anti-Pattern: Busy-Wait Polling

**Description:** Thread spins in tight loop checking for condition instead of blocking on synchronization primitive.

**BAD:**

```c
static volatile bool data_ready = false;  /* Set by ISR */

void polling_thread(void)
{
    while (1) {
        /* Busy-wait loop — wastes CPU cycles */
        while (!data_ready) {
            /* Spin waiting for ISR to set flag */
        }

        data_ready = false;
        process_data();
    }
}
```

**Why it's bad:**
- Busy-waiting consumes CPU even when no work to do
- Prevents lower-priority threads from running
- Terrible power efficiency — CPU never enters idle state
- `volatile` does not guarantee atomicity or memory ordering

**GOOD:**

```c
/* Use semaphore to block thread until data ready */

static struct k_sem data_ready_sem;

void data_isr(void)
{
    /* ISR signals semaphore */
    k_sem_give(&data_ready_sem);
}

void blocking_thread(void)
{
    while (1) {
        /* Block until ISR signals — CPU can sleep */
        k_sem_take(&data_ready_sem, K_FOREVER);

        process_data();
    }
}

int init(void)
{
    k_sem_init(&data_ready_sem, 0, 1);
}
```

Thread blocks on semaphore, CPU enters idle state, wakes only when ISR signals.

**Cross-reference:** zephyr-kernel/concurrency-patterns.md (ISR-Safe Signaling)

---

## Memory Anti-Patterns

### Anti-Pattern: System Heap Abuse

**Description:** Application uses `k_malloc()`/`k_free()` (system heap) for dynamic allocation instead of private heaps.

**BAD:**

```c
void process_sensor_data(void)
{
    /* Allocating from system heap */
    uint8_t *buffer = k_malloc(256);
    if (!buffer) {
        LOG_ERR("Out of memory");
        return;
    }

    read_sensor_into_buffer(buffer);
    process_buffer(buffer);

    k_free(buffer);
}
```

**Why it's bad:**
- System heap is shared and unbounded — any module can exhaust it
- No per-module memory accounting — cannot track which module leaked memory
- System heap can be disabled via Kconfig — code breaks
- No isolation — one module's leak affects entire system

**GOOD:**

```c
/* Use private heap per module */

K_HEAP_DEFINE(sensor_heap, 4096);  /* Bounded heap, 4KB total */

void process_sensor_data(void)
{
    /* Allocate from private heap */
    uint8_t *buffer = k_heap_alloc(&sensor_heap, 256, K_NO_WAIT);
    if (!buffer) {
        LOG_ERR("Sensor heap exhausted");
        return;
    }

    read_sensor_into_buffer(buffer);
    process_buffer(buffer);

    k_heap_free(&sensor_heap, buffer);
}
```

Private heap has bounded size (4KB), module-specific accounting, isolation from other modules.

**Cross-reference:** Non-negotiable #5 (Private heaps only)

---

### Anti-Pattern: Unbounded Dynamic Allocation

**Description:** Allocating memory in a loop or on every event without bounds checking or pool limits.

**BAD:**

```c
void sensor_event_handler(const struct sensor_reading *reading)
{
    /* Allocate new buffer on every sensor reading — unbounded */
    struct sensor_reading *copy = k_malloc(sizeof(*copy));
    if (!copy) {
        /* Out of memory — but how many allocations already happened? */
        return;
    }

    memcpy(copy, reading, sizeof(*copy));
    k_msgq_put(&storage_queue, &copy, K_NO_WAIT);

    /* No free() — memory leak */
}
```

**Why it's bad:**
- No upper bound on allocations — will eventually exhaust heap
- Memory leak: `copy` is allocated but never freed
- No backpressure: if storage cannot keep up, allocations continue
- Heap fragmentation over time

**GOOD:**

```c
/* Use fixed-size memory slab (bounded pool) */

#define MAX_SENSOR_BUFFERS 10

K_MEM_SLAB_DEFINE(sensor_slab, sizeof(struct sensor_reading),
                  MAX_SENSOR_BUFFERS, 4);

void sensor_event_handler(const struct sensor_reading *reading)
{
    struct sensor_reading *copy;

    /* Allocate from bounded pool */
    int ret = k_mem_slab_alloc(&sensor_slab, (void **)&copy, K_NO_WAIT);
    if (ret != 0) {
        LOG_WRN("Sensor buffer pool exhausted (max %d), dropping sample",
                MAX_SENSOR_BUFFERS);
        return;  /* Bounded failure — cannot allocate more than MAX */
    }

    memcpy(copy, reading, sizeof(*copy));
    k_msgq_put(&storage_queue, &copy, K_NO_WAIT);
}

void storage_thread(void)
{
    struct sensor_reading *reading;

    while (1) {
        k_msgq_get(&storage_queue, &reading, K_FOREVER);

        write_to_storage(reading);

        /* Consumer frees buffer back to pool */
        k_mem_slab_free(&sensor_slab, reading);
    }
}
```

Memory slab has fixed size (10 buffers max), constant-time alloc/free, no fragmentation, bounded memory usage.

**Cross-reference:** Memory Management Patterns section (Static Buffer Pool)

---

### Anti-Pattern: Stack Overflow

**Description:** Thread stack sized by guessing, no measurement, crashes when stack exhausted.

**BAD:**

```c
/* Guessed stack size — no analysis */
K_THREAD_STACK_DEFINE(worker_stack, 512);  /* Is 512 enough? Who knows? */

struct k_thread worker_thread;

void worker_entry(void)
{
    char local_buffer[256];  /* Large stack allocation */
    recursive_function(10);  /* Unknown stack depth */

    /* Stack overflow — undefined behavior, likely crash */
}

int main(void)
{
    k_thread_create(&worker_thread, worker_stack, 512,
                    worker_entry, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(5), 0, K_NO_WAIT);
}
```

**Why it's bad:**
- Stack size chosen arbitrarily (512 bytes) — no measurement
- Large local buffer (256 bytes) + recursion = high stack usage
- No overflow detection — crash is silent and hard to debug
- Wastes RAM if oversized, crashes if undersized

**GOOD:**

```c
/* Enable stack analysis */
/* In prj.conf:
CONFIG_THREAD_STACK_INFO=y
CONFIG_THREAD_ANALYZER=y
*/

/* Initial stack size based on worst-case estimate */
K_THREAD_STACK_DEFINE(worker_stack, 2048);

struct k_thread worker_thread;

void worker_entry(void)
{
    char local_buffer[256];
    recursive_function(10);
}

int main(void)
{
    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack),
                    worker_entry, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

    k_thread_name_set(&worker_thread, "worker");

    /* After running under load, measure actual usage */
    k_sleep(K_SECONDS(60));  /* Let system run */

    size_t unused;
    int ret = k_thread_stack_space_get(&worker_thread, &unused);
    if (ret == 0) {
        size_t used = K_THREAD_STACK_SIZEOF(worker_stack) - unused;
        LOG_INF("Worker stack: %zu/%zu bytes used (%zu free)",
                used, K_THREAD_STACK_SIZEOF(worker_stack), unused);

        /* Rule of thumb: keep 25% margin */
        size_t recommended = used + (used / 4);
        LOG_INF("Recommended stack size: %zu bytes", recommended);
    }
}
```

Enable stack analysis, measure actual usage, add 25% margin, resize stack in code.

**Cross-reference:** Memory Management Patterns section (Stack Sizing Methodology)

---

### Anti-Pattern: VLA Usage

**Description:** Variable-length arrays (VLAs) used on stack, creating unpredictable stack usage.

**BAD:**

```c
void process_samples(int num_samples)
{
    /* VLA — stack size depends on runtime parameter */
    uint16_t samples[num_samples];  /* DANGER: stack usage unknown at compile time */

    for (int i = 0; i < num_samples; i++) {
        samples[i] = read_adc();
    }

    compute_fft(samples, num_samples);
}
```

**Why it's bad:**
- VLAs allocate on stack with size determined at runtime
- Stack overflow risk if `num_samples` is large
- Cannot statically analyze stack requirements
- Forbidden by C17 (VLAs are optional in C11, removed in C17)
- Violates non-negotiable #10 (Strict C17 only)

**GOOD:**

```c
/* Option 1: Fixed-size array with limit check */
#define MAX_SAMPLES 128

void process_samples(int num_samples)
{
    if (num_samples > MAX_SAMPLES) {
        LOG_ERR("Too many samples: %d (max %d)", num_samples, MAX_SAMPLES);
        return;
    }

    uint16_t samples[MAX_SAMPLES];  /* Fixed size, known at compile time */

    for (int i = 0; i < num_samples; i++) {
        samples[i] = read_adc();
    }

    compute_fft(samples, num_samples);
}

/* Option 2: Heap allocation from private heap */
K_HEAP_DEFINE(dsp_heap, 2048);

void process_samples(int num_samples)
{
    size_t size = num_samples * sizeof(uint16_t);
    uint16_t *samples = k_heap_alloc(&dsp_heap, size, K_NO_WAIT);
    if (!samples) {
        LOG_ERR("Failed to allocate %zu bytes for %d samples", size, num_samples);
        return;
    }

    for (int i = 0; i < num_samples; i++) {
        samples[i] = read_adc();
    }

    compute_fft(samples, num_samples);

    k_heap_free(&dsp_heap, samples);
}
```

**Cross-reference:** Non-negotiable #10 (No VLAs)

---

## Error Handling Anti-Patterns

### Anti-Pattern: Silent Failure

**Description:** Function fails, returns error, caller ignores return value, continues with invalid state.

**BAD:**

```c
void init_system(void)
{
    sensor_init();  /* Returns int, but we ignore it */
    ble_init();     /* May have failed, we don't know */

    /* Assume everything worked */
    start_application();  /* Will crash if init failed */
}

int sensor_init(void)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));
    if (!device_is_ready(dev)) {
        return -ENODEV;  /* Caller ignores this */
    }

    return 0;
}
```

**Why it's bad:**
- Errors are returned but not checked
- System continues with invalid state (sensor not initialized)
- Crash occurs later, far from root cause
- Impossible to diagnose which init step failed

**GOOD:**

```c
void init_system(void)
{
    int ret;

    ret = sensor_init();
    if (ret < 0) {
        LOG_ERR("Sensor init failed: %d", ret);
        /* Decide: fail-fast or graceful degradation */
        return;
    }

    ret = ble_init();
    if (ret < 0) {
        LOG_ERR("BLE init failed: %d", ret);
        return;
    }

    LOG_INF("System initialized successfully");
    start_application();
}

int sensor_init(void)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));
    if (!device_is_ready(dev)) {
        LOG_ERR("Sensor device not ready");
        return -ENODEV;
    }

    LOG_INF("Sensor initialized");
    return 0;
}
```

Every return value checked, every error logged, fail-fast or degrade gracefully.

**Cross-reference:** Non-negotiable #6 (errno returns), Error Handling Patterns section

---

### Anti-Pattern: Assert in Production

**Description:** Using `assert()` or `__ASSERT()` for runtime error handling instead of returning error codes.

**BAD:**

```c
int read_sensor(struct sensor_reading *out)
{
    /* Assert on invalid input — crashes in production */
    __ASSERT(out != NULL, "NULL output pointer");

    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));

    /* Assert on hardware failure — crashes in production */
    __ASSERT(device_is_ready(dev), "Sensor not ready");

    int ret = sensor_sample_fetch(dev);

    /* Assert on I2C NAK — crashes in production */
    __ASSERT(ret == 0, "Sensor fetch failed");

    return 0;
}
```

**Why it's bad:**
- Assertions crash the system (or are compiled out in release builds)
- Hardware failures (I2C NAK, device not ready) are runtime errors, not programmer errors
- Caller cannot recover from failure — system halts
- Asserts are for development-only invariants, not production error paths

**GOOD:**

```c
int read_sensor(struct sensor_reading *out)
{
    /* Check for invalid input, return error */
    if (out == NULL) {
        LOG_ERR("NULL output pointer");
        return -EINVAL;
    }

    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));

    /* Check device readiness, return error */
    if (!device_is_ready(dev)) {
        LOG_ERR("Sensor device not ready");
        return -ENODEV;
    }

    /* Check sensor fetch, propagate error */
    int ret = sensor_sample_fetch(dev);
    if (ret < 0) {
        LOG_ERR("Sensor fetch failed: %d", ret);
        return ret;
    }

    /* Populate output on success */
    struct sensor_value val;
    sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val);
    out->temperature = val.val1;

    return 0;
}

/* Caller handles error */
int ret = read_sensor(&reading);
if (ret < 0) {
    LOG_WRN("Sensor read failed: %d, using cached value", ret);
    /* Graceful degradation */
}
```

Return negative errno, log error, caller decides how to handle.

**Cross-reference:** Non-negotiable #6 (Never assert in production paths)

---

### Anti-Pattern: Panic on Recoverable Error

**Description:** Triggering system reset or halt on transient, recoverable errors.

**BAD:**

```c
void network_send_data(const uint8_t *data, size_t len)
{
    int ret = ble_send(data, len);

    if (ret < 0) {
        /* BLE send failed — reset the entire system */
        LOG_ERR("BLE send failed, resetting system");
        sys_reboot(SYS_REBOOT_COLD);  /* Nuclear option */
    }
}
```

**Why it's bad:**
- BLE send failure is transient (connection lost, buffer full) — recoverable
- System reset destroys all state, interrupts user
- Better to retry, queue for later, or gracefully degrade
- Wastes user's work if reset is unnecessary

**GOOD:**

```c
#define MAX_SEND_RETRIES 3

int network_send_data(const uint8_t *data, size_t len)
{
    int retry_count = 0;

    while (retry_count < MAX_SEND_RETRIES) {
        int ret = ble_send(data, len);

        if (ret == 0) {
            return 0;  /* Success */
        }

        retry_count++;
        LOG_WRN("BLE send failed (attempt %d/%d): %d",
                retry_count, MAX_SEND_RETRIES, ret);

        k_sleep(K_MSEC(100));  /* Backoff before retry */
    }

    LOG_ERR("BLE send failed after %d retries, dropping data", MAX_SEND_RETRIES);
    return -EIO;  /* Propagate error, let caller decide next action */
}

/* Caller can retry later or queue data */
int ret = network_send_data(sensor_data, sizeof(sensor_data));
if (ret < 0) {
    LOG_INF("Queueing data for later transmission");
    storage_queue_for_retry(sensor_data, sizeof(sensor_data));
}
```

Retry transient errors, propagate persistent failures, let caller decide recovery strategy.

**Cross-reference:** Error Handling Patterns section (Retry with Backoff)

---

### Anti-Pattern: Missing device_is_ready Check

**Description:** Using device pointer from `DEVICE_DT_GET()` without checking if device is ready.

**BAD:**

```c
void init_sensor(void)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));

    /* No device_is_ready() check — dev may be NULL or not initialized */
    sensor_sample_fetch(dev);  /* Will crash if device not ready */

    struct sensor_value val;
    sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val);
}
```

**Why it's bad:**
- `DEVICE_DT_GET()` returns a pointer even if device doesn't exist or failed init
- Device may not be initialized yet (dependency ordering issue)
- Device driver init may have failed (hardware not present)
- Dereferencing invalid device pointer causes crash

**GOOD:**

```c
int init_sensor(void)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));

    /* Always check device_is_ready() before use */
    if (!device_is_ready(dev)) {
        LOG_ERR("BME280 sensor not ready");
        return -ENODEV;
    }

    int ret = sensor_sample_fetch(dev);
    if (ret < 0) {
        LOG_ERR("Sensor fetch failed: %d", ret);
        return ret;
    }

    struct sensor_value val;
    sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val);

    LOG_INF("Sensor initialized, temp=%d C", val.val1);
    return 0;
}
```

Always call `device_is_ready()` after `DEVICE_DT_GET()`, handle failure gracefully.

**Cross-reference:** zephyr-kernel skill (Device Driver Model section)

---

## Configuration Anti-Patterns

### Anti-Pattern: ifdef Spaghetti

**Description:** Using raw `#ifdef CONFIG_*` instead of `IS_ENABLED()` for feature toggles.

**BAD:**

```c
void process_data(const uint8_t *data, size_t len)
{
#ifdef CONFIG_APP_ENCRYPTION
    encrypt_data(data, len);
#endif

#ifdef CONFIG_APP_COMPRESSION
    compress_data(data, len);
#endif

#ifdef CONFIG_APP_CRC
    uint32_t crc = compute_crc(data, len);
    append_crc(crc);
#endif

    send_data(data, len);
}
```

**Why it's bad:**
- Preprocessor branches make code hard to read
- Typos in `CONFIG_*` symbol names compile silently (wrong behavior)
- Cannot use `if` statements with `#ifdef` (no early return)
- Nested `#ifdef` blocks become unreadable

**GOOD:**

```c
void process_data(const uint8_t *data, size_t len)
{
    if (IS_ENABLED(CONFIG_APP_ENCRYPTION)) {
        encrypt_data(data, len);
    }

    if (IS_ENABLED(CONFIG_APP_COMPRESSION)) {
        compress_data(data, len);
    }

    if (IS_ENABLED(CONFIG_APP_CRC)) {
        uint32_t crc = compute_crc(data, len);
        append_crc(crc);
    }

    send_data(data, len);
}
```

`IS_ENABLED()` works in regular `if` statements, compiler dead-code elimination removes disabled paths, typos are caught at compile time.

**Cross-reference:** Non-negotiable #9 (Kconfig with IS_ENABLED)

---

### Anti-Pattern: Hardcoded Hardware

**Description:** Pin numbers, peripheral addresses, clock frequencies hardcoded in C code instead of devicetree.

**BAD:**

```c
/* Hardcoded hardware configuration */
#define LED_PIN 13
#define LED_PORT "GPIO_0"
#define I2C_ADDR 0x76
#define I2C_FREQ 100000

void init_hardware(void)
{
    const struct device *gpio = device_get_binding(LED_PORT);  /* Deprecated API */
    gpio_pin_configure(gpio, LED_PIN, GPIO_OUTPUT);

    const struct device *i2c = device_get_binding("I2C_0");
    /* No way to configure I2C frequency from devicetree */
}
```

**Why it's bad:**
- Hardcoded pin 13 — breaks on different boards
- Port name "GPIO_0" is SoC-specific
- `device_get_binding()` is deprecated
- Cannot change hardware config without modifying C code
- No single source of truth for hardware configuration

**GOOD:**

```c
/* Hardware config from devicetree */

/* In board overlay (nrf52840dk_nrf52840.overlay):
&i2c0 {
    status = "okay";
    clock-frequency = <100000>;

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};

/ {
    leds {
        compatible = "gpio-leds";
        led0: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
        };
    };
};
*/

/* In C code: */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);

int init_hardware(void)
{
    if (!gpio_is_ready_dt(&led)) {
        LOG_ERR("LED GPIO not ready");
        return -ENODEV;
    }

    int ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
    if (ret < 0) {
        LOG_ERR("LED config failed: %d", ret);
        return ret;
    }

    const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(bme280));
    if (!device_is_ready(sensor)) {
        LOG_ERR("Sensor not ready");
        return -ENODEV;
    }

    LOG_INF("Hardware initialized");
    return 0;
}
```

All hardware parameters (pin, port, I2C address, clock frequency) come from devicetree. Switch boards by changing overlay, not C code.

**Cross-reference:** Non-negotiable #7 (Devicetree as single source of truth)

---

### Anti-Pattern: Missing Kconfig Dependencies

**Description:** Code assumes Kconfig symbols are enabled but doesn't explicitly list them in `prj.conf`.

**BAD:**

```c
/* Code depends on CONFIG_LOG=y but doesn't enable it */

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(my_module, LOG_LEVEL_INF);

void my_function(void)
{
    LOG_INF("Hello");  /* Silently does nothing if CONFIG_LOG=n */
}
```

**prj.conf:**
```
# Missing CONFIG_LOG=y
```

**Why it's bad:**
- Code depends on logging but doesn't enable `CONFIG_LOG`
- Logging calls compile but do nothing at runtime
- Implicit dependency — fragile if another module also needs logging
- Hard to diagnose why logs don't appear

**GOOD:**

```c
/* Same code */
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(my_module, LOG_LEVEL_INF);

void my_function(void)
{
    LOG_INF("Hello");
}
```

**prj.conf:**
```
# Logging subsystem
CONFIG_LOG=y
CONFIG_LOG_MODE_MINIMAL=n
CONFIG_LOG_BACKEND_UART=y

# I2C (needed by sensor driver)
CONFIG_I2C=y

# Sensor subsystem
CONFIG_SENSOR=y
CONFIG_BME280=y
```

Every dependency explicitly listed with comment explaining why.

**Cross-reference:** Kconfig Policy section (identity skill)

---

### Anti-Pattern: Late MCUboot Integration

**Description:** Building application without bootloader, attempting to add MCUboot later after memory layout is fixed.

**BAD:**

```bash
# Initial development without MCUboot
west build -b nrf52840dk_nrf52840 app

# Months later: "Now let's add OTA updates"
# Surprise: partition table needs surgery, flash layout changes, existing images break
```

**Why it's bad:**
- MCUboot changes memory layout (bootloader occupies flash, partition table required)
- Existing firmware images are not MCUboot-compatible
- Image signing, version management, rollback protection need to be retrofitted
- Weeks of integration pain, risk of bricking devices in field

**GOOD:**

```bash
# From day one: use sysbuild with MCUboot
west build -b nrf52840dk_nrf52840 --sysbuild app

# MCUboot configured from start:
# - Partition table defined
# - Image signing configured
# - Bootloader + application built together
# - OTA updates work from first deployment
```

**In prj.conf:**
```
# Sysbuild + MCUboot from day one
CONFIG_BOOTLOADER_MCUBOOT=y
CONFIG_IMG_MANAGER=y
CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION="1.0.0"
```

MCUboot integrated from first build. OTA updates work from day one, no retrofit pain.

**Cross-reference:** Non-negotiable #8 (Always sysbuild with MCUboot from day one)

---

Each anti-pattern cross-references the relevant non-negotiable rule from the identity skill and the specific design pattern that provides the correct approach.

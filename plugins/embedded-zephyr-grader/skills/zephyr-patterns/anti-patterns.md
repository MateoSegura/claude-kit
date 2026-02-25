# Anti-Patterns

Common Zephyr RTOS mistakes with BAD code examples, detailed failure mode explanations, and GOOD corrected code.

## Anti-Pattern 1: Sleeping in ISR

### What Developers Do Wrong

Call k_sleep(), k_msleep(), k_usleep(), or other blocking functions from interrupt context.

### BAD Code Example

```c
static struct k_sem data_sem;

ISR_DIRECT_DECLARE(uart_isr)
{
    uint8_t data = read_uart_register();

    // Process data (takes time)
    k_msleep(5);  // CRITICAL ERROR

    k_sem_give(&data_sem);
    return 1;
}
```

### Why It Fails

**Failure mode:** System crash, hard fault, or hang

**Detailed explanation:**

When an interrupt occurs, the CPU switches to interrupt context. This context has strict constraints:
1. No thread scheduler is active — interrupts preempt threads but don't have thread context
2. The interrupt stack is typically very small (CONFIG_ISR_STACK_SIZE, often 2KB)
3. Sleeping requires the scheduler to switch to another thread, but the scheduler cannot run in interrupt context

Calling k_msleep() in an ISR attempts to:
1. Put the "current thread" to sleep — but there is no current thread, there's only interrupt context
2. Invoke the scheduler — which is not available in interrupt context
3. Context switch — which cannot happen from an ISR

Result: **Immediate system crash, hard fault, or undefined behavior.**

### GOOD Code Example

```c
static struct k_sem data_sem;
static uint8_t data_buffer;

ISR_DIRECT_DECLARE(uart_isr)
{
    // Minimal work in ISR
    data_buffer = read_uart_register();

    // Signal thread to do the real work
    k_sem_give(&data_sem);

    return 1;
}

void uart_processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        // Block until ISR signals
        k_sem_take(&data_sem, K_FOREVER);

        // Now we can sleep/block (we're in thread context)
        process_data(data_buffer);
        k_msleep(5);  // OK in thread context
    }
}
```

---

## Anti-Pattern 2: Mutex Locking in ISR

### What Developers Do Wrong

Attempt to acquire a mutex from interrupt context using k_mutex_lock().

### BAD Code Example

```c
static struct k_mutex data_mutex;
static int shared_counter = 0;

ISR_DIRECT_DECLARE(timer_isr)
{
    k_mutex_lock(&data_mutex, K_FOREVER);  // CRITICAL ERROR
    shared_counter++;
    k_mutex_unlock(&data_mutex);

    return 1;
}

void worker_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_mutex_lock(&data_mutex, K_FOREVER);
        printk("Counter: %d\n", shared_counter);
        k_mutex_unlock(&data_mutex);
        k_msleep(1000);
    }
}
```

### Why It Fails

**Failure mode:** Deadlock or system crash

**Detailed explanation:**

Mutexes in Zephyr implement **priority inheritance** to prevent priority inversion. This requires scheduler interaction.

Scenario:
1. Worker thread (priority 10) acquires mutex
2. Timer ISR fires, preempts worker thread
3. ISR tries to acquire mutex → mutex is held by worker thread
4. Normal behavior: ISR should block and wait
5. **Problem:** ISRs cannot block! Blocking requires scheduler, which doesn't run in interrupt context
6. **Result:** Either immediate crash (attempted scheduler call from ISR) or deadlock (ISR spins forever because thread never runs to release mutex)

Additionally, priority inheritance requires the scheduler to boost the thread holding the mutex to the ISR's effective priority. This is meaningless because ISRs don't have thread priority.

### GOOD Code Example

**Option 1: Use atomic operations (best for simple counters)**

```c
static atomic_t shared_counter = ATOMIC_INIT(0);

ISR_DIRECT_DECLARE(timer_isr)
{
    atomic_inc(&shared_counter);  // Atomic, no lock needed
    return 1;
}

void worker_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        int val = atomic_get(&shared_counter);
        printk("Counter: %d\n", val);
        k_msleep(1000);
    }
}
```

**Option 2: Use semaphore for signaling + mutex in thread only**

```c
static struct k_mutex data_mutex;
static struct k_sem update_sem;
static int shared_counter = 0;
static int pending_increments = 0;

ISR_DIRECT_DECLARE(timer_isr)
{
    pending_increments++;  // Quick update (or use atomic)
    k_sem_give(&update_sem);  // Signal thread
    return 1;
}

void worker_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&update_sem, K_FOREVER);

        // Now in thread context, mutex is safe
        k_mutex_lock(&data_mutex, K_FOREVER);
        shared_counter += pending_increments;
        pending_increments = 0;
        printk("Counter: %d\n", shared_counter);
        k_mutex_unlock(&data_mutex);
    }
}
```

---

## Anti-Pattern 3: Unprotected Shared State Between ISR and Thread

### What Developers Do Wrong

Access global variables from both ISR and thread context without synchronization.

### BAD Code Example

```c
static uint32_t event_count = 0;  // BAD: No protection
static bool data_ready = false;   // BAD: No protection

ISR_DIRECT_DECLARE(sensor_isr)
{
    event_count++;      // CRITICAL: Race condition
    data_ready = true;  // CRITICAL: Race condition
    return 1;
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        if (data_ready) {  // CRITICAL: Race condition
            printk("Events: %u\n", event_count);  // CRITICAL: Torn read
            data_ready = false;  // CRITICAL: Race condition
        }
        k_msleep(100);
    }
}
```

### Why It Fails

**Failure mode:** Data corruption, torn reads, inconsistent state, race conditions

**Detailed explanation:**

Multiple problems occur:

1. **Non-atomic operations:** `event_count++` is typically 3 CPU instructions (load, increment, store). ISR can interrupt between any of these, causing lost increments.

2. **Torn reads:** On some architectures, reading a 32-bit value is not atomic. Thread might read half of old value and half of new value.

3. **Compiler optimization:** Compiler may optimize away the `data_ready` check, caching it in a register and never re-reading from memory.

4. **Memory ordering:** On multi-core systems, writes from ISR may not be visible to thread immediately due to cache coherency.

Example failure sequence:
```
event_count = 10
Thread: Load event_count into register → 10
        Increment register → 11
ISR fires (preempts thread)
ISR:    Load event_count (still 10) → 10
        Increment → 11
        Store → event_count = 11
ISR returns
Thread: Store register to event_count → 11
Result: One increment lost (should be 12, but is 11)
```

### GOOD Code Example

**Option 1: Use atomics for simple variables**

```c
static atomic_t event_count = ATOMIC_INIT(0);
static atomic_t data_ready = ATOMIC_INIT(0);

ISR_DIRECT_DECLARE(sensor_isr)
{
    atomic_inc(&event_count);
    atomic_set(&data_ready, 1);
    return 1;
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        if (atomic_get(&data_ready) == 1) {
            uint32_t count = atomic_get(&event_count);
            printk("Events: %u\n", count);
            atomic_set(&data_ready, 0);
        }
        k_msleep(100);
    }
}
```

**Option 2: Use ISR → thread signaling (best practice)**

```c
static struct k_sem event_sem;
static uint32_t event_count = 0;  // Only accessed by thread after semaphore

ISR_DIRECT_DECLARE(sensor_isr)
{
    k_sem_give(&event_sem);  // Atomic signaling
    return 1;
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&event_sem, K_FOREVER);
        event_count++;  // Safe: only modified here
        printk("Events: %u\n", event_count);
    }
}
```

---

## Anti-Pattern 4: Missing device_is_ready() Check

### What Developers Do Wrong

Use a device pointer from DEVICE_DT_GET() without checking if device is ready.

### BAD Code Example

```c
void app_init(void)
{
    const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

    // BAD: No ready check, direct use
    uint8_t data[2];
    i2c_read(i2c_dev, data, sizeof(data), 0x50);  // CRASH if device not ready
}
```

### Why It Fails

**Failure mode:** Null pointer dereference, hard fault, system crash

**Detailed explanation:**

DEVICE_DT_GET() returns a pointer to a device structure, but the device may not be:
1. Initialized (driver init function may have failed)
2. Present in hardware (devicetree says it exists, but hardware doesn't have it)
3. Ready to use (still in power-down state)

If device is not ready, the device pointer may be:
- NULL (causing immediate crash on dereference)
- Valid pointer but device->api is NULL (crash when calling API function)
- Valid but device is not initialized (hardware returns garbage, protocol errors)

Example scenario:
- I2C0 defined in devicetree
- I2C0 driver init function fails (wrong pin configuration)
- Device pointer is valid but device is not usable
- i2c_read() tries to access hardware → undefined behavior, possible crash

### GOOD Code Example

```c
int app_init(void)
{
    const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

    if (!device_is_ready(i2c_dev)) {
        LOG_ERR("I2C device not ready");
        return -ENODEV;
    }

    // Safe to use device
    uint8_t data[2];
    int ret = i2c_read(i2c_dev, data, sizeof(data), 0x50);
    if (ret != 0) {
        LOG_ERR("I2C read failed: %d", ret);
        return ret;
    }

    return 0;
}
```

---

## Anti-Pattern 5: Incorrect k_timer Usage

### What Developers Do Wrong

Define k_timer on stack or use without proper initialization/expiry function.

### BAD Code Example

```c
void start_timer(void)
{
    struct k_timer my_timer;  // BAD: Stack allocation, no init

    k_timer_start(&my_timer, K_MSEC(1000), K_NO_WAIT);  // Undefined behavior

    k_msleep(2000);
    // my_timer goes out of scope, but timer still running → crash
}
```

### Why It Fails

**Failure mode:** Use-after-free, memory corruption, crash

**Detailed explanation:**

Timers in Zephyr are kernel objects that must persist for the lifetime of the timer. When timer expires, the kernel:
1. Calls the expiry function (if provided)
2. Accesses the timer structure to check repeat settings
3. May reschedule the timer

If the timer structure is on the stack and goes out of scope, the kernel accesses freed memory → crash.

### GOOD Code Example

**Option 1: Static/global timer**

```c
static struct k_timer my_timer;

void timer_expiry_fn(struct k_timer *timer)
{
    printk("Timer expired\n");
}

void app_init(void)
{
    k_timer_init(&my_timer, timer_expiry_fn, NULL);
    k_timer_start(&my_timer, K_MSEC(1000), K_MSEC(1000));  // Repeat every 1s
}
```

**Option 2: Use K_TIMER_DEFINE macro**

```c
void timer_expiry_fn(struct k_timer *timer)
{
    printk("Timer expired\n");
}

K_TIMER_DEFINE(my_timer, timer_expiry_fn, NULL);

void app_init(void)
{
    k_timer_start(&my_timer, K_MSEC(1000), K_MSEC(1000));
}
```

---

## Anti-Pattern 6: Raw Register Access Instead of Zephyr APIs

### What Developers Do Wrong

Directly access hardware registers instead of using Zephyr device drivers.

### BAD Code Example

```c
// BAD: Direct register access
#define GPIO0_BASE 0x50000000
#define GPIO_OUT_OFFSET 0x504
#define GPIO_OUTSET_OFFSET 0x508

void toggle_led(void)
{
    volatile uint32_t *gpio_out = (uint32_t *)(GPIO0_BASE + GPIO_OUT_OFFSET);
    *gpio_out ^= (1 << 13);  // Toggle pin 13
}
```

### Why It Fails

**Failure mode:** Not portable, breaks on different boards, may conflict with driver state, no power management integration

**Detailed explanation:**

Problems:
1. **Hardcoded addresses** work only on specific SoC (nRF52840 in this case)
2. **Pin numbers** are board-specific
3. **No power management** — device may be powered off
4. **No synchronization** with Zephyr's GPIO driver if both are used
5. **No devicetree integration** — can't change pins via DT overlay
6. **No runtime checks** — register access might fault if peripheral clock disabled

### GOOD Code Example

```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int init_led(void)
{
    if (!device_is_ready(led.port)) {
        return -ENODEV;
    }

    return gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
}

void toggle_led(void)
{
    gpio_pin_toggle_dt(&led);
}
```

**Benefits:**
- Portable across boards (pin defined in devicetree)
- Power management integration
- Safe (checks device ready state)
- Can be reconfigured via DT overlay without code changes

---

## Anti-Pattern 7: Priority Inversion Without k_mutex

### What Developers Do Wrong

Use k_sem as binary semaphore for mutual exclusion instead of k_mutex when priority inheritance is needed.

### BAD Code Example

```c
static K_SEM_DEFINE(data_sem, 1, 1);  // Binary semaphore
static int shared_data = 0;

// High-priority thread
void high_priority_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&data_sem, K_FOREVER);
        shared_data += 100;
        k_sem_give(&data_sem);
        k_msleep(10);
    }
}

// Low-priority thread
void low_priority_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&data_sem, K_FOREVER);
        // Long processing
        for (int i = 0; i < 1000000; i++) {
            shared_data++;
        }
        k_sem_give(&data_sem);
    }
}
```

### Why It Fails

**Failure mode:** Priority inversion — high-priority thread blocked by low-priority thread for extended time

**Detailed explanation:**

Scenario:
1. Low-priority thread acquires semaphore
2. Low-priority thread starts long processing
3. High-priority thread becomes ready, preempts low-priority thread
4. High-priority thread tries to acquire semaphore → blocked
5. **Problem:** Low-priority thread doesn't get boosted, so any medium-priority thread can preempt it
6. **Result:** High-priority thread blocked indefinitely while medium-priority threads run

With semaphore: No priority inheritance, low-priority thread keeps its low priority even though high-priority thread is waiting.

### GOOD Code Example

```c
static K_MUTEX_DEFINE(data_mutex);
static int shared_data = 0;

// High-priority thread
void high_priority_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_mutex_lock(&data_mutex, K_FOREVER);
        shared_data += 100;
        k_mutex_unlock(&data_mutex);
        k_msleep(10);
    }
}

// Low-priority thread
void low_priority_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_mutex_lock(&data_mutex, K_FOREVER);
        // When high-priority thread waits, THIS thread gets boosted to high priority
        for (int i = 0; i < 1000000; i++) {
            shared_data++;
        }
        k_mutex_unlock(&data_mutex);
    }
}
```

**Benefits:**
- Mutex implements priority inheritance
- When high-priority thread waits for mutex, holder gets temporarily boosted to high priority
- Medium-priority threads cannot preempt the boosted low-priority thread
- High-priority thread blocked for minimal time

---

## Anti-Pattern 8: Unbounded Stack Allocation

### What Developers Do Wrong

Use variable-length arrays (VLA) or large stack allocations that can overflow the thread stack.

### BAD Code Example

```c
void process_data(int size)
{
    uint8_t buffer[size];  // BAD: VLA, size unbounded

    // Fill buffer
    for (int i = 0; i < size; i++) {
        buffer[i] = i;
    }

    transmit(buffer, size);
}

void thread_entry(void *p1, void *p2, void *p3)
{
    int user_size = get_user_input();  // Could be anything
    process_data(user_size);  // Stack overflow if user_size is large
}
```

### Why It Fails

**Failure mode:** Stack overflow, memory corruption, crash

**Detailed explanation:**

Embedded systems have limited stack sizes (typically 1-4KB per thread). VLAs allocate on stack, and if `size` is large (e.g., 10000), the stack overflows:

1. Stack overflow overwrites adjacent memory
2. May corrupt other thread's stack
3. May corrupt kernel data structures
4. Results in undefined behavior, crashes, or security vulnerabilities

Zephyr stacks have guard pages (if MPU/MMU enabled), but overflow still causes crash.

### GOOD Code Example

**Option 1: Fixed maximum size**

```c
#define MAX_BUFFER_SIZE 256

int process_data(int size)
{
    if (size > MAX_BUFFER_SIZE) {
        return -EINVAL;
    }

    uint8_t buffer[MAX_BUFFER_SIZE];
    for (int i = 0; i < size; i++) {
        buffer[i] = i;
    }

    return transmit(buffer, size);
}
```

**Option 2: Heap allocation**

```c
int process_data(int size)
{
    if (size > 65536) {  // Sanity check
        return -EINVAL;
    }

    uint8_t *buffer = k_malloc(size);
    if (buffer == NULL) {
        return -ENOMEM;
    }

    for (int i = 0; i < size; i++) {
        buffer[i] = i;
    }

    int ret = transmit(buffer, size);
    k_free(buffer);

    return ret;
}
```

**Option 3: Memory slab (best for repeated fixed-size allocations)**

```c
struct buffer_block {
    uint8_t data[256];
};

K_MEM_SLAB_DEFINE(buffer_slab, sizeof(struct buffer_block), 4, 4);

int process_data(int size)
{
    if (size > sizeof(struct buffer_block)) {
        return -EINVAL;
    }

    struct buffer_block *block;
    if (k_mem_slab_alloc(&buffer_slab, (void **)&block, K_NO_WAIT) != 0) {
        return -ENOMEM;
    }

    for (int i = 0; i < size; i++) {
        block->data[i] = i;
    }

    int ret = transmit(block->data, size);
    k_mem_slab_free(&buffer_slab, (void *)block);

    return ret;
}
```

---

## Anti-Pattern 9: Polling Loops Instead of Event-Driven

### What Developers Do Wrong

Use busy-wait polling loops instead of blocking on synchronization primitives.

### BAD Code Example

```c
static volatile bool data_ready = false;

ISR_DIRECT_DECLARE(sensor_isr)
{
    read_sensor_data();
    data_ready = true;
    return 1;
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        while (!data_ready) {  // BAD: Busy-wait, wastes CPU
            // Spinning
        }
        data_ready = false;
        process_data();
    }
}
```

### Why It Fails

**Failure mode:** High CPU usage, prevents low-power modes, reduces battery life

**Detailed explanation:**

The polling loop runs continuously, keeping CPU at 100% even when no work is available:
1. Thread constantly checks `data_ready`
2. CPU cannot enter low-power sleep states
3. Battery drains quickly
4. Other threads get less CPU time

On battery-powered devices, this can reduce battery life from months to hours.

### GOOD Code Example

```c
static struct k_sem data_ready_sem;

ISR_DIRECT_DECLARE(sensor_isr)
{
    read_sensor_data();
    k_sem_give(&data_ready_sem);
    return 1;
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&data_ready_sem, K_FOREVER);  // Blocks, allows CPU to sleep
        process_data();
    }
}
```

**Benefits:**
- Thread blocks when no work available
- CPU enters low-power sleep
- Immediate wake when ISR signals
- Other threads get full CPU time

---

## Anti-Pattern 10: Incorrect Thread Priority (Inverted Understanding)

### What Developers Do Wrong

Assume higher priority number = higher priority (like POSIX), but Zephyr uses the opposite.

### BAD Code Example

```c
// Intent: High-priority sensor thread, low-priority logging thread
#define SENSOR_PRIORITY 10  // BAD: Actually LOW priority in Zephyr
#define LOG_PRIORITY 1      // BAD: Actually HIGH priority in Zephyr

k_thread_create(&sensor_thread, sensor_stack, SENSOR_STACK_SIZE,
                sensor_thread_entry, NULL, NULL, NULL,
                SENSOR_PRIORITY, 0, K_NO_WAIT);

k_thread_create(&log_thread, log_stack, LOG_STACK_SIZE,
                log_thread_entry, NULL, NULL, NULL,
                LOG_PRIORITY, 0, K_NO_WAIT);
```

### Why It Fails

**Failure mode:** Priority inversion, missed real-time deadlines, system instability

**Detailed explanation:**

In Zephyr, **lower number = higher priority**. The code above creates:
- Sensor thread with priority 10 (LOW priority)
- Log thread with priority 1 (HIGH priority)

Result: Logging preempts sensor readings, causing missed samples and incorrect system behavior.

### GOOD Code Example

```c
// Lower number = higher priority in Zephyr
#define SENSOR_PRIORITY 1   // High priority (runs first)
#define LOG_PRIORITY 10     // Low priority (runs when sensor idle)

k_thread_create(&sensor_thread, sensor_stack, SENSOR_STACK_SIZE,
                sensor_thread_entry, NULL, NULL, NULL,
                SENSOR_PRIORITY, 0, K_NO_WAIT);

k_thread_create(&log_thread, log_stack, LOG_STACK_SIZE,
                log_thread_entry, NULL, NULL, NULL,
                LOG_PRIORITY, 0, K_NO_WAIT);
```

**Priority guidelines:**
- Negative priorities: Cooperative threads (higher priority, never preempted by other cooperative threads)
- 0-7: High-priority preemptive threads (ISR-like responsiveness)
- 8-11: Medium-priority threads
- 12-15: Low-priority threads (background tasks, logging)

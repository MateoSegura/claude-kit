# Correctness Checklist

Complete specification of all Zephyr RTOS correctness patterns for code review and grading.

## Category 1: Kernel APIs (4 patterns)

### Pattern 1.1: k_msleep vs k_sleep

**What to check:** Use k_msleep() for delays, not k_sleep() for millisecond-level waits.

**Grep pattern:**
```bash
grep -rn "k_sleep(K_MSEC\|k_sleep(K_SECONDS" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** -2 points per occurrence

**Correct:**
```c
k_msleep(100);  // Sleep for 100 milliseconds
k_sleep(K_SECONDS(5));  // Sleep for 5 seconds (K_SECONDS is OK)
```

**Incorrect:**
```c
k_sleep(K_MSEC(100));  // Should use k_msleep(100)
k_sleep(K_MSEC(10));   // Non-idiomatic
```

**Rationale:** k_msleep() is more readable and the preferred API for millisecond sleeps.

---

### Pattern 1.2: k_yield() Usage

**What to check:** k_yield() should only be used when cooperative scheduling is appropriate.

**Grep pattern:**
```bash
grep -rn "k_yield()" --include="*.c"
```

**Severity:** Minor (context-dependent)

**Scoring impact:** Review usage context, -5 if used as busy-wait alternative

**Correct:**
```c
// Cooperative task yielding to other same-priority threads
while (!data_ready) {
    k_yield();
}
```

**Incorrect:**
```c
// Using k_yield() as a substitute for proper synchronization
while (!flag) {
    k_yield();  // BAD: Should use k_sem or k_msgq
}
```

**Rationale:** k_yield() is cooperative and doesn't guarantee the condition will change. Use proper synchronization primitives.

---

### Pattern 1.3: SYS_INIT() Ordering

**What to check:** SYS_INIT() priority levels must respect dependencies.

**Grep pattern:**
```bash
grep -rn "SYS_INIT" --include="*.c" -A 2
```

**Severity:** Major

**Scoring impact:** -10 if dependencies are violated

**Correct:**
```c
// Early init (hardware, drivers)
SYS_INIT(driver_init, PRE_KERNEL_1, 0);

// Later init (application, depends on drivers)
SYS_INIT(app_init, APPLICATION, 0);
```

**Incorrect:**
```c
// App init at PRE_KERNEL level but uses POST_KERNEL drivers
SYS_INIT(app_init, PRE_KERNEL_2, 0);  // BAD: Too early
```

**Rationale:** Init levels ensure correct ordering. PRE_KERNEL runs before threads, POST_KERNEL after.

**Init levels (in order):**
1. EARLY (very early, minimal hardware)
2. PRE_KERNEL_1 (core hardware init)
3. PRE_KERNEL_2 (device drivers)
4. POST_KERNEL (kernel services available)
5. APPLICATION (app-level init, threads can be created)

---

### Pattern 1.4: k_busy_wait() for Short Delays

**What to check:** k_busy_wait() used only for microsecond-level delays where sleeping is inappropriate.

**Grep pattern:**
```bash
grep -rn "k_busy_wait" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** -5 if used for >100μs delays

**Correct:**
```c
// Short hardware timing delay
gpio_set(pin, 1);
k_busy_wait(10);  // 10μs pulse width
gpio_set(pin, 0);
```

**Incorrect:**
```c
k_busy_wait(10000);  // 10ms busy-wait: BAD, use k_msleep(10)
```

**Rationale:** Busy-waiting wastes CPU. Use only for sub-millisecond delays where sleep overhead is too high.

---

## Category 2: Threading (5 patterns)

### Pattern 2.1: Thread Stack Definition

**What to check:** Thread stacks must be defined with K_THREAD_STACK_DEFINE() or K_KERNEL_STACK_DEFINE().

**Grep pattern:**
```bash
grep -rn "k_thread_create" --include="*.c" -B 5 | grep -E "K_THREAD_STACK_DEFINE|K_KERNEL_STACK_DEFINE"
```

**Severity:** Critical

**Scoring impact:** -15 if stack not properly defined

**Correct:**
```c
#define STACK_SIZE 1024
K_THREAD_STACK_DEFINE(my_thread_stack, STACK_SIZE);
struct k_thread my_thread_data;

k_tid_t tid = k_thread_create(&my_thread_data, my_thread_stack,
                               K_THREAD_STACK_SIZEOF(my_thread_stack),
                               thread_entry, NULL, NULL, NULL,
                               PRIORITY, 0, K_NO_WAIT);
```

**Incorrect:**
```c
char stack[1024];  // BAD: Not aligned, no MPU/MMU protection
k_thread_create(&thread_data, stack, sizeof(stack), ...);
```

**Rationale:** K_THREAD_STACK_DEFINE ensures proper alignment, size, and MPU/MMU protection.

---

### Pattern 2.2: Thread Priority Range

**What to check:** Thread priorities must be in range [-CONFIG_NUM_COOP_PRIORITIES, CONFIG_NUM_PREEMPT_PRIORITIES-1].

**Grep pattern:**
```bash
grep -rn "k_thread_create\|k_thread_priority_set" --include="*.c" -A 1
```

**Severity:** Major

**Scoring impact:** -10 if priority out of range

**Correct:**
```c
// Typical range: cooperative -1 to -16, preemptive 0 to 15
#define MY_PRIORITY 5  // Preemptive, mid-priority
k_thread_create(..., MY_PRIORITY, ...);
```

**Incorrect:**
```c
#define MY_PRIORITY 128  // BAD: Out of range
k_thread_create(..., MY_PRIORITY, ...);
```

**Rationale:** Invalid priorities cause runtime errors. Lower numbers = higher priority.

**Priority ranges (default config):**
- Cooperative: -1 to -16 (negative values, higher priority)
- Preemptive: 0 to 15 (positive values, lower priority)

---

### Pattern 2.3: Thread Termination

**What to check:** Threads should either run forever or properly exit with k_thread_abort() or return.

**Grep pattern:**
```bash
grep -rn "void.*thread_entry" --include="*.c" -A 20 | grep "return\|k_thread_abort"
```

**Severity:** Minor

**Scoring impact:** -3 if thread exits without cleanup

**Correct:**
```c
void thread_entry(void *p1, void *p2, void *p3) {
    while (1) {
        // Work
        k_msleep(100);
    }
    // Never reached
}

// Or for one-shot threads:
void oneshot_thread(void *p1, void *p2, void *p3) {
    do_work();
    return;  // Thread exits cleanly
}
```

**Incorrect:**
```c
void thread_entry(void *p1, void *p2, void *p3) {
    do_work();
    // BAD: Falls off end without return or infinite loop
}
```

---

### Pattern 2.4: Thread Join Usage

**What to check:** Use k_thread_join() to wait for thread completion if needed.

**Grep pattern:**
```bash
grep -rn "k_thread_join" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** Context-dependent, check if needed for correctness

**Correct:**
```c
k_tid_t tid = k_thread_create(...);
// Do other work
k_thread_join(tid, K_FOREVER);  // Wait for thread to complete
```

**Rationale:** Ensures thread has finished before accessing its results.

---

### Pattern 2.5: Thread Entry Function Signature

**What to check:** Thread entry functions must match: void (*)(void *, void *, void *)

**Grep pattern:**
```bash
grep -rn "k_thread_create" --include="*.c" -A 1
```

**Severity:** Major (causes compile error if wrong)

**Scoring impact:** Compile error prevents grading

**Correct:**
```c
void my_thread_entry(void *p1, void *p2, void *p3) {
    int arg = (int)p1;
    // ...
}

k_thread_create(&thread_data, stack, STACK_SIZE,
                my_thread_entry, (void *)42, NULL, NULL,
                PRIORITY, 0, K_NO_WAIT);
```

---

## Category 3: ISR Safety (4 patterns)

### Pattern 3.1: No Sleeping in ISR

**What to check:** ISRs must not call k_sleep, k_msleep, k_usleep, or any blocking function.

**Grep pattern:**
```bash
grep -rn "ISR_DIRECT_DECLARE\|ISR_DIRECT_PM" --include="*.c" -A 20 | grep -E "k_sleep|k_msleep|k_usleep|k_mutex_lock"
```

**Severity:** Critical

**Scoring impact:** -20, auto-fail

**Correct:**
```c
ISR_DIRECT_DECLARE(my_isr) {
    // Quick work only
    gpio_pin_toggle(dev, PIN);
    k_sem_give(&my_sem);  // Signal thread (non-blocking)
    return 1;
}
```

**Incorrect:**
```c
ISR_DIRECT_DECLARE(my_isr) {
    k_msleep(10);  // CRITICAL ERROR: Sleeping in ISR
    return 1;
}
```

**Rationale:** Sleeping in ISR crashes the system. ISRs must be fast and non-blocking.

---

### Pattern 3.2: No Mutex Locking in ISR

**What to check:** ISRs must not call k_mutex_lock() (mutexes can sleep).

**Grep pattern:**
```bash
grep -rn "ISR_DIRECT_DECLARE\|ISR_DIRECT_PM" --include="*.c" -A 20 | grep "k_mutex_lock"
```

**Severity:** Critical

**Scoring impact:** -20, auto-fail

**Correct:**
```c
ISR_DIRECT_DECLARE(my_isr) {
    k_sem_give(&my_sem);  // OK: k_sem_give is ISR-safe
    return 1;
}
```

**Incorrect:**
```c
ISR_DIRECT_DECLARE(my_isr) {
    k_mutex_lock(&my_mutex, K_FOREVER);  // CRITICAL ERROR
    // ...
    k_mutex_unlock(&my_mutex);
    return 1;
}
```

**Rationale:** Mutexes implement priority inheritance and can cause the ISR to block, crashing the system.

---

### Pattern 3.3: ISR Detection with k_is_in_isr()

**What to check:** Code that can run in both ISR and thread context should check k_is_in_isr().

**Grep pattern:**
```bash
grep -rn "k_is_in_isr()" --include="*.c"
```

**Severity:** Minor (best practice)

**Scoring impact:** +5 bonus if used correctly

**Correct:**
```c
void signal_event(void) {
    if (k_is_in_isr()) {
        k_sem_give(&event_sem);
    } else {
        k_sem_give(&event_sem);  // Same in this case, but could differ
    }
}
```

**Rationale:** Some APIs have different behavior in ISR vs thread context.

---

### Pattern 3.4: ISR-to-Thread Signaling

**What to check:** ISRs signal threads using k_sem_give(), k_msgq_put(), or k_poll_signal_raise().

**Grep pattern:**
```bash
grep -rn "ISR_DIRECT_DECLARE\|ISR_DIRECT_PM" --include="*.c" -A 20 | grep -E "k_sem_give|k_msgq_put|k_poll_signal_raise"
```

**Severity:** Major if missing when needed

**Scoring impact:** -10 if ISR doesn't signal thread when it should

**Correct:**
```c
static struct k_sem data_ready_sem;

ISR_DIRECT_DECLARE(uart_isr) {
    // Read data into buffer
    k_sem_give(&data_ready_sem);  // Signal thread
    return 1;
}

void processing_thread(void) {
    while (1) {
        k_sem_take(&data_ready_sem, K_FOREVER);
        process_data();
    }
}
```

**Rationale:** ISRs should do minimal work and defer processing to thread context.

---

## Category 4: Devicetree (6 patterns)

### Pattern 4.1: Device Access with device_is_ready()

**What to check:** All device pointers from DEVICE_DT_GET() must be checked with device_is_ready() before use.

**Grep pattern:**
```bash
grep -rn "DEVICE_DT_GET\|DEVICE_DT_GET_ONE" --include="*.c" -A 3 | grep "device_is_ready"
```

**Severity:** Critical

**Scoring impact:** -15 per missing check

**Correct:**
```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

if (!device_is_ready(dev)) {
    LOG_ERR("Device not ready");
    return -ENODEV;
}

// Use device
i2c_write(dev, ...);
```

**Incorrect:**
```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));
i2c_write(dev, ...);  // BAD: No ready check, crash if device not ready
```

**Rationale:** Device may not be initialized or available. Checking prevents null pointer dereferences.

---

### Pattern 4.2: DT_NODELABEL vs DT_ALIAS

**What to check:** Use DT_NODELABEL or DT_ALIAS instead of DT_PATH for better maintainability.

**Grep pattern:**
```bash
grep -rn "DT_PATH\|DT_NODELABEL\|DT_ALIAS" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** -3 if using DT_PATH unnecessarily

**Correct:**
```c
const struct device *i2c = DEVICE_DT_GET(DT_NODELABEL(i2c0));
const struct device *led = DEVICE_DT_GET(DT_ALIAS(led0));
```

**Incorrect:**
```c
const struct device *i2c = DEVICE_DT_GET(DT_PATH(/soc/i2c@40003000));  // BAD: Hard to maintain
```

**Rationale:** Labels and aliases are board-portable. Paths are fragile.

---

### Pattern 4.3: DT Macro Availability Check

**What to check:** Use DT_NODE_EXISTS() to check if devicetree node exists before using it.

**Grep pattern:**
```bash
grep -rn "DT_NODE_EXISTS\|#if DT_NODE_HAS_STATUS.*okay" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** +5 bonus if used for conditional compilation

**Correct:**
```c
#if DT_NODE_HAS_STATUS(DT_NODELABEL(i2c0), okay)
const struct device *i2c = DEVICE_DT_GET(DT_NODELABEL(i2c0));
#else
#warning "I2C0 not available in devicetree"
#endif
```

**Rationale:** Enables board-portable code that adapts to devicetree configuration.

---

### Pattern 4.4: GPIO DT Spec Initialization

**What to check:** GPIO devices should use GPIO_DT_SPEC_GET macros for initialization.

**Grep pattern:**
```bash
grep -rn "GPIO_DT_SPEC_GET\|gpio_dt_spec" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** +5 bonus if used

**Correct:**
```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int init(void) {
    if (!device_is_ready(led.port)) {
        return -ENODEV;
    }
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
    return 0;
}
```

**Rationale:** _dt helpers simplify devicetree-based GPIO configuration.

---

### Pattern 4.5: DT Property Access

**What to check:** Use DT_PROP() to access devicetree properties, not hardcoded values.

**Grep pattern:**
```bash
grep -rn "DT_PROP" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** +3 bonus if properties are used from DT

**Correct:**
```c
#define I2C_SPEED DT_PROP(DT_NODELABEL(i2c0), clock_frequency)

i2c_configure(dev, I2C_SPEED);
```

**Incorrect:**
```c
#define I2C_SPEED 100000  // BAD: Hardcoded, not from devicetree
```

---

### Pattern 4.6: Device Binding Macros

**What to check:** Device-specific bindings should use generated macros (e.g., DT_GPIO_LABEL, DT_SPI_DEV_CS_GPIOS_LABEL).

**Grep pattern:**
```bash
grep -rn "DT_.*_LABEL\|DT_.*_GPIOS" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** Informational, note in review

**Correct:**
```c
#define SPI_CS_GPIO_DEV DT_SPI_DEV_CS_GPIOS_LABEL(DT_NODELABEL(spi_device))
#define SPI_CS_GPIO_PIN DT_SPI_DEV_CS_GPIOS_PIN(DT_NODELABEL(spi_device))
```

---

## Category 5: Kconfig (3 patterns)

### Pattern 5.1: CONFIG_ Prefix

**What to check:** All Kconfig symbols must use CONFIG_ prefix when referenced in C code.

**Grep pattern:**
```bash
grep -rn "#ifdef\|#if defined" --include="*.c" | grep -v "CONFIG_"
```

**Severity:** Major (compile error if wrong)

**Scoring impact:** Compile error

**Correct:**
```c
#ifdef CONFIG_UART_CONSOLE
    console_init();
#endif
```

**Incorrect:**
```c
#ifdef UART_CONSOLE  // BAD: Missing CONFIG_ prefix
    console_init();
#endif
```

---

### Pattern 5.2: IS_ENABLED() for Bool Configs

**What to check:** Use IS_ENABLED(CONFIG_*) instead of #ifdef for bool Kconfigs in expressions.

**Grep pattern:**
```bash
grep -rn "IS_ENABLED" --include="*.c"
```

**Severity:** Minor (style)

**Scoring impact:** +3 bonus if used correctly

**Correct:**
```c
if (IS_ENABLED(CONFIG_DEBUG)) {
    print_debug_info();
}
```

**Better than:**
```c
#ifdef CONFIG_DEBUG
    print_debug_info();
#endif
```

**Rationale:** IS_ENABLED() keeps code in same compilation flow, enabling better compiler checks.

---

### Pattern 5.3: Kconfig Range Validation

**What to check:** Validate Kconfig values at runtime if they affect safety or correctness.

**Grep pattern:**
```bash
grep -rn "CONFIG_" --include="*.c" -A 3 | grep "if.*CONFIG_.*>"
```

**Severity:** Minor

**Scoring impact:** +5 bonus if validation present

**Correct:**
```c
#define PRIORITY CONFIG_MY_THREAD_PRIORITY
BUILD_ASSERT(PRIORITY >= 0 && PRIORITY < 16, "Invalid priority");
```

---

## Category 6: Synchronization (5 patterns)

### Pattern 6.1: Mutex vs Semaphore Choice

**What to check:** Use k_mutex for mutual exclusion (protecting shared data), k_sem for signaling.

**Grep pattern:**
```bash
grep -rn "k_mutex\|k_sem" --include="*.c"
```

**Severity:** Major if wrong primitive used

**Scoring impact:** -10 if semaphore used for mutual exclusion in complex case

**Correct:**
```c
// Mutex for mutual exclusion
static struct k_mutex data_mutex;
k_mutex_lock(&data_mutex, K_FOREVER);
shared_data++;
k_mutex_unlock(&data_mutex);

// Semaphore for signaling
static struct k_sem event_sem;
// ISR or producer
k_sem_give(&event_sem);
// Consumer thread
k_sem_take(&event_sem, K_FOREVER);
```

**Incorrect:**
```c
// Using semaphore for mutual exclusion (less safe for complex cases)
static struct k_sem data_sem;
K_SEM_DEFINE(data_sem, 1, 1);  // Binary semaphore
k_sem_take(&data_sem, K_FOREVER);
shared_data++;
k_sem_give(&data_sem);  // BAD: Should use mutex for priority inheritance
```

**Rationale:** Mutexes provide priority inheritance to prevent priority inversion. Semaphores don't.

---

### Pattern 6.2: Shared State Protection (ISR + Thread)

**What to check:** Global variables accessed by both ISR and threads must be protected.

**Grep pattern:**
```bash
# Look for globals modified in ISR
grep -rn "ISR_DIRECT_DECLARE" --include="*.c" -A 20 | grep "="
```

**Severity:** Critical

**Scoring impact:** -20, auto-fail

**Correct:**
```c
static atomic_t counter = ATOMIC_INIT(0);

ISR_DIRECT_DECLARE(my_isr) {
    atomic_inc(&counter);  // Atomic operation
    return 1;
}

void thread(void) {
    int val = atomic_get(&counter);
}
```

**Incorrect:**
```c
static int counter = 0;  // BAD: No protection

ISR_DIRECT_DECLARE(my_isr) {
    counter++;  // CRITICAL: Race condition
    return 1;
}

void thread(void) {
    if (counter > 10) {  // CRITICAL: Race condition
        // ...
    }
}
```

**Rationale:** Unprotected access causes race conditions and data corruption.

---

### Pattern 6.3: Message Queue Usage

**What to check:** Use k_msgq for passing data between threads/ISRs.

**Grep pattern:**
```bash
grep -rn "k_msgq" --include="*.c"
```

**Severity:** Minor (alternative to other methods)

**Scoring impact:** +5 bonus if used appropriately

**Correct:**
```c
struct data_item {
    uint32_t timestamp;
    uint16_t value;
};

K_MSGQ_DEFINE(data_msgq, sizeof(struct data_item), 10, 4);

// Producer
struct data_item item = {.timestamp = k_uptime_get_32(), .value = 42};
k_msgq_put(&data_msgq, &item, K_NO_WAIT);

// Consumer
struct data_item received;
k_msgq_get(&data_msgq, &received, K_FOREVER);
```

---

### Pattern 6.4: Atomic Operations

**What to check:** Use atomic_* operations for simple shared variables instead of mutexes when appropriate.

**Grep pattern:**
```bash
grep -rn "atomic_t\|atomic_" --include="*.c"
```

**Severity:** Minor (optimization)

**Scoring impact:** +5 bonus if used correctly

**Correct:**
```c
static atomic_t flag = ATOMIC_INIT(0);

// Set flag (thread-safe)
atomic_set(&flag, 1);

// Check flag (thread-safe)
if (atomic_get(&flag) == 1) {
    // ...
}
```

---

### Pattern 6.5: k_poll for Multi-Event Waiting

**What to check:** Use k_poll() to wait on multiple events instead of busy-polling.

**Grep pattern:**
```bash
grep -rn "k_poll\|K_POLL_EVENT" --include="*.c"
```

**Severity:** Minor (advanced feature)

**Scoring impact:** +10 bonus if used correctly

**Correct:**
```c
struct k_poll_event events[2] = {
    K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SEM_AVAILABLE, K_POLL_MODE_NOTIFY_ONLY, &sem1),
    K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_MSGQ_DATA_AVAILABLE, K_POLL_MODE_NOTIFY_ONLY, &msgq),
};

k_poll(events, 2, K_FOREVER);

if (events[0].state == K_POLL_STATE_SEM_AVAILABLE) {
    k_sem_take(&sem1, K_NO_WAIT);
}
if (events[1].state == K_POLL_STATE_MSGQ_DATA_AVAILABLE) {
    k_msgq_get(&msgq, &data, K_NO_WAIT);
}
```

---

## Category 7: Memory Management (3 patterns)

### Pattern 7.1: k_malloc vs k_heap_alloc

**What to check:** Use k_malloc() for simple allocation or k_heap_alloc() for custom heaps.

**Grep pattern:**
```bash
grep -rn "k_malloc\|k_heap_alloc" --include="*.c"
```

**Severity:** Minor

**Scoring impact:** -5 if k_malloc used when not enabled in config

**Correct:**
```c
#if CONFIG_HEAP_MEM_POOL_SIZE > 0
void *buffer = k_malloc(1024);
if (buffer == NULL) {
    return -ENOMEM;
}
// Use buffer
k_free(buffer);
#endif
```

---

### Pattern 7.2: Memory Slab Usage

**What to check:** Use k_mem_slab for fixed-size allocations (better performance, no fragmentation).

**Grep pattern:**
```bash
grep -rn "k_mem_slab\|K_MEM_SLAB_DEFINE" --include="*.c"
```

**Severity:** Minor (optimization)

**Scoring impact:** +5 bonus if used correctly

**Correct:**
```c
struct data_block {
    uint8_t data[256];
};

K_MEM_SLAB_DEFINE(data_slab, sizeof(struct data_block), 10, 4);

struct data_block *block;
if (k_mem_slab_alloc(&data_slab, (void **)&block, K_NO_WAIT) == 0) {
    // Use block
    k_mem_slab_free(&data_slab, (void *)block);
}
```

---

### Pattern 7.3: Avoid VLA and alloca()

**What to check:** No variable-length arrays or alloca() on stack (stack overflow risk).

**Grep pattern:**
```bash
grep -rn "alloca\|uint8_t.*\[.*\]" --include="*.c"
```

**Severity:** Major

**Scoring impact:** -15 per occurrence

**Correct:**
```c
#define MAX_SIZE 256
uint8_t buffer[MAX_SIZE];  // Fixed size
```

**Incorrect:**
```c
void process(int size) {
    uint8_t buffer[size];  // BAD: VLA, stack overflow risk
}
```

---

## Category 8: Error Handling (2 patterns)

### Pattern 8.1: Negative Errno Returns

**What to check:** Functions return negative errno values (-EINVAL, -ENOMEM, etc.), not positive.

**Grep pattern:**
```bash
grep -rn "return EINVAL\|return ENOMEM" --include="*.c" | grep -v "return -"
```

**Severity:** Major

**Scoring impact:** -10 per occurrence

**Correct:**
```c
int function(void) {
    if (error) {
        return -EINVAL;
    }
    return 0;  // Success
}
```

**Incorrect:**
```c
int function(void) {
    if (error) {
        return EINVAL;  // BAD: Should be negative
    }
    return 0;
}
```

---

### Pattern 8.2: Error Code Checking

**What to check:** Return values from Zephyr APIs are checked.

**Grep pattern:**
```bash
grep -rn "k_msgq_put\|k_sem_take\|device_init" --include="*.c"
```

**Severity:** Major if unchecked

**Scoring impact:** -5 per critical unchecked call

**Correct:**
```c
int ret = k_msgq_put(&msgq, &data, K_NO_WAIT);
if (ret != 0) {
    LOG_ERR("Failed to put message: %d", ret);
    return ret;
}
```

**Incorrect:**
```c
k_msgq_put(&msgq, &data, K_NO_WAIT);  // BAD: Unchecked, may fail
```

---

## Category 9: Power Management (2 patterns)

### Pattern 9.1: Device Power Management

**What to check:** Use pm_device_action_run() to control device power states.

**Grep pattern:**
```bash
grep -rn "pm_device_action_run\|PM_DEVICE" --include="*.c"
```

**Severity:** Minor (advanced feature)

**Scoring impact:** +5 bonus if used

**Correct:**
```c
#ifdef CONFIG_PM_DEVICE
int ret = pm_device_action_run(dev, PM_DEVICE_ACTION_SUSPEND);
if (ret != 0) {
    return ret;
}
#endif
```

---

### Pattern 9.2: System Power Management

**What to check:** No busy-wait loops preventing system sleep.

**Grep pattern:**
```bash
grep -rn "while.*{" --include="*.c" -A 5 | grep -v "k_sleep\|k_msleep"
```

**Severity:** Major if prevents sleep

**Scoring impact:** -10 if busy-wait loop found

**Correct:**
```c
while (1) {
    k_msgq_get(&msgq, &data, K_FOREVER);  // Blocks, allows sleep
    process(data);
}
```

**Incorrect:**
```c
while (1) {
    if (flag) {  // BAD: Busy-wait, prevents system sleep
        process();
    }
}
```

# Zephyr Concurrency Patterns

Idiomatic patterns for building robust concurrent embedded systems with Zephyr RTOS.

## Producer-Consumer with Message Queue

**Use case:** Sensor reading thread produces samples, processing thread consumes them.

```c
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(sensor_pipeline, LOG_LEVEL_INF);

struct sensor_sample {
    int32_t temperature;
    int32_t humidity;
    int64_t timestamp;
};

/* Message queue with 4-byte aligned buffer */
char __aligned(4) msgq_buffer[10 * sizeof(struct sensor_sample)];
struct k_msgq sample_queue;

K_THREAD_STACK_DEFINE(reader_stack, 2048);
K_THREAD_STACK_DEFINE(processor_stack, 2048);

struct k_thread reader_thread;
struct k_thread processor_thread;

void sensor_reader(void *p1, void *p2, void *p3)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));

    if (!device_is_ready(dev)) {
        LOG_ERR("Sensor not ready");
        return;
    }

    while (1) {
        struct sensor_sample sample;

        sensor_sample_fetch(dev);
        sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &temp_val);
        sensor_channel_get(dev, SENSOR_CHAN_HUMIDITY, &hum_val);

        sample.temperature = temp_val.val1;
        sample.humidity = hum_val.val1;
        sample.timestamp = k_uptime_get();

        /* Non-blocking put - drops sample if queue full */
        if (k_msgq_put(&sample_queue, &sample, K_NO_WAIT) != 0) {
            LOG_WRN("Queue full, dropping sample");
        }

        k_sleep(K_MSEC(100));
    }
}

void data_processor(void *p1, void *p2, void *p3)
{
    struct sensor_sample sample;

    while (1) {
        /* Blocking get - waits forever for data */
        k_msgq_get(&sample_queue, &sample, K_FOREVER);

        LOG_INF("T=%d C, H=%d%%, t=%lld ms",
                sample.temperature, sample.humidity, sample.timestamp);

        /* Process data... */
    }
}

void init_sensor_pipeline(void)
{
    k_msgq_init(&sample_queue, msgq_buffer, sizeof(struct sensor_sample), 10);

    k_thread_create(&reader_thread, reader_stack,
                    K_THREAD_STACK_SIZEOF(reader_stack),
                    sensor_reader, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(7), 0, K_NO_WAIT);

    k_thread_create(&processor_thread, processor_stack,
                    K_THREAD_STACK_SIZEOF(processor_stack),
                    data_processor, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(8), 0, K_NO_WAIT);
}
```

**Key points:**
- Message queue provides FIFO ordering and automatic synchronization
- Non-blocking put prevents sensor thread from blocking on full queue
- Blocking get puts processor thread to sleep when no data available
- Fixed-size messages enable zero-copy semantics

## Periodic Work with Delayable Work Queue

**Use case:** Run periodic tasks in thread context without dedicating a thread.

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);
static struct k_work_delayable blink_work;

void blink_handler(struct k_work *work)
{
    static bool state = false;

    gpio_pin_toggle_dt(&led);
    state = !state;

    /* Reschedule for next blink */
    k_work_schedule(&blink_work, K_MSEC(500));
}

void init_blinker(void)
{
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);

    k_work_init_delayable(&blink_work, blink_handler);
    k_work_schedule(&blink_work, K_MSEC(500));
}
```

**Key points:**
- Runs in system work queue thread context (not ISR)
- Self-rescheduling for periodic execution
- Lower overhead than dedicated thread
- Can access blocking APIs (unlike timers)

## ISR-Safe Signaling

**Use case:** ISR signals event to thread for deferred processing.

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

static struct k_sem button_sem;
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_NODELABEL(button0), gpios);
static struct gpio_callback button_cb_data;

void button_isr(const struct device *dev, struct gpio_callback *cb, gpio_port_pins_t pins)
{
    /* Called in ISR context - must be fast */
    k_sem_give(&button_sem);  /* ISR-safe */
}

void button_handler_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sem_take(&button_sem, K_FOREVER);

        /* Deferred processing in thread context */
        printk("Button pressed!\n");

        /* Can do blocking operations here */
        k_sleep(K_MSEC(50));  /* Debounce delay */
    }
}

K_THREAD_STACK_DEFINE(button_stack, 1024);
struct k_thread button_thread;

void init_button_handler(void)
{
    k_sem_init(&button_sem, 0, 1);

    gpio_pin_configure_dt(&button, GPIO_INPUT);
    gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_RISING);

    gpio_init_callback(&button_cb_data, button_isr, BIT(button.pin));
    gpio_add_callback(button.port, &button_cb_data);

    k_thread_create(&button_thread, button_stack,
                    K_THREAD_STACK_SIZEOF(button_stack),
                    button_handler_thread, NULL, NULL, NULL,
                    K_PRIO_PREEMPT(5), 0, K_NO_WAIT);
}
```

**Key points:**
- ISR does minimal work: only signals semaphore
- Thread context handles complex processing
- Semaphore limit of 1 prevents queue overflow
- Debouncing done in thread context where `k_sleep()` is allowed

## Work Queue Submission from ISR

**Use case:** Defer complex work from ISR to work queue.

```c
#include <zephyr/kernel.h>

static struct k_work data_ready_work;

void data_ready_isr(const struct device *dev)
{
    /* In ISR context - just submit work */
    k_work_submit(&data_ready_work);
}

void process_data(struct k_work *work)
{
    /* In system work queue thread context */
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));

    /* Can use blocking APIs */
    sensor_sample_fetch(dev);

    struct sensor_value val;
    sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val);

    printk("Temperature: %d.%06d\n", val.val1, val.val2);
}

void init_data_processing(void)
{
    k_work_init(&data_ready_work, process_data);

    /* Configure device to trigger interrupt when data ready */
    /* ... */
}
```

**Key points:**
- `k_work_submit()` is ISR-safe
- Work runs in system work queue thread (priority 0)
- Multiple submits while work executing are coalesced (work runs once)
- Use custom work queue if need specific priority

## Thread Pool Using Work Queue

**Use case:** Process multiple concurrent tasks with fixed thread pool.

```c
#include <zephyr/kernel.h>

K_THREAD_STACK_DEFINE(worker_stack, 4096);
static struct k_work_q worker_queue;

struct task_item {
    struct k_work work;
    int task_id;
    /* Additional task data */
};

void process_task(struct k_work *work)
{
    struct task_item *task = CONTAINER_OF(work, struct task_item, work);

    printk("Processing task %d in thread %p\n", task->task_id, k_current_get());

    /* Do work... */
    k_sleep(K_MSEC(100));

    printk("Task %d complete\n", task->task_id);

    k_free(task);
}

void submit_task(int task_id)
{
    struct task_item *task = k_malloc(sizeof(struct task_item));
    if (!task) {
        printk("Out of memory\n");
        return;
    }

    task->task_id = task_id;
    k_work_init(&task->work, process_task);
    k_work_submit_to_queue(&worker_queue, &task->work);
}

void init_worker_pool(void)
{
    k_work_queue_init(&worker_queue);
    k_work_queue_start(&worker_queue, worker_stack,
                       K_THREAD_STACK_SIZEOF(worker_stack),
                       K_PRIO_PREEMPT(5), NULL);
}
```

**Key points:**
- Single worker thread processes queued work items
- Work items are dynamically allocated and freed
- FIFO ordering of submitted work
- Can create multiple work queues for different priorities

## Timeout Pattern with k_poll

**Use case:** Wait on multiple events with timeout.

```c
#include <zephyr/kernel.h>

static struct k_sem sem1;
static struct k_sem sem2;
static struct k_poll_signal shutdown_signal;

void multi_event_waiter(void)
{
    struct k_poll_event events[] = {
        K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SEM_AVAILABLE, K_POLL_MODE_NOTIFY_ONLY, &sem1),
        K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SEM_AVAILABLE, K_POLL_MODE_NOTIFY_ONLY, &sem2),
        K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SIGNAL, K_POLL_MODE_NOTIFY_ONLY, &shutdown_signal),
    };

    while (1) {
        int ret = k_poll(events, ARRAY_SIZE(events), K_MSEC(1000));

        if (ret == 0) {
            /* At least one event ready */
            if (events[0].state == K_POLL_STATE_SEM_AVAILABLE) {
                k_sem_take(&sem1, K_NO_WAIT);
                printk("Event 1 triggered\n");
                events[0].state = K_POLL_STATE_NOT_READY;
            }

            if (events[1].state == K_POLL_STATE_SEM_AVAILABLE) {
                k_sem_take(&sem2, K_NO_WAIT);
                printk("Event 2 triggered\n");
                events[1].state = K_POLL_STATE_NOT_READY;
            }

            if (events[2].state == K_POLL_STATE_SIGNALED) {
                printk("Shutdown signal received\n");
                break;
            }
        } else if (ret == -EAGAIN) {
            /* Timeout - do periodic work */
            printk("Timeout - still waiting\n");
        }
    }
}

void init_polling(void)
{
    k_sem_init(&sem1, 0, 1);
    k_sem_init(&sem2, 0, 1);
    k_poll_signal_init(&shutdown_signal);
}

void trigger_shutdown(void)
{
    k_poll_signal_raise(&shutdown_signal, 0);
}
```

**Key points:**
- Single thread waits on multiple event sources
- Timeout allows periodic processing
- Events must be reset to `K_POLL_STATE_NOT_READY` after handling
- More efficient than multiple threads with blocking waits

## Memory-Safe Buffer Passing with Memory Slab

**Use case:** Fixed-size buffer pool for zero-copy data passing.

```c
#include <zephyr/kernel.h>

#define BUFFER_SIZE 128
#define NUM_BUFFERS 8

K_MEM_SLAB_DEFINE(buffer_pool, BUFFER_SIZE, NUM_BUFFERS, 4);

struct data_buffer {
    uint8_t data[BUFFER_SIZE];
    size_t length;
};

struct k_msgq buffer_queue;
char __aligned(4) queue_buffer[NUM_BUFFERS * sizeof(struct data_buffer *)];

void producer_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        struct data_buffer *buf;

        /* Allocate buffer from pool */
        if (k_mem_slab_alloc(&buffer_pool, (void **)&buf, K_MSEC(100)) != 0) {
            printk("No buffers available\n");
            continue;
        }

        /* Fill buffer with data */
        buf->length = read_sensor_data(buf->data, BUFFER_SIZE);

        /* Pass pointer to consumer (zero-copy) */
        if (k_msgq_put(&buffer_queue, &buf, K_NO_WAIT) != 0) {
            printk("Queue full\n");
            k_mem_slab_free(&buffer_pool, buf);
        }

        k_sleep(K_MSEC(50));
    }
}

void consumer_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        struct data_buffer *buf;

        /* Receive buffer pointer */
        k_msgq_get(&buffer_queue, &buf, K_FOREVER);

        /* Process data */
        process_data(buf->data, buf->length);

        /* Return buffer to pool */
        k_mem_slab_free(&buffer_pool, buf);
    }
}

void init_buffer_passing(void)
{
    k_msgq_init(&buffer_queue, queue_buffer, sizeof(struct data_buffer *), NUM_BUFFERS);

    /* Create producer and consumer threads... */
}
```

**Key points:**
- Memory slab provides bounded allocation time (real-time friendly)
- Fixed-size blocks prevent fragmentation
- Message queue passes pointers (zero-copy)
- Producer allocates, consumer frees (clear ownership)
- Bounded pool size prevents memory exhaustion

## Mutex with Priority Inheritance

**Use case:** Protect shared resource from priority inversion.

```c
#include <zephyr/kernel.h>

static struct k_mutex sensor_mutex;
static const struct device *shared_sensor;

void low_priority_task(void *p1, void *p2, void *p3)
{
    while (1) {
        k_mutex_lock(&sensor_mutex, K_FOREVER);

        /* Slow operation on shared sensor */
        sensor_sample_fetch(shared_sensor);
        k_sleep(K_MSEC(100));  /* Simulate slow processing */

        k_mutex_unlock(&sensor_mutex);

        k_sleep(K_MSEC(500));
    }
}

void high_priority_task(void *p1, void *p2, void *p3)
{
    while (1) {
        k_sleep(K_MSEC(200));

        /* High-priority thread needs sensor */
        k_mutex_lock(&sensor_mutex, K_FOREVER);

        /* Low-priority thread temporarily inherits high priority */
        sensor_sample_fetch(shared_sensor);

        k_mutex_unlock(&sensor_mutex);
    }
}

void init_priority_inheritance(void)
{
    k_mutex_init(&sensor_mutex);

    shared_sensor = DEVICE_DT_GET(DT_NODELABEL(sensor));

    /* Create threads with different priorities... */
}
```

**Key points:**
- Mutex automatically implements priority inheritance
- Low-priority holder inherits priority of highest waiter
- Prevents unbounded priority inversion
- Always use mutex for shared resources accessed by different priority threads

## Cooperative Thread Yielding

**Use case:** Fair scheduling among equal-priority cooperative threads.

```c
#include <zephyr/kernel.h>

void cooperative_worker(void *p1, void *p2, void *p3)
{
    int worker_id = (int)p1;

    while (1) {
        printk("Worker %d: processing\n", worker_id);

        /* Do some work */
        for (int i = 0; i < 1000; i++) {
            /* ... */
        }

        /* Yield to other cooperative threads at same priority */
        k_yield();

        /* Will resume here when scheduled again */
        printk("Worker %d: resumed\n", worker_id);
    }
}

void init_cooperative_pool(void)
{
    for (int i = 0; i < 4; i++) {
        K_THREAD_STACK_DEFINE(stack, 1024);
        struct k_thread thread;

        k_thread_create(&thread, stack, K_THREAD_STACK_SIZEOF(stack),
                        cooperative_worker, (void *)i, NULL, NULL,
                        K_PRIO_COOP(5), 0, K_NO_WAIT);
    }
}
```

**Key points:**
- Cooperative threads (priority < 0) are never preempted
- Must explicitly yield to allow other threads to run
- Round-robin among equal-priority cooperative threads after yield
- Preemptible threads can preempt cooperative threads

## Condition Variable for State Changes

**Use case:** Wait for condition to become true.

```c
#include <zephyr/kernel.h>

static struct k_mutex state_mutex;
static struct k_condvar state_changed;
static int system_state = 0;

void state_monitor(void *p1, void *p2, void *p3)
{
    int target_state = (int)p1;

    k_mutex_lock(&state_mutex, K_FOREVER);

    while (system_state != target_state) {
        /* Atomically unlock mutex and wait */
        k_condvar_wait(&state_changed, &state_mutex, K_FOREVER);
        /* Mutex reacquired when returning */
    }

    printk("System reached state %d\n", target_state);

    k_mutex_unlock(&state_mutex);
}

void update_state(int new_state)
{
    k_mutex_lock(&state_mutex, K_FOREVER);

    system_state = new_state;

    /* Wake all waiters */
    k_condvar_broadcast(&state_changed);

    k_mutex_unlock(&state_mutex);
}

void init_state_machine(void)
{
    k_mutex_init(&state_mutex);
    k_condvar_init(&state_changed);
}
```

**Key points:**
- Condition variable avoids busy-waiting
- Always use with associated mutex
- `wait` atomically unlocks mutex and blocks
- `broadcast` wakes all waiters, `signal` wakes one
- Waiter must recheck condition after waking (spurious wakeups possible)

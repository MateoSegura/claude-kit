# Zephyr Design Patterns — Complete Reference

Detailed reference with compilable code examples for each design pattern. Every pattern follows the plugin's non-negotiables: runtime initialization, HAL APIs only, structured logging, private heaps, errno returns, C17 only.

## Subsystem Module Pattern

**Problem:** How to structure a self-contained module with clean API boundaries, explicit dependencies, and lifecycle management.

**Solution:** Public header with typed API, private implementation file, runtime initialization creating all OS primitives, clean shutdown.

### Complete Example: Sensor Manager Subsystem

**Public API (`sensor_manager.h`):**

```c
#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <zephyr/kernel.h>
#include <stdint.h>

/**
 * @brief Sensor reading data structure
 */
struct sensor_reading {
    int32_t temperature;  /* Celsius * 100 */
    int32_t humidity;     /* Percent * 100 */
    int64_t timestamp;    /* k_uptime_get() */
};

/**
 * @brief Initialize sensor manager subsystem
 *
 * Creates polling thread, initializes sensor hardware, allocates resources.
 * Must be called before any other sensor_manager_* functions.
 *
 * @retval 0 Success
 * @retval -ENODEV Sensor hardware not available
 * @retval -ENOMEM Insufficient memory for initialization
 */
int sensor_manager_init(void);

/**
 * @brief Get most recent sensor reading
 *
 * @param reading Output buffer for sensor data
 * @param timeout Maximum time to wait for fresh reading
 *
 * @retval 0 Success, reading populated
 * @retval -EAGAIN Timeout expired, no fresh data
 * @retval -EINVAL NULL reading pointer
 */
int sensor_manager_get_reading(struct sensor_reading *reading, k_timeout_t timeout);

/**
 * @brief Shutdown sensor manager and release resources
 *
 * Stops polling thread, releases memory, disables sensor hardware.
 *
 * @retval 0 Success
 */
int sensor_manager_shutdown(void);

#endif /* SENSOR_MANAGER_H */
```

**Private Implementation (`sensor_manager.c`):**

```c
#include "sensor_manager.h"
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(sensor_manager, LOG_LEVEL_INF);

/* All state is private (static) */
static K_THREAD_STACK_DEFINE(sensor_thread_stack, 2048);
static struct k_thread sensor_thread;
static struct k_msgq reading_queue;
static char __aligned(4) queue_buffer[5 * sizeof(struct sensor_reading)];
static bool initialized = false;
static bool shutdown_requested = false;

/* Sensor device reference */
static const struct device *sensor_dev;

/**
 * @brief Sensor polling thread (private)
 */
static void sensor_thread_entry(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    struct sensor_value temp_val, hum_val;
    struct sensor_reading reading;

    LOG_INF("Sensor polling thread started");

    while (!shutdown_requested) {
        int ret = sensor_sample_fetch(sensor_dev);
        if (ret < 0) {
            LOG_ERR("Sensor fetch failed: %d", ret);
            k_sleep(K_SECONDS(1));
            continue;
        }

        sensor_channel_get(sensor_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp_val);
        sensor_channel_get(sensor_dev, SENSOR_CHAN_HUMIDITY, &hum_val);

        reading.temperature = temp_val.val1 * 100 + temp_val.val2 / 10000;
        reading.humidity = hum_val.val1 * 100 + hum_val.val2 / 10000;
        reading.timestamp = k_uptime_get();

        /* Non-blocking put — drops oldest if queue full */
        ret = k_msgq_put(&reading_queue, &reading, K_NO_WAIT);
        if (ret != 0) {
            LOG_WRN("Reading queue full, dropping oldest sample");
            k_msgq_purge(&reading_queue);
            k_msgq_put(&reading_queue, &reading, K_NO_WAIT);
        }

        k_sleep(K_MSEC(500));  /* Poll rate: 2 Hz */
    }

    LOG_INF("Sensor polling thread stopped");
}

int sensor_manager_init(void)
{
    if (initialized) {
        LOG_WRN("Sensor manager already initialized");
        return 0;
    }

    /* Obtain sensor device from devicetree */
    sensor_dev = DEVICE_DT_GET(DT_NODELABEL(bme280));
    if (!device_is_ready(sensor_dev)) {
        LOG_ERR("Sensor device not ready");
        return -ENODEV;
    }

    /* Runtime initialization of message queue */
    k_msgq_init(&reading_queue, queue_buffer,
                sizeof(struct sensor_reading), 5);

    /* Runtime thread creation */
    k_tid_t tid = k_thread_create(
        &sensor_thread,
        sensor_thread_stack,
        K_THREAD_STACK_SIZEOF(sensor_thread_stack),
        sensor_thread_entry,
        NULL, NULL, NULL,
        K_PRIO_PREEMPT(7),
        0,
        K_NO_WAIT
    );

    if (!tid) {
        LOG_ERR("Failed to create sensor thread");
        return -ENOMEM;
    }

    k_thread_name_set(tid, "sensor_poll");

    initialized = true;
    shutdown_requested = false;

    LOG_INF("Sensor manager initialized successfully");
    return 0;
}

int sensor_manager_get_reading(struct sensor_reading *reading, k_timeout_t timeout)
{
    if (!initialized) {
        LOG_ERR("Sensor manager not initialized");
        return -EINVAL;
    }

    if (reading == NULL) {
        LOG_ERR("NULL reading pointer");
        return -EINVAL;
    }

    int ret = k_msgq_get(&reading_queue, reading, timeout);
    if (ret != 0) {
        LOG_DBG("No sensor reading available (timeout)");
        return -EAGAIN;
    }

    return 0;
}

int sensor_manager_shutdown(void)
{
    if (!initialized) {
        return 0;
    }

    LOG_INF("Shutting down sensor manager");

    shutdown_requested = true;

    /* Wait for thread to finish */
    k_thread_join(&sensor_thread, K_SECONDS(2));

    /* Clean up queue */
    k_msgq_purge(&reading_queue);

    initialized = false;

    LOG_INF("Sensor manager shutdown complete");
    return 0;
}
```

**Key Design Decisions:**

1. **All state is private:** No global variables exposed, only functions in header
2. **Runtime initialization:** `k_msgq_init()` and `k_thread_create()`, not static macros
3. **Explicit lifecycle:** `init()` before use, `shutdown()` to clean up
4. **Error propagation:** Every function returns errno, logs failures
5. **Structured logging:** `LOG_MODULE_REGISTER` at top, `LOG_*` throughout
6. **Devicetree-based hardware:** `DEVICE_DT_GET(DT_NODELABEL(...))`, no hardcoded addresses
7. **Overflow handling:** Queue full purges old data rather than blocking producer

**When to use:**
- Any subsystem that manages hardware, threads, or resources
- When you need clear ownership and lifecycle boundaries
- When testing requires module-level isolation

**When NOT to use:**
- For simple utility functions (no state, no threads) — just a `.c/.h` pair suffices
- For tightly coupled components that share significant internal state

---

## Hierarchical State Machine

**Problem:** Complex state management with nested states, entry/exit actions, guard conditions.

**Solution:** Struct-based states with function pointers for enter/exit/event handlers, k_msgq-driven event dispatch, explicit state transitions with logging.

### Complete Example: BLE Connection Lifecycle

```c
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(connection_sm, LOG_LEVEL_INF);

/* Forward declarations */
struct state;

/* Event types */
enum event_type {
    EVENT_CONNECT_REQUEST,
    EVENT_CONNECTION_ESTABLISHED,
    EVENT_PAIRING_REQUEST,
    EVENT_PAIRING_COMPLETE,
    EVENT_DISCONNECT_REQUEST,
    EVENT_CONNECTION_LOST,
};

struct event {
    enum event_type type;
    void *data;  /* Event-specific payload */
};

/* State function pointers */
typedef void (*state_entry_fn)(struct state *state);
typedef void (*state_exit_fn)(struct state *state);
typedef void (*state_event_fn)(struct state *state, const struct event *event);

/* State definition */
struct state {
    const char *name;
    state_entry_fn on_entry;
    state_exit_fn on_exit;
    state_event_fn on_event;
    struct state *parent;  /* For hierarchical states */
};

/* State machine context */
struct state_machine {
    struct state *current_state;
    struct k_msgq event_queue;
    char __aligned(4) queue_buffer[10 * sizeof(struct event)];
};

static struct state_machine sm;

/* Forward declare states */
static struct state state_idle;
static struct state state_connecting;
static struct state state_connected;
static struct state state_connected_unpaired;
static struct state state_connected_paired;
static struct state state_disconnecting;

/* Transition helper */
static void transition_to(struct state *new_state)
{
    if (sm.current_state && sm.current_state->on_exit) {
        sm.current_state->on_exit(sm.current_state);
    }

    LOG_INF("State transition: %s -> %s",
            sm.current_state ? sm.current_state->name : "NONE",
            new_state->name);

    sm.current_state = new_state;

    if (new_state->on_entry) {
        new_state->on_entry(new_state);
    }
}

/* ===== State: IDLE ===== */
static void idle_on_entry(struct state *state)
{
    LOG_DBG("Entered IDLE state");
    /* Stop advertising, disable radio */
}

static void idle_on_event(struct state *state, const struct event *event)
{
    if (event->type == EVENT_CONNECT_REQUEST) {
        LOG_INF("Connect request received");
        transition_to(&state_connecting);
    }
}

static struct state state_idle = {
    .name = "IDLE",
    .on_entry = idle_on_entry,
    .on_exit = NULL,
    .on_event = idle_on_event,
    .parent = NULL,
};

/* ===== State: CONNECTING ===== */
static void connecting_on_entry(struct state *state)
{
    LOG_DBG("Entered CONNECTING state");
    /* Start BLE connection procedure */
}

static void connecting_on_exit(struct state *state)
{
    /* Stop connection timeout timer */
}

static void connecting_on_event(struct state *state, const struct event *event)
{
    switch (event->type) {
    case EVENT_CONNECTION_ESTABLISHED:
        LOG_INF("Connection established");
        transition_to(&state_connected_unpaired);
        break;

    case EVENT_CONNECTION_LOST:
        LOG_WRN("Connection failed during establishment");
        transition_to(&state_idle);
        break;

    default:
        LOG_DBG("Ignoring event %d in CONNECTING state", event->type);
        break;
    }
}

static struct state state_connecting = {
    .name = "CONNECTING",
    .on_entry = connecting_on_entry,
    .on_exit = connecting_on_exit,
    .on_event = connecting_on_event,
    .parent = NULL,
};

/* ===== State: CONNECTED (parent state) ===== */
static void connected_on_entry(struct state *state)
{
    LOG_DBG("Entered CONNECTED parent state");
    /* Enable connection monitoring */
}

static void connected_on_exit(struct state *state)
{
    LOG_DBG("Exiting CONNECTED parent state");
    /* Disable connection monitoring */
}

static void connected_on_event(struct state *state, const struct event *event)
{
    /* Parent handler for events common to all connected substates */
    if (event->type == EVENT_DISCONNECT_REQUEST ||
        event->type == EVENT_CONNECTION_LOST) {
        LOG_INF("Disconnecting");
        transition_to(&state_disconnecting);
    }
}

static struct state state_connected = {
    .name = "CONNECTED",
    .on_entry = connected_on_entry,
    .on_exit = connected_on_exit,
    .on_event = connected_on_event,
    .parent = NULL,
};

/* ===== State: CONNECTED_UNPAIRED (child of CONNECTED) ===== */
static void connected_unpaired_on_entry(struct state *state)
{
    LOG_DBG("Entered CONNECTED_UNPAIRED state");
    /* Enter parent state first */
    if (state->parent && state->parent->on_entry) {
        state->parent->on_entry(state->parent);
    }
}

static void connected_unpaired_on_exit(struct state *state)
{
    /* Exit parent state */
    if (state->parent && state->parent->on_exit) {
        state->parent->on_exit(state->parent);
    }
}

static void connected_unpaired_on_event(struct state *state, const struct event *event)
{
    if (event->type == EVENT_PAIRING_REQUEST) {
        LOG_INF("Pairing started");
        /* Start pairing, wait for completion */
    } else if (event->type == EVENT_PAIRING_COMPLETE) {
        LOG_INF("Pairing complete");
        transition_to(&state_connected_paired);
    } else {
        /* Delegate to parent */
        if (state->parent && state->parent->on_event) {
            state->parent->on_event(state->parent, event);
        }
    }
}

static struct state state_connected_unpaired = {
    .name = "CONNECTED_UNPAIRED",
    .on_entry = connected_unpaired_on_entry,
    .on_exit = connected_unpaired_on_exit,
    .on_event = connected_unpaired_on_event,
    .parent = &state_connected,
};

/* ===== State: CONNECTED_PAIRED (child of CONNECTED) ===== */
static void connected_paired_on_entry(struct state *state)
{
    LOG_DBG("Entered CONNECTED_PAIRED state");
    if (state->parent && state->parent->on_entry) {
        state->parent->on_entry(state->parent);
    }
    /* Enable encrypted data transfer */
}

static void connected_paired_on_exit(struct state *state)
{
    if (state->parent && state->parent->on_exit) {
        state->parent->on_exit(state->parent);
    }
}

static void connected_paired_on_event(struct state *state, const struct event *event)
{
    /* All events delegated to parent */
    if (state->parent && state->parent->on_event) {
        state->parent->on_event(state->parent, event);
    }
}

static struct state state_connected_paired = {
    .name = "CONNECTED_PAIRED",
    .on_entry = connected_paired_on_entry,
    .on_exit = connected_paired_on_exit,
    .on_event = connected_paired_on_event,
    .parent = &state_connected,
};

/* ===== State: DISCONNECTING ===== */
static void disconnecting_on_entry(struct state *state)
{
    LOG_DBG("Entered DISCONNECTING state");
    /* Send disconnect command to BLE stack */
}

static void disconnecting_on_event(struct state *state, const struct event *event)
{
    if (event->type == EVENT_CONNECTION_LOST) {
        LOG_INF("Disconnection complete");
        transition_to(&state_idle);
    }
}

static struct state state_disconnecting = {
    .name = "DISCONNECTING",
    .on_entry = disconnecting_on_entry,
    .on_exit = NULL,
    .on_event = disconnecting_on_event,
    .parent = NULL,
};

/* State machine runner thread */
static void state_machine_thread(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    struct event event;

    while (1) {
        k_msgq_get(&sm.event_queue, &event, K_FOREVER);

        LOG_DBG("Processing event %d in state %s",
                event.type, sm.current_state->name);

        if (sm.current_state && sm.current_state->on_event) {
            sm.current_state->on_event(sm.current_state, &event);
        }
    }
}

/* Public API to post events */
void connection_sm_post_event(enum event_type type, void *data)
{
    struct event event = {
        .type = type,
        .data = data,
    };

    int ret = k_msgq_put(&sm.event_queue, &event, K_NO_WAIT);
    if (ret != 0) {
        LOG_ERR("Event queue full, dropping event %d", type);
    }
}

/* Initialization */
static K_THREAD_STACK_DEFINE(sm_thread_stack, 2048);
static struct k_thread sm_thread;

int connection_sm_init(void)
{
    /* Runtime init of message queue */
    k_msgq_init(&sm.event_queue, sm.queue_buffer,
                sizeof(struct event), 10);

    /* Start in IDLE state */
    sm.current_state = NULL;
    transition_to(&state_idle);

    /* Create state machine thread */
    k_tid_t tid = k_thread_create(
        &sm_thread, sm_thread_stack,
        K_THREAD_STACK_SIZEOF(sm_thread_stack),
        state_machine_thread,
        NULL, NULL, NULL,
        K_PRIO_PREEMPT(5), 0, K_NO_WAIT
    );

    if (!tid) {
        LOG_ERR("Failed to create state machine thread");
        return -ENOMEM;
    }

    k_thread_name_set(tid, "conn_sm");

    LOG_INF("Connection state machine initialized");
    return 0;
}
```

**Key Design Decisions:**

1. **Struct-based states:** Each state is a struct with function pointers
2. **Hierarchical support:** Child states delegate to parent via `.parent` pointer
3. **Event-driven:** Events arrive via message queue, processed sequentially
4. **Entry/exit actions:** Explicit lifecycle hooks for state-specific setup/teardown
5. **Transition logging:** Every transition logged with old and new state names
6. **Single-threaded:** State machine runs in dedicated thread, no concurrency within state logic

**When to use:**
- Complex state management (connection lifecycle, protocol handlers, device modes)
- When entry/exit actions are needed
- When hierarchical states reduce duplication

**When NOT to use:**
- Simple binary states (use a bool flag)
- High-frequency state changes (function call overhead matters)

---

## Event-Driven Architecture

**Problem:** Decouple producers from consumers, enable fan-out, avoid tight coupling.

**Solution:** Central event dispatcher with typed events, subscriber registration, message queue delivery.

### Complete Example: Sensor Event Distribution

```c
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(event_dispatcher, LOG_LEVEL_INF);

/* Event types */
enum event_type {
    EVENT_SENSOR_TEMP,
    EVENT_SENSOR_HUMIDITY,
    EVENT_SENSOR_PRESSURE,
    EVENT_BATTERY_LOW,
    EVENT_BUTTON_PRESS,
};

/* Discriminated union for event payload */
struct event {
    enum event_type type;
    int64_t timestamp;

    union {
        struct {
            int32_t value;  /* Temperature in Celsius * 100 */
        } temp;

        struct {
            int32_t value;  /* Humidity in percent * 100 */
        } humidity;

        struct {
            int32_t value;  /* Pressure in hPa * 100 */
        } pressure;

        struct {
            uint16_t voltage_mv;  /* Battery voltage in millivolts */
        } battery;

        struct {
            uint8_t button_id;
        } button;
    } payload;
};

/* Subscriber callback type */
typedef void (*event_subscriber_fn)(const struct event *event);

/* Subscriber registry */
#define MAX_SUBSCRIBERS 8

struct subscriber {
    event_subscriber_fn callback;
    uint32_t event_mask;  /* Bitmask of subscribed event types */
};

static struct subscriber subscribers[MAX_SUBSCRIBERS];
static int num_subscribers = 0;
static struct k_mutex subscriber_mutex;

/* Event queue */
static struct k_msgq event_queue;
static char __aligned(4) queue_buffer[20 * sizeof(struct event)];

/**
 * @brief Register event subscriber
 *
 * @param callback Function to call on matching events
 * @param event_mask Bitmask of event types to receive (1 << EVENT_SENSOR_TEMP, etc.)
 *
 * @retval 0 Success
 * @retval -ENOMEM Subscriber registry full
 */
int event_subscribe(event_subscriber_fn callback, uint32_t event_mask)
{
    k_mutex_lock(&subscriber_mutex, K_FOREVER);

    if (num_subscribers >= MAX_SUBSCRIBERS) {
        k_mutex_unlock(&subscriber_mutex);
        LOG_ERR("Subscriber registry full");
        return -ENOMEM;
    }

    subscribers[num_subscribers].callback = callback;
    subscribers[num_subscribers].event_mask = event_mask;
    num_subscribers++;

    k_mutex_unlock(&subscriber_mutex);

    LOG_INF("Registered subscriber %d with mask 0x%08x", num_subscribers - 1, event_mask);
    return 0;
}

/**
 * @brief Publish event to all subscribers
 *
 * @param event Event to publish
 *
 * @retval 0 Success
 * @retval -EAGAIN Event queue full
 */
int event_publish(const struct event *event)
{
    if (event == NULL) {
        return -EINVAL;
    }

    int ret = k_msgq_put(&event_queue, event, K_NO_WAIT);
    if (ret != 0) {
        LOG_WRN("Event queue full, dropping event type %d", event->type);
        return -EAGAIN;
    }

    return 0;
}

/* Event dispatcher thread */
static void event_dispatcher_thread(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    struct event event;

    while (1) {
        k_msgq_get(&event_queue, &event, K_FOREVER);

        uint32_t event_bit = (1 << event.type);

        LOG_DBG("Dispatching event type %d to subscribers", event.type);

        k_mutex_lock(&subscriber_mutex, K_FOREVER);

        int delivered = 0;
        for (int i = 0; i < num_subscribers; i++) {
            if (subscribers[i].event_mask & event_bit) {
                subscribers[i].callback(&event);
                delivered++;
            }
        }

        k_mutex_unlock(&subscriber_mutex);

        LOG_DBG("Event type %d delivered to %d subscribers", event.type, delivered);
    }
}

/* Example subscribers */
static void display_subscriber(const struct event *event)
{
    switch (event->type) {
    case EVENT_SENSOR_TEMP:
        LOG_INF("Display: Temperature %d.%02d C",
                event->payload.temp.value / 100,
                event->payload.temp.value % 100);
        /* Update display widget */
        break;

    case EVENT_SENSOR_HUMIDITY:
        LOG_INF("Display: Humidity %d.%02d %%",
                event->payload.humidity.value / 100,
                event->payload.humidity.value % 100);
        break;

    default:
        break;
    }
}

static void storage_subscriber(const struct event *event)
{
    /* Log all sensor events to flash */
    switch (event->type) {
    case EVENT_SENSOR_TEMP:
    case EVENT_SENSOR_HUMIDITY:
    case EVENT_SENSOR_PRESSURE:
        LOG_INF("Storage: Writing sensor event type %d to flash", event->type);
        /* Append to flash log */
        break;

    default:
        break;
    }
}

static void network_subscriber(const struct event *event)
{
    /* Forward temperature and battery events to cloud */
    if (event->type == EVENT_SENSOR_TEMP || event->type == EVENT_BATTERY_LOW) {
        LOG_INF("Network: Queueing event type %d for transmission", event->type);
        /* Add to BLE notification queue */
    }
}

/* Initialization */
static K_THREAD_STACK_DEFINE(dispatcher_stack, 2048);
static struct k_thread dispatcher_thread;

int event_dispatcher_init(void)
{
    k_mutex_init(&subscriber_mutex);

    k_msgq_init(&event_queue, queue_buffer, sizeof(struct event), 20);

    /* Register subscribers */
    event_subscribe(display_subscriber,
                    (1 << EVENT_SENSOR_TEMP) | (1 << EVENT_SENSOR_HUMIDITY));

    event_subscribe(storage_subscriber,
                    (1 << EVENT_SENSOR_TEMP) | (1 << EVENT_SENSOR_HUMIDITY) |
                    (1 << EVENT_SENSOR_PRESSURE));

    event_subscribe(network_subscriber,
                    (1 << EVENT_SENSOR_TEMP) | (1 << EVENT_BATTERY_LOW));

    /* Create dispatcher thread */
    k_tid_t tid = k_thread_create(
        &dispatcher_thread, dispatcher_stack,
        K_THREAD_STACK_SIZEOF(dispatcher_stack),
        event_dispatcher_thread,
        NULL, NULL, NULL,
        K_PRIO_PREEMPT(6), 0, K_NO_WAIT
    );

    if (!tid) {
        LOG_ERR("Failed to create dispatcher thread");
        return -ENOMEM;
    }

    k_thread_name_set(tid, "event_dispatch");

    LOG_INF("Event dispatcher initialized with %d subscribers", num_subscribers);
    return 0;
}

/* Example producer */
void sensor_read_callback(int32_t temp, int32_t hum, int32_t press)
{
    struct event event;

    /* Publish temperature event */
    event.type = EVENT_SENSOR_TEMP;
    event.timestamp = k_uptime_get();
    event.payload.temp.value = temp;
    event_publish(&event);

    /* Publish humidity event */
    event.type = EVENT_SENSOR_HUMIDITY;
    event.timestamp = k_uptime_get();
    event.payload.humidity.value = hum;
    event_publish(&event);

    /* Publish pressure event */
    event.type = EVENT_SENSOR_PRESSURE;
    event.timestamp = k_uptime_get();
    event.payload.pressure.value = press;
    event_publish(&event);
}
```

**Key Design Decisions:**

1. **Typed events:** Discriminated union ensures type safety
2. **Subscriber registry:** Bounded array, mutex-protected for thread safety
3. **Event mask:** Subscribers declare interest via bitmask, efficient filtering
4. **Decoupling:** Producers call `event_publish()`, consumers register callbacks — no direct coupling
5. **Fan-out:** Single event delivered to all matching subscribers
6. **Non-blocking publish:** Publisher never waits for consumers

**When to use:**
- One producer, multiple consumers
- When adding new consumers shouldn't require changing producer code
- When consumers have different interests (filtering needed)

**When NOT to use:**
- Point-to-point communication (use message queue directly)
- When order of delivery matters (subscribers notified in registration order, not guaranteed)

---

## Zero-Copy Pipeline

**Problem:** Minimize data copying in producer → processing → consumer pipeline.

**Solution:** ISR signals work queue, producer allocates from slab, fills buffer, passes pointer via message queue, consumer processes and frees.

### Complete Example: ADC Sampling Pipeline

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(adc_pipeline, LOG_LEVEL_INF);

/* Buffer pool for ADC samples */
#define SAMPLE_BUFFER_SIZE 128
#define NUM_BUFFERS 4

K_MEM_SLAB_DEFINE(sample_buffer_pool, SAMPLE_BUFFER_SIZE, NUM_BUFFERS, 4);

struct sample_buffer {
    uint16_t data[SAMPLE_BUFFER_SIZE / sizeof(uint16_t)];
    size_t count;
    int64_t timestamp;
};

/* Message queue for buffer pointers (zero-copy) */
static struct k_msgq buffer_queue;
static char __aligned(4) queue_buffer[NUM_BUFFERS * sizeof(struct sample_buffer *)];

/* Work item for deferred processing */
static struct k_work adc_work;

/* ADC device */
static const struct device *adc_dev;

/**
 * @brief ADC data ready ISR
 *
 * Called in ISR context when ADC conversion complete.
 * Defers work to thread context via work queue.
 */
static void adc_data_ready_isr(const struct device *dev)
{
    ARG_UNUSED(dev);

    /* In ISR context — just submit work, no blocking calls */
    k_work_submit(&adc_work);
}

/**
 * @brief Producer work handler (runs in system work queue thread)
 *
 * Allocates buffer, reads ADC samples, passes pointer to consumer.
 */
static void adc_work_handler(struct k_work *work)
{
    ARG_UNUSED(work);

    struct sample_buffer *buf;

    /* Allocate buffer from pool */
    int ret = k_mem_slab_alloc(&sample_buffer_pool, (void **)&buf, K_NO_WAIT);
    if (ret != 0) {
        LOG_WRN("No buffers available, dropping ADC sample");
        return;
    }

    /* Fill buffer with ADC samples */
    buf->count = SAMPLE_BUFFER_SIZE / sizeof(uint16_t);
    buf->timestamp = k_uptime_get();

    /* Read from ADC into buffer (blocking call OK in work queue context) */
    for (size_t i = 0; i < buf->count; i++) {
        /* Simplified: actual ADC read would use channel config */
        buf->data[i] = adc_read_sample(adc_dev, 0);
    }

    /* Pass pointer to consumer (ownership transfer) */
    ret = k_msgq_put(&buffer_queue, &buf, K_NO_WAIT);
    if (ret != 0) {
        LOG_ERR("Buffer queue full, dropping sample");
        k_mem_slab_free(&sample_buffer_pool, buf);
        return;
    }

    LOG_DBG("Producer: Sent buffer %p with %zu samples", buf, buf->count);
}

/**
 * @brief Consumer thread
 *
 * Receives buffer pointers, processes data, frees buffers.
 */
static void consumer_thread_entry(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    struct sample_buffer *buf;

    while (1) {
        /* Block until buffer available */
        k_msgq_get(&buffer_queue, &buf, K_FOREVER);

        LOG_DBG("Consumer: Received buffer %p with %zu samples", buf, buf->count);

        /* Process samples */
        uint32_t sum = 0;
        for (size_t i = 0; i < buf->count; i++) {
            sum += buf->data[i];
        }
        uint16_t avg = sum / buf->count;

        LOG_INF("ADC average: %u (timestamp: %lld ms)", avg, buf->timestamp);

        /* Consumer owns the buffer — must free it */
        k_mem_slab_free(&sample_buffer_pool, buf);

        LOG_DBG("Consumer: Released buffer %p", buf);
    }
}

/* Initialization */
static K_THREAD_STACK_DEFINE(consumer_stack, 2048);
static struct k_thread consumer_thread;

int adc_pipeline_init(void)
{
    /* Get ADC device from devicetree */
    adc_dev = DEVICE_DT_GET(DT_NODELABEL(adc0));
    if (!device_is_ready(adc_dev)) {
        LOG_ERR("ADC device not ready");
        return -ENODEV;
    }

    /* Runtime init of message queue */
    k_msgq_init(&buffer_queue, queue_buffer,
                sizeof(struct sample_buffer *), NUM_BUFFERS);

    /* Initialize work item */
    k_work_init(&adc_work, adc_work_handler);

    /* Create consumer thread */
    k_tid_t tid = k_thread_create(
        &consumer_thread, consumer_stack,
        K_THREAD_STACK_SIZEOF(consumer_stack),
        consumer_thread_entry,
        NULL, NULL, NULL,
        K_PRIO_PREEMPT(5), 0, K_NO_WAIT
    );

    if (!tid) {
        LOG_ERR("Failed to create consumer thread");
        return -ENOMEM;
    }

    k_thread_name_set(tid, "adc_consumer");

    /* Configure ADC to trigger ISR on data ready */
    /* (Simplified: actual ADC config would use channel setup) */
    adc_register_callback(adc_dev, adc_data_ready_isr);

    LOG_INF("ADC pipeline initialized");
    return 0;
}
```

**Ownership flow:**

1. **ISR:** Signals work queue (no allocation, no blocking)
2. **Work handler (producer):** Allocates buffer from slab, fills with ADC data, puts pointer on queue
3. **Message queue:** Transfers pointer (not data) — zero-copy
4. **Consumer:** Receives pointer, processes data, frees buffer

**Key Design Decisions:**

1. **Fixed-size buffers:** `K_MEM_SLAB` provides constant-time alloc/free
2. **Pointer passing:** Message queue carries `struct sample_buffer *`, not the full buffer
3. **Clear ownership:** Producer allocates, consumer frees — no ambiguity
4. **ISR defers to work queue:** ISR only submits work, all blocking operations in work handler
5. **Bounded resource usage:** `NUM_BUFFERS` limits memory, allocation fails gracefully

**When to use:**
- Large data transfers (audio samples, image buffers, sensor bursts)
- Real-time constraints (copying is too slow)
- When buffer pool can be bounded at compile time

**When NOT to use:**
- Small messages (< 64 bytes) — copying is faster than pointer indirection
- When buffer lifetime is complex (multiple consumers sharing same buffer)

---

## Health Monitor Pattern

**Problem:** Detect resource exhaustion before it causes failures.

**Solution:** Low-priority thread periodically checks queue depths, heap usage, stack margins. Logs warnings when approaching limits, triggers recovery actions.

### Complete Example: System Health Monitor

```c
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/heap_listener.h>

LOG_MODULE_REGISTER(health_monitor, LOG_LEVEL_INF);

/* External references to subsystem resources */
extern struct k_msgq sensor_queue;
extern struct k_msgq network_queue;
extern struct k_thread sensor_thread;
extern struct k_thread network_thread;
extern struct k_heap sensor_heap;
extern struct k_heap network_heap;

/* Health thresholds (percentages) */
#define QUEUE_WARN_THRESHOLD 75
#define HEAP_WARN_THRESHOLD 80
#define STACK_WARN_THRESHOLD 256  /* Bytes remaining */

/* Health status */
struct health_status {
    bool sensor_queue_ok;
    bool network_queue_ok;
    bool sensor_heap_ok;
    bool network_heap_ok;
    bool sensor_stack_ok;
    bool network_stack_ok;
};

static struct health_status health;

/**
 * @brief Check message queue health
 */
static void check_queue_health(const char *name, struct k_msgq *queue,
                                 bool *health_flag)
{
    uint32_t used = k_msgq_num_used_get(queue);
    uint32_t free = k_msgq_num_free_get(queue);
    uint32_t total = used + free;

    if (total == 0) {
        return;  /* Queue not initialized or invalid */
    }

    uint32_t usage_pct = (used * 100) / total;

    if (usage_pct >= QUEUE_WARN_THRESHOLD) {
        if (*health_flag) {
            LOG_WRN("%s queue high usage: %u/%u (%u%%)",
                    name, used, total, usage_pct);
            *health_flag = false;
        }
    } else {
        if (!*health_flag) {
            LOG_INF("%s queue usage normalized: %u/%u (%u%%)",
                    name, used, total, usage_pct);
            *health_flag = true;
        }
    }
}

/**
 * @brief Check heap health
 */
static void check_heap_health(const char *name, struct k_heap *heap,
                                bool *health_flag)
{
    struct sys_memory_stats stats;
    int ret = sys_heap_runtime_stats_get(&heap->heap, &stats);
    if (ret != 0) {
        return;
    }

    if (stats.max_allocated_bytes == 0) {
        return;
    }

    uint32_t usage_pct = (stats.allocated_bytes * 100) / stats.max_allocated_bytes;

    if (usage_pct >= HEAP_WARN_THRESHOLD) {
        if (*health_flag) {
            LOG_WRN("%s heap high usage: %zu/%zu bytes (%u%%)",
                    name, stats.allocated_bytes,
                    stats.max_allocated_bytes, usage_pct);
            *health_flag = false;
        }
    } else {
        if (!*health_flag) {
            LOG_INF("%s heap usage normalized: %zu/%zu bytes (%u%%)",
                    name, stats.allocated_bytes,
                    stats.max_allocated_bytes, usage_pct);
            *health_flag = true;
        }
    }
}

/**
 * @brief Check thread stack health
 */
static void check_stack_health(const char *name, struct k_thread *thread,
                                 bool *health_flag)
{
    size_t unused;
    int ret = k_thread_stack_space_get(thread, &unused);
    if (ret != 0) {
        LOG_ERR("Failed to get stack space for %s: %d", name, ret);
        return;
    }

    if (unused < STACK_WARN_THRESHOLD) {
        if (*health_flag) {
            LOG_ERR("%s stack critical: %zu bytes free", name, unused);
            *health_flag = false;

            /* Recovery action: could increase priority, pause non-critical tasks */
        }
    } else {
        if (!*health_flag) {
            LOG_INF("%s stack space recovered: %zu bytes free", name, unused);
            *health_flag = true;
        }
    }
}

/**
 * @brief Health monitor thread
 *
 * Low priority, runs periodically to check system health.
 */
static void health_monitor_thread(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    /* Initialize health status (all OK initially) */
    health.sensor_queue_ok = true;
    health.network_queue_ok = true;
    health.sensor_heap_ok = true;
    health.network_heap_ok = true;
    health.sensor_stack_ok = true;
    health.network_stack_ok = true;

    LOG_INF("Health monitor started");

    while (1) {
        /* Check queue depths */
        check_queue_health("sensor", &sensor_queue, &health.sensor_queue_ok);
        check_queue_health("network", &network_queue, &health.network_queue_ok);

        /* Check heap usage */
        check_heap_health("sensor", &sensor_heap, &health.sensor_heap_ok);
        check_heap_health("network", &network_heap, &health.network_heap_ok);

        /* Check stack margins */
        check_stack_health("sensor", &sensor_thread, &health.sensor_stack_ok);
        check_stack_health("network", &network_thread, &health.network_stack_ok);

        /* Overall health summary */
        bool all_ok = health.sensor_queue_ok && health.network_queue_ok &&
                      health.sensor_heap_ok && health.network_heap_ok &&
                      health.sensor_stack_ok && health.network_stack_ok;

        if (all_ok) {
            LOG_DBG("System health: OK");
        } else {
            LOG_WRN("System health: DEGRADED");
        }

        /* Sleep until next check (low priority, doesn't need frequent updates) */
        k_sleep(K_SECONDS(10));
    }
}

/* Initialization */
static K_THREAD_STACK_DEFINE(health_stack, 1536);
static struct k_thread health_thread;

int health_monitor_init(void)
{
    /* Create health monitor thread with low priority */
    k_tid_t tid = k_thread_create(
        &health_thread, health_stack,
        K_THREAD_STACK_SIZEOF(health_stack),
        health_monitor_thread,
        NULL, NULL, NULL,
        K_PRIO_PREEMPT(14),  /* Low priority */
        0, K_NO_WAIT
    );

    if (!tid) {
        LOG_ERR("Failed to create health monitor thread");
        return -ENOMEM;
    }

    k_thread_name_set(tid, "health_mon");

    LOG_INF("Health monitor initialized");
    return 0;
}
```

**Key Design Decisions:**

1. **Low priority:** Health monitor runs at priority 14 (very low), doesn't interfere with real work
2. **Hysteresis:** State changes logged only once (not every check cycle), prevents log spam
3. **Proactive warnings:** Detects approaching limits before failures occur
4. **Multiple resource types:** Queues, heaps, stacks all monitored
5. **Recovery hooks:** Can trigger actions (pause tasks, increase priority, free caches)

**When to use:**
- Production systems where resource exhaustion is a risk
- During development to validate resource budgets
- Systems with multiple subsystems competing for resources

**When NOT to use:**
- Extremely resource-constrained systems (health monitor itself consumes resources)
- When resource usage is trivially bounded (single thread, static buffers)

---

## Retry with Backoff

**Problem:** Transient failures (I2C NAK, SPI timeout, network disconnect) should be retried, but not in a tight loop.

**Solution:** Retry with exponential backoff, Kconfig max retry count, logging at each level, failure propagation after exhaustion.

### Complete Example: I2C Communication with Retry

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(i2c_retry, LOG_LEVEL_INF);

/* Retry configuration (could be Kconfig) */
#define I2C_MAX_RETRIES 5
#define I2C_INITIAL_BACKOFF_MS 10
#define I2C_MAX_BACKOFF_MS 1000

/**
 * @brief Write to I2C device with retry and exponential backoff
 *
 * @param dev I2C device
 * @param addr Device address
 * @param data Data to write
 * @param len Data length
 *
 * @retval 0 Success
 * @retval -EIO I2C write failed after all retries
 * @retval -ENODEV Device not ready
 */
int i2c_write_with_retry(const struct device *dev, uint16_t addr,
                          const uint8_t *data, size_t len)
{
    if (!device_is_ready(dev)) {
        LOG_ERR("I2C device not ready");
        return -ENODEV;
    }

    int retry_count = 0;
    int backoff_ms = I2C_INITIAL_BACKOFF_MS;

    while (retry_count <= I2C_MAX_RETRIES) {
        int ret = i2c_write(dev, data, len, addr);

        if (ret == 0) {
            if (retry_count > 0) {
                LOG_INF("I2C write succeeded after %d retries", retry_count);
            }
            return 0;  /* Success */
        }

        retry_count++;

        if (retry_count > I2C_MAX_RETRIES) {
            LOG_ERR("I2C write failed after %d retries: %d",
                    I2C_MAX_RETRIES, ret);
            return -EIO;
        }

        LOG_WRN("I2C write failed (attempt %d/%d): %d, retrying in %d ms",
                retry_count, I2C_MAX_RETRIES, ret, backoff_ms);

        k_sleep(K_MSEC(backoff_ms));

        /* Exponential backoff with cap */
        backoff_ms *= 2;
        if (backoff_ms > I2C_MAX_BACKOFF_MS) {
            backoff_ms = I2C_MAX_BACKOFF_MS;
        }
    }

    return -EIO;  /* Unreachable, but keeps compiler happy */
}

/**
 * @brief Read from I2C device with retry and exponential backoff
 *
 * @param dev I2C device
 * @param addr Device address
 * @param data Buffer for read data
 * @param len Data length
 *
 * @retval 0 Success
 * @retval -EIO I2C read failed after all retries
 * @retval -ENODEV Device not ready
 */
int i2c_read_with_retry(const struct device *dev, uint16_t addr,
                         uint8_t *data, size_t len)
{
    if (!device_is_ready(dev)) {
        LOG_ERR("I2C device not ready");
        return -ENODEV;
    }

    int retry_count = 0;
    int backoff_ms = I2C_INITIAL_BACKOFF_MS;

    while (retry_count <= I2C_MAX_RETRIES) {
        int ret = i2c_read(dev, data, len, addr);

        if (ret == 0) {
            if (retry_count > 0) {
                LOG_INF("I2C read succeeded after %d retries", retry_count);
            }
            return 0;
        }

        retry_count++;

        if (retry_count > I2C_MAX_RETRIES) {
            LOG_ERR("I2C read failed after %d retries: %d",
                    I2C_MAX_RETRIES, ret);
            return -EIO;
        }

        LOG_WRN("I2C read failed (attempt %d/%d): %d, retrying in %d ms",
                retry_count, I2C_MAX_RETRIES, ret, backoff_ms);

        k_sleep(K_MSEC(backoff_ms));

        backoff_ms *= 2;
        if (backoff_ms > I2C_MAX_BACKOFF_MS) {
            backoff_ms = I2C_MAX_BACKOFF_MS;
        }
    }

    return -EIO;
}

/**
 * @brief Write-then-read I2C transaction with retry
 *
 * Common pattern for register reads.
 *
 * @param dev I2C device
 * @param addr Device address
 * @param write_data Data to write (e.g., register address)
 * @param write_len Write data length
 * @param read_data Buffer for read data
 * @param read_len Read data length
 *
 * @retval 0 Success
 * @retval -EIO Transaction failed after all retries
 * @retval -ENODEV Device not ready
 */
int i2c_write_read_with_retry(const struct device *dev, uint16_t addr,
                                const uint8_t *write_data, size_t write_len,
                                uint8_t *read_data, size_t read_len)
{
    if (!device_is_ready(dev)) {
        LOG_ERR("I2C device not ready");
        return -ENODEV;
    }

    int retry_count = 0;
    int backoff_ms = I2C_INITIAL_BACKOFF_MS;

    while (retry_count <= I2C_MAX_RETRIES) {
        int ret = i2c_write_read(dev, addr, write_data, write_len,
                                  read_data, read_len);

        if (ret == 0) {
            if (retry_count > 0) {
                LOG_INF("I2C write-read succeeded after %d retries", retry_count);
            }
            return 0;
        }

        retry_count++;

        if (retry_count > I2C_MAX_RETRIES) {
            LOG_ERR("I2C write-read failed after %d retries: %d",
                    I2C_MAX_RETRIES, ret);
            return -EIO;
        }

        LOG_WRN("I2C write-read failed (attempt %d/%d): %d, retrying in %d ms",
                retry_count, I2C_MAX_RETRIES, ret, backoff_ms);

        k_sleep(K_MSEC(backoff_ms));

        backoff_ms *= 2;
        if (backoff_ms > I2C_MAX_BACKOFF_MS) {
            backoff_ms = I2C_MAX_BACKOFF_MS;
        }
    }

    return -EIO;
}
```

**Key Design Decisions:**

1. **Exponential backoff:** Start at 10ms, double each retry, cap at 1000ms
2. **Configurable limits:** `I2C_MAX_RETRIES` can be Kconfig symbol
3. **Logging levels:** First failure = WRN, final failure = ERR, success after retry = INF
4. **Failure propagation:** After exhausting retries, return `-EIO` to caller
5. **No silent retries:** Every retry attempt logged with context

**When to use:**
- Transient hardware failures (I2C NAK, SPI timeout)
- Network communication (BLE disconnect, packet loss)
- Flash operations (busy status)

**When NOT to use:**
- Permanent failures (device not present) — retries waste time
- Real-time paths where latency is critical

---

All examples follow the plugin's non-negotiables:
- **Runtime init:** `k_msgq_init()`, `k_thread_create()`, never `K_*_DEFINE` macros
- **HAL APIs:** `DEVICE_DT_GET()`, `device_is_ready()`, Zephyr driver APIs
- **Structured logging:** `LOG_MODULE_REGISTER()` + `LOG_*()`, never `printk`
- **Private heaps:** `K_HEAP_DEFINE()`, `K_MEM_SLAB_DEFINE()`, never `k_malloc`
- **errno returns:** All fallible functions return negative errno, callers check
- **C17 only:** No C++, no GCC extensions, no VLAs

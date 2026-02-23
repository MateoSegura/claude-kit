---
name: coding-embedded-zephyr-tester:mock-strategies
description: "FFF (Fake Function Framework) mocking strategies for Zephyr RTOS: test double taxonomy, FFF setup and usage, custom_fake patterns, call history verification, mock reset conventions, mocking Zephyr drivers and subsystems, and building reusable mock libraries."
user-invocable: false
---

# FFF Mocking Strategies for Zephyr

## Test Double Taxonomy

Before mocking, choose the right type of test double:

| Type | Purpose | FFF Pattern | When to Use |
|------|---------|-------------|-------------|
| **Fake** | Simplified working implementation | `custom_fake` with logic | Complex dependencies with multiple interacting methods |
| **Stub** | Returns canned values | `return_val` / `return_val_seq` | Simple dependencies where only return value matters |
| **Mock** | Verifies interactions | `call_count`, `arg_history` | When you need to verify HOW a dependency was called |
| **Spy** | Records calls, delegates to real | `custom_fake` wrapping real | When you want real behavior plus call recording |

### Decision Guide

1. **Does the test only care about the return value?** Use a stub (`return_val`).
2. **Does the test need to verify the function was called with specific arguments?** Use a mock (`arg_history`, `call_count`).
3. **Does the test need the dependency to have simplified but working behavior?** Use a fake (`custom_fake`).
4. **Does the test need real behavior plus call recording?** Use a spy (`custom_fake` wrapping the real implementation).

## FFF Setup

### Include and Global Declaration

Every test file using FFF needs:

```c
#include <zephyr/fff.h>
DEFINE_FFF_GLOBALS;
```

`DEFINE_FFF_GLOBALS` must appear exactly once per test binary. If multiple .c files use FFF, put it in the main test file only.

### Declaring Fakes

#### Value-Returning Functions

```c
FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);
FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
                enum sensor_channel, struct sensor_value *);
```

Signature: `FAKE_VALUE_FUNC(return_type, func_name, arg1_type, arg2_type, ...)`

#### Void Functions

```c
FAKE_VOID_FUNC(k_sem_give, struct k_sem *);
FAKE_VOID_FUNC(gpio_pin_set_dt, const struct gpio_dt_spec *, int);
```

Signature: `FAKE_VOID_FUNC(func_name, arg1_type, arg2_type, ...)`

#### Variadic Functions

```c
FAKE_VALUE_FUNC_VARARG(int, snprintk, char *, size_t, const char *, ...);
```

### Fake Properties

Every fake gets these properties:

| Property | Type | Description |
|----------|------|-------------|
| `call_count` | `unsigned int` | Number of times the fake was called |
| `arg0_val` | varies | Last value of first argument |
| `arg1_val` | varies | Last value of second argument |
| `arg0_history[N]` | varies | History of first argument values |
| `arg1_history[N]` | varies | History of second argument values |
| `return_val` | varies | Value to return (stubs) |
| `return_val_seq` | varies* | Sequence of return values |
| `return_val_seq_len` | `int` | Length of return sequence |
| `custom_fake` | fn ptr | Custom implementation function pointer |

## Stub Patterns

### Fixed Return Value

```c
/* Make sensor_sample_fetch always return success */
sensor_sample_fetch_fake.return_val = 0;

/* Make sensor_sample_fetch always return error */
sensor_sample_fetch_fake.return_val = -EIO;
```

### Return Value Sequence

```c
/* First call succeeds, second fails */
int returns[] = {0, -EIO};
SET_RETURN_SEQ(sensor_sample_fetch_fake, returns, 2);
```

After the sequence is exhausted, subsequent calls return the last value in the sequence.

### Conditional Returns via custom_fake

```c
static int fake_sensor_fetch(const struct device *dev)
{
    if (dev == NULL) {
        return -EINVAL;
    }
    return 0;
}

sensor_sample_fetch_fake.custom_fake = fake_sensor_fetch;
```

## Mock Patterns (Interaction Verification)

### Verify Function Was Called

```c
my_module_do_something();

zassert_equal(sensor_sample_fetch_fake.call_count, 1,
              "sensor_sample_fetch called %d times, expected 1",
              sensor_sample_fetch_fake.call_count);
```

### Verify Call Arguments

```c
my_module_write(buffer, 10);

zassert_equal(spi_write_fake.arg1_val, 10,
              "spi_write called with length %d, expected 10",
              spi_write_fake.arg1_val);
```

### Verify Call Order

```c
module_init();

/* Check global call history for ordering */
zassert_equal(fff.call_history[0], (void *)k_mutex_init,
              "k_mutex_init should be called first");
zassert_equal(fff.call_history[1], (void *)k_msgq_init,
              "k_msgq_init should be called second");
```

### Verify Argument History

```c
/* After multiple calls, check arg history */
process_batch(items, 3);

zassert_equal(process_item_fake.arg0_history[0], &items[0],
              "first call should process item[0]");
zassert_equal(process_item_fake.arg0_history[1], &items[1],
              "second call should process item[1]");
zassert_equal(process_item_fake.arg0_history[2], &items[2],
              "third call should process item[2]");
```

## Fake Patterns (Simplified Implementations)

### Stateful Fake

```c
static struct {
    bool initialized;
    int sample_count;
    struct sensor_value last_value;
} fake_sensor_state;

static int fake_sensor_init(const struct device *dev)
{
    ARG_UNUSED(dev);
    fake_sensor_state.initialized = true;
    fake_sensor_state.sample_count = 0;
    return 0;
}

static int fake_sensor_fetch(const struct device *dev)
{
    if (!fake_sensor_state.initialized) {
        return -ENODEV;
    }
    fake_sensor_state.sample_count++;
    fake_sensor_state.last_value.val1 = 25;
    fake_sensor_state.last_value.val2 = 0;
    return 0;
}
```

### Fake with Callback Trigger

```c
static sensor_trigger_handler_t registered_handler;
static const struct sensor_trigger *registered_trigger;

static int fake_trigger_set(const struct device *dev,
                            const struct sensor_trigger *trig,
                            sensor_trigger_handler_t handler)
{
    registered_handler = handler;
    registered_trigger = trig;
    return 0;
}

/* In test: trigger the callback manually */
ZTEST(sensor, test_trigger_fires_callback)
{
    sensor_trigger_set_fake.custom_fake = fake_trigger_set;
    my_module_setup_trigger();

    /* Simulate the trigger firing */
    zassert_not_null(registered_handler, "handler not registered");
    registered_handler(dev, registered_trigger);

    /* Verify the module handled the trigger */
    zassert_true(module_got_data(), "module did not process trigger");
}
```

## Mock Reset Conventions

### Always Reset in before() Function

```c
static void suite_before(void *f)
{
    /* Reset all fakes */
    RESET_FAKE(sensor_sample_fetch);
    RESET_FAKE(sensor_channel_get);
    RESET_FAKE(sensor_trigger_set);
    RESET_FAKE(k_sem_take);
    RESET_FAKE(k_sem_give);

    /* Reset global call history */
    FFF_RESET_HISTORY();

    /* Reset custom state if using stateful fakes */
    memset(&fake_sensor_state, 0, sizeof(fake_sensor_state));
}
```

### What RESET_FAKE Clears

- `call_count` = 0
- `arg*_val` = 0/NULL
- `arg*_history[]` = all zeroed
- `return_val` = 0/NULL
- `return_val_seq` = NULL
- `return_val_seq_len` = 0
- `custom_fake` = NULL

### What FFF_RESET_HISTORY Clears

- `fff.call_history[]` = all NULL
- `fff.call_history_idx` = 0

## Mocking Zephyr APIs

### Kernel Primitives

```c
/* Semaphore */
FAKE_VALUE_FUNC(int, k_sem_take, struct k_sem *, k_timeout_t);
FAKE_VOID_FUNC(k_sem_give, struct k_sem *);
FAKE_VALUE_FUNC(int, k_sem_init, struct k_sem *, unsigned int, unsigned int);

/* Mutex */
FAKE_VALUE_FUNC(int, k_mutex_lock, struct k_mutex *, k_timeout_t);
FAKE_VALUE_FUNC(int, k_mutex_unlock, struct k_mutex *);

/* Message Queue */
FAKE_VALUE_FUNC(int, k_msgq_put, struct k_msgq *, const void *, k_timeout_t);
FAKE_VALUE_FUNC(int, k_msgq_get, struct k_msgq *, void *, k_timeout_t);
```

### Device API

```c
FAKE_VALUE_FUNC(bool, device_is_ready, const struct device *);
```

### GPIO

```c
FAKE_VALUE_FUNC(int, gpio_pin_configure_dt, const struct gpio_dt_spec *, gpio_flags_t);
FAKE_VALUE_FUNC(int, gpio_pin_set_dt, const struct gpio_dt_spec *, int);
FAKE_VALUE_FUNC(int, gpio_pin_get_dt, const struct gpio_dt_spec *);
FAKE_VALUE_FUNC(int, gpio_pin_interrupt_configure_dt, const struct gpio_dt_spec *, gpio_flags_t);
```

### Sensor

```c
FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);
FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
                enum sensor_channel, struct sensor_value *);
FAKE_VALUE_FUNC(int, sensor_trigger_set, const struct device *,
                const struct sensor_trigger *, sensor_trigger_handler_t);
```

## Reusable Mock Libraries

For large projects, create shared mock headers:

```
tests/
├── mocks/
│   ├── mock_gpio.h        # FFF declarations for GPIO API
│   ├── mock_sensor.h      # FFF declarations for sensor API
│   ├── mock_i2c.h         # FFF declarations for I2C API
│   └── mock_kernel.h      # FFF declarations for kernel primitives
├── unit/
│   └── sensor_mgr/
│       └── src/
│           └── main.c     # #include "mock_sensor.h" + "mock_kernel.h"
```

Each mock header contains only `FAKE_*_FUNC` declarations. `DEFINE_FFF_GLOBALS` stays in the test's main.c.

## FFF API Reference

See [fff-reference.md](fff-reference.md) for the complete FFF macro reference.

# FFF (Fake Function Framework) Reference

Complete API reference for FFF macros used in Zephyr test suites. Header: `<zephyr/fff.h>`.

## Setup Macros

### DEFINE_FFF_GLOBALS

```c
DEFINE_FFF_GLOBALS;
```

Must appear exactly once per test binary. Defines the global call history array and index. Place in the main test source file, outside any function.

### FFF_RESET_HISTORY

```c
FFF_RESET_HISTORY();
```

Resets the global call history (`fff.call_history[]` and `fff.call_history_idx`). Call in the `before` fixture function alongside individual `RESET_FAKE` calls.

## Fake Declaration Macros

### FAKE_VALUE_FUNC

Declare a fake for a function that returns a value.

```c
FAKE_VALUE_FUNC(return_type, func_name, arg1_type, arg2_type, ...)
```

Supports 0 to 20 arguments.

**Examples:**

```c
/* No arguments */
FAKE_VALUE_FUNC(int, get_status);

/* One argument */
FAKE_VALUE_FUNC(bool, device_is_ready, const struct device *);

/* Two arguments */
FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);

/* Three arguments */
FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
                enum sensor_channel, struct sensor_value *);

/* Four arguments */
FAKE_VALUE_FUNC(int, spi_transceive, const struct device *,
                const struct spi_config *, const struct spi_buf_set *,
                const struct spi_buf_set *);
```

### FAKE_VOID_FUNC

Declare a fake for a function that returns void.

```c
FAKE_VOID_FUNC(func_name, arg1_type, arg2_type, ...)
```

**Examples:**

```c
FAKE_VOID_FUNC(k_sem_give, struct k_sem *);
FAKE_VOID_FUNC(gpio_pin_set_dt, const struct gpio_dt_spec *, int);
FAKE_VOID_FUNC(log_output, const char *, size_t);
```

### FAKE_VALUE_FUNC_VARARG

For variadic functions:

```c
FAKE_VALUE_FUNC_VARARG(return_type, func_name, arg1_type, ...)
```

```c
FAKE_VALUE_FUNC_VARARG(int, snprintk, char *, size_t, const char *, ...);
```

### FAKE_VOID_FUNC_VARARG

```c
FAKE_VOID_FUNC_VARARG(func_name, arg1_type, ...)
```

## Fake Properties

After declaring a fake, these properties are available on `<func_name>_fake`:

### Return Value Control

#### return_val

```c
sensor_sample_fetch_fake.return_val = -EIO;
```

Sets the value returned by every call to the fake (unless overridden by `return_val_seq` or `custom_fake`).

#### SET_RETURN_SEQ

```c
int returns[] = {0, 0, -ENOMEM};
SET_RETURN_SEQ(sensor_sample_fetch_fake, returns, 3);
```

Sets a sequence of return values. The Nth call returns `returns[N-1]`. After the sequence is exhausted, subsequent calls return the last value.

### Call Tracking

#### call_count

```c
unsigned int count = sensor_sample_fetch_fake.call_count;
```

Number of times the fake was called since the last `RESET_FAKE`.

#### arg0_val, arg1_val, arg2_val, ...

```c
const struct device *last_dev = sensor_sample_fetch_fake.arg0_val;
```

The argument values from the **most recent** call.

#### arg0_history[], arg1_history[], ...

```c
const struct device *first_call_dev = sensor_sample_fetch_fake.arg0_history[0];
const struct device *second_call_dev = sensor_sample_fetch_fake.arg0_history[1];
```

History of argument values across calls. Default history depth is `FFF_ARG_HISTORY_LEN` (50).

### Custom Implementation

#### custom_fake

```c
static int my_custom_fetch(const struct device *dev)
{
    if (dev == NULL) {
        return -EINVAL;
    }
    return 0;
}

sensor_sample_fetch_fake.custom_fake = my_custom_fetch;
```

When `custom_fake` is set, it is called instead of returning `return_val`. The custom fake receives the same arguments as the original function. This takes priority over `return_val` and `return_val_seq`.

## Reset Macros

### RESET_FAKE

```c
RESET_FAKE(sensor_sample_fetch);
```

Resets a single fake to its initial state:
- `call_count` = 0
- All `arg*_val` = 0
- All `arg*_history[]` = zeroed
- `return_val` = 0
- `return_val_seq` = NULL
- `return_val_seq_len` = 0
- `custom_fake` = NULL

### FFF_RESET_HISTORY

```c
FFF_RESET_HISTORY();
```

Resets the global call order history. Does NOT reset individual fake state.

### Complete Reset Pattern

```c
static void suite_before(void *f)
{
    RESET_FAKE(func_a);
    RESET_FAKE(func_b);
    RESET_FAKE(func_c);
    FFF_RESET_HISTORY();
}
```

Always reset ALL fakes, not just the ones you think will be used. A previous test may have set up a custom_fake that will affect the current test.

## Global Call History

### fff.call_history

```c
fff.call_history[0]  /* Function pointer of the first function called */
fff.call_history[1]  /* Function pointer of the second function called */
```

Maximum depth: `FFF_CALL_HISTORY_LEN` (default 50).

### Verifying Call Order

```c
/* Verify init calls happen in correct order */
module_init();

zassert_equal(fff.call_history[0], (void *)k_mutex_init,
              "first call should be k_mutex_init");
zassert_equal(fff.call_history[1], (void *)k_sem_init,
              "second call should be k_sem_init");
zassert_equal(fff.call_history[2], (void *)k_msgq_init,
              "third call should be k_msgq_init");
```

## Configuration Macros

### FFF_ARG_HISTORY_LEN

Default: 50. Maximum number of calls for which argument history is recorded.

```c
#define FFF_ARG_HISTORY_LEN 100  /* Increase before including fff.h */
#include <zephyr/fff.h>
```

### FFF_CALL_HISTORY_LEN

Default: 50. Maximum depth of the global call history.

```c
#define FFF_CALL_HISTORY_LEN 100
#include <zephyr/fff.h>
```

## Complete Mock Example

### Header: mock_sensor.h

```c
#ifndef MOCK_SENSOR_H_
#define MOCK_SENSOR_H_

#include <zephyr/fff.h>
#include <zephyr/drivers/sensor.h>

FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);
FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
                enum sensor_channel, struct sensor_value *);
FAKE_VALUE_FUNC(int, sensor_trigger_set, const struct device *,
                const struct sensor_trigger *, sensor_trigger_handler_t);

#endif /* MOCK_SENSOR_H_ */
```

### Test: main.c

```c
#include <zephyr/ztest.h>
#include <zephyr/fff.h>
DEFINE_FFF_GLOBALS;

#include "mock_sensor.h"
#include "sensor_mgr.h"

struct sensor_mgr_fixture {
    struct sensor_sample sample;
};

static void *suite_setup(void)
{
    static struct sensor_mgr_fixture fixture;
    return &fixture;
}

static void suite_before(void *f)
{
    struct sensor_mgr_fixture *fixture = f;
    memset(fixture, 0, sizeof(*fixture));
    RESET_FAKE(sensor_sample_fetch);
    RESET_FAKE(sensor_channel_get);
    RESET_FAKE(sensor_trigger_set);
    FFF_RESET_HISTORY();
}

ZTEST_SUITE(sensor_mgr, NULL, suite_setup, suite_before, NULL, NULL);

ZTEST_F(sensor_mgr, test_read_succeeds)
{
    sensor_sample_fetch_fake.return_val = 0;
    sensor_channel_get_fake.custom_fake = fake_channel_get_temp;

    int ret = sensor_mgr_read(&fixture->sample);
    zassert_equal(ret, 0, "read returned %d", ret);
    zassert_equal(sensor_sample_fetch_fake.call_count, 1,
                  "fetch called %d times", sensor_sample_fetch_fake.call_count);
}

ZTEST_F(sensor_mgr, test_read_fails_on_fetch_error)
{
    sensor_sample_fetch_fake.return_val = -EIO;

    int ret = sensor_mgr_read(&fixture->sample);
    zassert_equal(ret, -EIO, "expected -EIO, got %d", ret);
}
```

## Linking Considerations

FFF fakes replace the real function at link time. For this to work:

1. The fake declaration must have the **exact same signature** as the real function.
2. The real function's object file must NOT be linked into the test binary (otherwise you get duplicate symbol errors).
3. Use CMakeLists.txt to control which source files are included in the test build.

```cmake
# Include module under test but NOT the driver it depends on
target_sources(app PRIVATE
    ${APP_SOURCE_DIR}/src/sensor_mgr/sensor_mgr.c
    # Do NOT include sensor driver -- FFF fake replaces it
)
```

If you need to mock a function from a Zephyr library that is automatically linked, you may need to use `--wrap` linker flags or restructure the code to use function pointers for dependency injection.

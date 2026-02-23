---
name: coding-embedded-zephyr-tester:ztest-patterns
description: "Complete ztest framework reference: ZTEST_SUITE, ZTEST, ZTEST_F, ZTEST_RULE, assertions (zassert_*), test fixtures, parameterized tests, test ordering, ztress stress testing, and test-specific Kconfig patterns for Zephyr RTOS testing."
user-invocable: false
---

# Zephyr ztest Framework Patterns

## Suite Registration

Every test file uses `ZTEST_SUITE` to register a test suite. The macro signature:

```c
ZTEST_SUITE(suite_name, predicate, setup, before, after, teardown);
```

- **suite_name**: Identifier for the suite. Must be unique across the test binary.
- **predicate**: Function returning `bool` to conditionally run the suite, or `NULL` to always run.
- **setup**: One-time suite setup. Returns `void *` pointer to fixture data. Called once before any test in the suite. `NULL` if no fixture needed.
- **before**: Per-test setup. Called before each ZTEST in the suite. Receives fixture pointer. `NULL` if not needed.
- **after**: Per-test teardown. Called after each ZTEST. Receives fixture pointer. Use for mock resets. `NULL` if not needed.
- **teardown**: One-time suite teardown. Receives fixture pointer. Called once after all tests. `NULL` if not needed.

### Suite Without Fixture

```c
ZTEST_SUITE(my_module, NULL, NULL, NULL, NULL, NULL);

ZTEST(my_module, test_basic_operation)
{
    int ret = my_function(42);
    zassert_equal(ret, 0, "my_function(42) returned %d", ret);
}
```

### Suite With Fixture

```c
struct my_fixture {
    int initial_value;
    uint8_t buffer[64];
};

static void *my_suite_setup(void)
{
    static struct my_fixture fixture;
    /* One-time init: allocate resources, configure hardware mocks */
    return &fixture;
}

static void my_suite_before(void *f)
{
    struct my_fixture *fixture = f;
    fixture->initial_value = 0;
    memset(fixture->buffer, 0, sizeof(fixture->buffer));
    /* Reset FFF mocks here */
    RESET_FAKE(some_api_call);
    FFF_RESET_HISTORY();
}

static void my_suite_after(void *f)
{
    ARG_UNUSED(f);
    /* Cleanup per-test resources */
}

static void my_suite_teardown(void *f)
{
    ARG_UNUSED(f);
    /* One-time cleanup: free resources */
}

ZTEST_SUITE(my_module, NULL, my_suite_setup, my_suite_before,
            my_suite_after, my_suite_teardown);
```

## Test Macros

### ZTEST -- Test Without Fixture Access

```c
ZTEST(suite_name, test_name)
{
    /* Test body -- no fixture pointer available */
}
```

### ZTEST_F -- Test With Fixture Access

```c
ZTEST_F(suite_name, test_name)
{
    /* 'fixture' pointer is implicitly available as the first parameter */
    zassert_equal(fixture->initial_value, 0,
                  "fixture not properly initialized");
}
```

The fixture pointer type is automatically resolved to the struct returned by `setup`. The variable name is always `fixture`.

### ZTEST_USER -- Userspace Test

```c
ZTEST_USER(suite_name, test_name)
{
    /* Runs in userspace context (requires CONFIG_USERSPACE=y) */
    /* Used for testing permission checks and memory domain isolation */
}
```

### ZTEST_RULE -- Global Before/After for All Suites

```c
static void rule_before(const struct ztest_unit_test *test, void *f)
{
    /* Called before EVERY test in EVERY suite in this binary */
    /* Useful for global mock resets or logging */
    ARG_UNUSED(test);
    ARG_UNUSED(f);
}

static void rule_after(const struct ztest_unit_test *test, void *f)
{
    /* Called after EVERY test in EVERY suite */
    ARG_UNUSED(test);
    ARG_UNUSED(f);
}

ZTEST_RULE(my_rule, rule_before, rule_after);
```

Rules are registered globally and apply to all suites in the test binary. Use for cross-cutting concerns like resetting global state or validating heap integrity.

## Fixture Lifecycle

Execution order for a suite with 2 tests:

```
setup()                    -- once, returns fixture pointer
  before(fixture)          -- before test 1
    ZTEST_F(test_1)        -- test 1 runs
  after(fixture)           -- after test 1
  before(fixture)          -- before test 2
    ZTEST_F(test_2)        -- test 2 runs
  after(fixture)           -- after test 2
teardown(fixture)          -- once, cleanup
```

Key rules:
- `setup` runs exactly once. Use for expensive one-time initialization (allocating memory, setting up complex mock configurations).
- `before` runs before each test. Use for resetting state and mocks to a known baseline.
- `after` runs after each test. Use for releasing per-test resources and validating no state leakage.
- `teardown` runs exactly once after all tests. Use for releasing resources allocated in `setup`.

## Assertions Reference

All `zassert_*` macros accept a format string and variadic arguments as the last parameters for diagnostic messages.

### Value Comparisons

```c
zassert_equal(a, b, "msg", ...);         /* a == b */
zassert_not_equal(a, b, "msg", ...);     /* a != b */
zassert_within(a, b, delta, "msg", ...); /* |a - b| <= delta */
```

### Boolean

```c
zassert_true(cond, "msg", ...);          /* cond is true */
zassert_false(cond, "msg", ...);         /* cond is false */
zassert_ok(ret, "msg", ...);             /* ret == 0 */
```

### Pointer

```c
zassert_not_null(ptr, "msg", ...);       /* ptr != NULL */
zassert_is_null(ptr, "msg", ...);        /* ptr == NULL */
```

### Memory

```c
zassert_mem_equal(buf, expected, len, "msg", ...);  /* memcmp == 0 */
```

### String

```c
zassert_str_equal(s1, s2, "msg", ...);   /* strcmp == 0 */
```

### Control Flow

```c
zassert_unreachable("msg", ...);         /* Fail if reached */
```

## Conditional Test Execution

### Suite Predicate

```c
static bool should_run_ble_tests(void)
{
    /* Only run if BLE subsystem is enabled */
    return IS_ENABLED(CONFIG_BT);
}

ZTEST_SUITE(ble_service, should_run_ble_tests, NULL, NULL, NULL, NULL);
```

### Skipping Individual Tests

```c
ZTEST(my_module, test_hardware_specific_feature)
{
    if (!IS_ENABLED(CONFIG_GPIO)) {
        ztest_test_skip();
        return;
    }
    /* ... test body ... */
}
```

## Parameterized / Table-Driven Tests

Ztest does not have built-in parameterized test support, but table-driven patterns work well:

```c
struct test_vector {
    int input;
    int expected_output;
    const char *description;
};

static const struct test_vector vectors[] = {
    { .input = 0,   .expected_output = 0,    .description = "zero" },
    { .input = 1,   .expected_output = 1,    .description = "one" },
    { .input = -1,  .expected_output = -EINVAL, .description = "negative" },
    { .input = 255, .expected_output = 255,  .description = "max" },
};

ZTEST(my_module, test_process_table_driven)
{
    for (int i = 0; i < ARRAY_SIZE(vectors); i++) {
        int ret = process_value(vectors[i].input);
        zassert_equal(ret, vectors[i].expected_output,
                      "vector[%d] '%s': got %d, expected %d",
                      i, vectors[i].description, ret,
                      vectors[i].expected_output);
    }
}
```

## ztress Stress Testing

For stress testing concurrent operations:

```c
#include <zephyr/ztest.h>
#include <zephyr/ztress.h>

static bool stress_producer(void *user_data, uint32_t cnt, bool last, int prio)
{
    ARG_UNUSED(user_data);
    /* Called repeatedly by the stress framework */
    k_msgq_put(&test_queue, &cnt, K_NO_WAIT);
    return true; /* return false to abort early */
}

static bool stress_consumer(void *user_data, uint32_t cnt, bool last, int prio)
{
    ARG_UNUSED(user_data);
    uint32_t val;
    k_msgq_get(&test_queue, &val, K_MSEC(100));
    return true;
}

ZTEST(my_module, test_concurrent_queue_access)
{
    ztress_set_timeout(K_MSEC(1000));

    ZTRESS_EXECUTE(
        ZTRESS_THREAD(stress_producer, NULL, 0, 0, Z_TIMEOUT_TICKS(10)),
        ZTRESS_THREAD(stress_consumer, NULL, 0, 0, Z_TIMEOUT_TICKS(10))
    );
}
```

## Test-Specific Kconfig

### Common Test Configuration Options

```ini
# Enable ztest framework
CONFIG_ZTEST=y
CONFIG_ZTEST_NEW_API=y

# Stack size for test thread (increase for complex tests)
CONFIG_ZTEST_STACK_SIZE=4096

# Enable address sanitizer on native_sim
CONFIG_ASAN=y

# Enable undefined behavior sanitizer
CONFIG_UBSAN=y

# Coverage instrumentation
CONFIG_COVERAGE=y
CONFIG_COVERAGE_GCOV=y

# Verbose ztest output
CONFIG_ZTEST_VERBOSE_OUTPUT=y

# Shuffle test order to detect interdependence
CONFIG_ZTEST_SHUFFLE=y
CONFIG_TEST_RANDOM_SEED=12345
```

### Test-Specific Kconfig Overlays

In `testcase.yaml`, use `extra_configs` to add test-specific options:

```yaml
tests:
  my_module.unit:
    platform_allow: native_sim
    extra_configs:
      - CONFIG_ZTEST_SHUFFLE=y
      - CONFIG_ASAN=y
```

## Multiple Suites in One Binary

A single test binary can contain multiple suites:

```c
/* Suite 1: tests for module A */
ZTEST_SUITE(module_a, NULL, NULL, module_a_before, module_a_after, NULL);

ZTEST(module_a, test_a_init) { /* ... */ }
ZTEST(module_a, test_a_read) { /* ... */ }

/* Suite 2: tests for module B */
ZTEST_SUITE(module_b, NULL, NULL, module_b_before, module_b_after, NULL);

ZTEST(module_b, test_b_init) { /* ... */ }
ZTEST(module_b, test_b_write) { /* ... */ }
```

Each suite has its own fixture and lifecycle. Suites do not share state.

## Debug Output in Tests

Use `TC_PRINT` for test-specific debug output (not LOG_*):

```c
ZTEST(my_module, test_complex_scenario)
{
    TC_PRINT("Starting complex scenario with %d iterations\n", count);
    /* ... */
    TC_PRINT("Intermediate result: %d\n", intermediate);
    /* ... */
}
```

`TC_PRINT` output appears in twister logs and is useful for diagnosing test failures in CI. Use it sparingly -- tests should not need print debugging under normal circumstances.

## Common Patterns

### Testing Error Paths

```c
ZTEST(my_module, test_init_fails_when_device_not_ready)
{
    /* Arrange: make device_is_ready return false */
    device_is_ready_fake.return_val = false;

    /* Act */
    int ret = my_module_init();

    /* Assert */
    zassert_equal(ret, -ENODEV,
                  "expected -ENODEV when device not ready, got %d", ret);
}
```

### Testing Callback Registration

```c
static bool callback_invoked;
static void test_callback(int value)
{
    callback_invoked = true;
    zassert_equal(value, 42, "callback got %d, expected 42", value);
}

ZTEST(my_module, test_callback_fires_on_event)
{
    callback_invoked = false;
    my_module_register_callback(test_callback);
    my_module_trigger_event(42);
    zassert_true(callback_invoked, "callback was not invoked");
}
```

### Testing Thread-Safe Operations

```c
ZTEST(my_module, test_concurrent_access_is_safe)
{
    /* Verify that mock mutex was locked during operation */
    my_module_protected_operation();

    zassert_equal(k_mutex_lock_fake.call_count, 1,
                  "mutex_lock called %d times, expected 1",
                  k_mutex_lock_fake.call_count);
    zassert_equal(k_mutex_unlock_fake.call_count, 1,
                  "mutex_unlock called %d times, expected 1",
                  k_mutex_unlock_fake.call_count);
}
```

## API Reference

See [ztest-api-reference.md](ztest-api-reference.md) for the complete assertion macro reference with all signatures and examples.

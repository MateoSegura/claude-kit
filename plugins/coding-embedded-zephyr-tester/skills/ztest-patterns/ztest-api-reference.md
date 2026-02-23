# ztest API Reference

Complete reference for the Zephyr ztest framework macros and functions. Header: `<zephyr/ztest.h>`.

## Suite Registration

### ZTEST_SUITE

```c
ZTEST_SUITE(suite_name, predicate, setup, before, after, teardown)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| suite_name | identifier | Unique suite name, used in ZTEST macros |
| predicate | `bool (*)(void)` or `NULL` | Returns true to run suite, NULL = always run |
| setup | `void *(*)(void)` or `NULL` | One-time setup, returns fixture pointer |
| before | `void (*)(void *)` or `NULL` | Per-test setup, receives fixture |
| after | `void (*)(void *)` or `NULL` | Per-test teardown, receives fixture |
| teardown | `void (*)(void *)` or `NULL` | One-time teardown, receives fixture |

## Test Macros

### ZTEST

```c
ZTEST(suite_name, test_name)
{
    /* test body -- no fixture access */
}
```

Register a test case without fixture access.

### ZTEST_F

```c
ZTEST_F(suite_name, test_name)
{
    /* 'fixture' variable is available with the type returned by setup */
}
```

Register a test case with fixture access. The `fixture` variable is automatically typed.

### ZTEST_USER

```c
ZTEST_USER(suite_name, test_name)
{
    /* Runs in userspace. Requires CONFIG_USERSPACE=y */
}
```

### ZTEST_RULE

```c
ZTEST_RULE(rule_name, before_fn, after_fn)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| rule_name | identifier | Unique rule name |
| before_fn | `void (*)(const struct ztest_unit_test *, void *)` | Called before every test |
| after_fn | `void (*)(const struct ztest_unit_test *, void *)` | Called after every test |

## Assertion Macros

All assertions accept optional format string + variadic args as trailing parameters.

### Value Assertions

#### zassert_equal

```c
zassert_equal(a, b, fmt, ...)
```
Fails if `a != b`. Use for integer, enum, and pointer comparisons.

```c
zassert_equal(ret, 0, "init returned %d", ret);
zassert_equal(state, STATE_IDLE, "state is %d, expected IDLE", state);
```

#### zassert_not_equal

```c
zassert_not_equal(a, b, fmt, ...)
```
Fails if `a == b`.

```c
zassert_not_equal(ptr, NULL, "pointer should not be NULL");
```

#### zassert_within

```c
zassert_within(a, b, delta, fmt, ...)
```
Fails if `abs(a - b) > delta`. Use for floating-point or analog values with tolerance.

```c
zassert_within(measured_mv, 3300, 50,
               "voltage %d mV outside 3300 +/- 50 mV", measured_mv);
```

### Boolean Assertions

#### zassert_true

```c
zassert_true(cond, fmt, ...)
```
Fails if `cond` is false (zero).

```c
zassert_true(device_is_ready(dev), "device %s not ready", dev->name);
```

#### zassert_false

```c
zassert_false(cond, fmt, ...)
```
Fails if `cond` is true (non-zero).

```c
zassert_false(module_is_running(), "module should be stopped");
```

#### zassert_ok

```c
zassert_ok(ret, fmt, ...)
```
Fails if `ret != 0`. Convenience for checking Zephyr API return values.

```c
zassert_ok(k_sem_init(&sem, 0, 1), "sem init failed");
```

### Pointer Assertions

#### zassert_not_null

```c
zassert_not_null(ptr, fmt, ...)
```
Fails if `ptr == NULL`.

```c
zassert_not_null(dev, "DEVICE_DT_GET returned NULL");
```

#### zassert_is_null

```c
zassert_is_null(ptr, fmt, ...)
```
Fails if `ptr != NULL`.

```c
zassert_is_null(module_get_context(),
                "context should be NULL before init");
```

### Memory Assertions

#### zassert_mem_equal

```c
zassert_mem_equal(buf, expected, size, fmt, ...)
```
Fails if `memcmp(buf, expected, size) != 0`.

```c
uint8_t expected[] = {0x01, 0x02, 0x03};
zassert_mem_equal(output_buf, expected, sizeof(expected),
                  "output buffer mismatch");
```

### String Assertions

#### zassert_str_equal

```c
zassert_str_equal(s1, s2, fmt, ...)
```
Fails if `strcmp(s1, s2) != 0`.

```c
zassert_str_equal(dev->name, "sensor@76",
                  "device name is '%s'", dev->name);
```

### Control Flow Assertions

#### zassert_unreachable

```c
zassert_unreachable(fmt, ...)
```
Always fails. Place in code paths that should never execute.

```c
switch (state) {
case STATE_IDLE:
    break;
case STATE_RUNNING:
    break;
default:
    zassert_unreachable("unexpected state: %d", state);
}
```

## Test Control Functions

### ztest_test_skip

```c
void ztest_test_skip(void);
```
Mark the current test as skipped. Call and return from the test body:

```c
ZTEST(suite, test_needs_gpio)
{
    if (!IS_ENABLED(CONFIG_GPIO)) {
        ztest_test_skip();
        return;
    }
    /* ... */
}
```

### ztest_test_fail

```c
void ztest_test_fail(void);
```
Explicitly fail the current test.

### ztest_test_pass

```c
void ztest_test_pass(void);
```
Explicitly pass the current test and skip remaining assertions.

## Test Output

### TC_PRINT

```c
TC_PRINT(fmt, ...)
```
Print diagnostic output during test execution. Appears in twister logs.

```c
TC_PRINT("Processing %d samples...\n", sample_count);
```

### TC_ERROR

```c
TC_ERROR(fmt, ...)
```
Print error output during test execution.

### TC_PASS_STR / TC_FAIL_STR

```c
TC_PASS_STR  /* "PASS" */
TC_FAIL_STR  /* "FAIL" */
```

## Kconfig Options

| Symbol | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_ZTEST` | bool | n | Enable ztest framework |
| `CONFIG_ZTEST_NEW_API` | bool | n | Enable new ZTEST_SUITE API |
| `CONFIG_ZTEST_STACK_SIZE` | int | 2048 | Test thread stack size |
| `CONFIG_ZTEST_VERBOSE_OUTPUT` | bool | y | Verbose test output |
| `CONFIG_ZTEST_SHUFFLE` | bool | n | Randomize test execution order |
| `CONFIG_ZTEST_FAIL_FAST` | bool | n | Stop on first failure |
| `CONFIG_ZTEST_ASSERT_VERBOSE` | int | 1 | Assertion message verbosity (0=none, 1=fail, 2=all) |

## Expected Failures

Mark tests that are expected to fail (known bugs awaiting fix):

```c
ZTEST_EXPECT_FAIL(suite_name, test_name);
```

The test is still executed, but a failure is treated as a pass and a pass is treated as a failure. Use sparingly and always pair with a bug tracker reference in a comment.

## Test Ordering

By default, tests within a suite run in registration order (linker section order). To randomize:

```ini
CONFIG_ZTEST_SHUFFLE=y
CONFIG_TEST_RANDOM_SEED=42
```

This detects order-dependent tests. Run with different seeds to increase confidence.

## Multi-Suite Binary Layout

When a binary contains multiple suites, they run in linker registration order. Each suite runs all its tests (with before/after per test) before the next suite begins. Cross-suite dependencies are forbidden.

## Common Pitfalls

1. **Missing `CONFIG_ZTEST_NEW_API=y`:** Without this, the modern `ZTEST_SUITE` / `ZTEST` / `ZTEST_F` macros are not available. The old API uses different patterns.

2. **Fixture pointer in ZTEST (not ZTEST_F):** `ZTEST` does not provide the fixture variable. Use `ZTEST_F` to access fixture data.

3. **Static fixture storage:** The `setup` function must return a pointer to a **static** or **heap-allocated** struct. Returning a pointer to a local variable causes undefined behavior.

4. **Forgetting FFF_RESET_HISTORY:** Resetting individual fakes with `RESET_FAKE` does not reset the global call history. Always call `FFF_RESET_HISTORY()` as well.

5. **Large local buffers in tests:** Test thread stack is limited (default 2048 bytes). Use static or fixture-allocated buffers for large data. Increase `CONFIG_ZTEST_STACK_SIZE` if needed.

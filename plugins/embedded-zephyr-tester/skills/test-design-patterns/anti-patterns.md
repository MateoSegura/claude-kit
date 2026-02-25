# Test Anti-Patterns Reference

Comprehensive catalog of test anti-patterns for Zephyr RTOS embedded systems. Each anti-pattern includes detection strategy, severity, and concrete fix.

## Anti-Pattern Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| **Critical** | Causes false passes, hides bugs | Fix immediately, block PR |
| **High** | Causes flaky tests, wastes CI time | Fix before merge |
| **Medium** | Reduces maintainability | Fix in next refactor |
| **Low** | Style/convention violation | Fix when touching file |

## 1. Test Interdependence (Critical)

Tests that pass in sequence but fail when shuffled or run in isolation.

### Detection
```kconfig
# Enable in testcase.yaml to detect
CONFIG_ZTEST_SHUFFLE=y
```

Run tests 10 times with different seeds:
```bash
for seed in $(seq 1 10); do
    west twister -p native_sim -T tests/unit/my_module/ \
        --extra-args CONFIG_ZTEST_SHUFFLE=y \
        --extra-args CONFIG_ZTEST_SHUFFLE_SUITE_REPEAT_COUNT=3
done
```

### Root Causes
- Shared global/static state not reset between tests
- Missing `RESET_FAKE()` or `FFF_RESET_HISTORY()` in before function
- File system or network state leaking between tests
- Module internal state persisting across tests

### Fix Pattern
```c
static void before(void *f)
{
    /* Reset ALL mocks, not just the ones "this test uses" */
    RESET_FAKE(dep_a);
    RESET_FAKE(dep_b);
    RESET_FAKE(dep_c);
    FFF_RESET_HISTORY();

    /* Reset module under test */
    module_deinit();
    module_init();

    /* Clear any shared buffers */
    memset(shared_buffer, 0, sizeof(shared_buffer));
}
```

## 2. Over-Mocking (High)

Mocking internal functions of the module under test. Tests become coupled to implementation details and break on every refactor.

### Detection Checklist
- [ ] Are you mocking functions defined in the same .c file as the code under test?
- [ ] Do tests break when you refactor internals without changing the API?
- [ ] Are there more mock setup lines than assertion lines?

### Fix
Only mock at module boundaries — external dependencies accessed through function pointers or separate translation units.

```c
/* BAD: Mocking internal helper */
FAKE_VALUE_FUNC(int, internal_compute, int);

/* GOOD: Mock the external dependency */
FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *, enum sensor_channel);
```

## 3. Brittle Assertions (High)

Asserting on implementation details rather than observable behavior.

### Examples
```c
/* BAD: Asserts exact call count of internal function */
zassert_equal(internal_helper_fake.call_count, 3);

/* BAD: Asserts exact log message string */
zassert_str_equal(log_buffer, "Sensor initialized at 0x20001234");

/* BAD: Asserts exact timing (will flake) */
zassert_equal(elapsed_ms, 100);

/* GOOD: Assert on public API behavior */
zassert_equal(module_get_state(), STATE_READY);

/* GOOD: Assert within tolerance */
zassert_within(elapsed_ms, 100, 10, "timing outside tolerance");

/* GOOD: Assert on observable side effect */
zassert_true(output_buffer_has_data());
```

## 4. Test Logic Duplication (Critical)

Duplicating the module's algorithm in the test to compute expected values. If both have the same bug, the test passes incorrectly.

### Detection
Look for tests where the expected value is computed rather than hardcoded:

```c
/* BAD: Replicating the CRC algorithm in the test */
uint32_t expected_crc = compute_crc32(data, len);  /* same function! */
zassert_equal(module_crc(data, len), expected_crc);

/* GOOD: Known test vector from specification */
static const uint8_t test_data[] = {0x31, 0x32, 0x33};
zassert_equal(module_crc(test_data, 3), 0xCBF43926,
              "CRC32 of '123' must match IEEE 802.3 test vector");
```

### Fix
Use test vectors from specifications, datasheets, or reference implementations. When no specification exists, compute expected values by hand and document the calculation.

## 5. Missing Negative Tests (High)

Only testing happy paths. Error handling code is untested and often contains bugs (null pointer dereferences, resource leaks, incorrect error codes).

### Detection
For each public API function, count tests per return value:

```
sensor_mgr_init():
  ✓ returns 0 on success          (tested)
  ✗ returns -ENODEV when not ready (NOT tested)
  ✗ returns -EINVAL for null arg   (NOT tested)
  ✗ returns -EALREADY when reinit  (NOT tested)
```

### Fix
Write at least one test per documented error return:

```c
ZTEST(sensor_mgr, test_init_returns_enodev_when_device_not_ready)
{
    device_is_ready_fake.return_val = false;
    int ret = sensor_mgr_init();
    zassert_equal(ret, -ENODEV, "expected -ENODEV, got %d", ret);
}

ZTEST(sensor_mgr, test_init_returns_einval_for_null_config)
{
    int ret = sensor_mgr_init_with_config(NULL);
    zassert_equal(ret, -EINVAL, "expected -EINVAL for NULL config");
}
```

## 6. Flaky Timing Tests (Critical)

Tests using `k_sleep()` or fixed delays for synchronization. Pass on fast machines, fail on slow CI runners.

### Detection
```bash
grep -rn 'k_sleep\|k_msleep\|k_usleep\|k_busy_wait' tests/ --include='*.c'
```

Any `k_sleep` in test code is suspicious unless it's explicitly testing a delay feature.

### Fix
Replace sleep-based synchronization with event-based:

```c
/* BAD: Race condition */
start_async_operation();
k_sleep(K_MSEC(100));  /* hope it's done... */
zassert_true(operation_complete());

/* GOOD: Event-based synchronization */
static K_SEM_DEFINE(done_sem, 0, 1);

static void completion_callback(void) {
    k_sem_give(&done_sem);
}

ZTEST(async, test_operation_completes)
{
    start_async_operation(completion_callback);
    int ret = k_sem_take(&done_sem, K_MSEC(5000));
    zassert_equal(ret, 0, "operation timed out after 5 seconds");
    zassert_true(operation_complete());
}
```

## 7. Magic Numbers (Medium)

Hardcoded values in assertions without explanation.

```c
/* BAD: What is 42? Why 42? */
zassert_equal(result, 42);
zassert_equal(buffer_size, 1024);
zassert_equal(retry_count, 3);

/* GOOD: Named constants with meaning */
#define EXPECTED_DEFAULT_SAMPLE 42    /* Per BME280 datasheet table 4.3 */
#define MAX_PROTOCOL_PAYLOAD   1024   /* MTU - header (1280 - 256) */
#define MAX_RETRY_ATTEMPTS     3      /* As configured in Kconfig */

zassert_equal(result, EXPECTED_DEFAULT_SAMPLE,
              "default sample: got %d, expected %d per datasheet",
              result, EXPECTED_DEFAULT_SAMPLE);
```

## 8. Giant Test Functions (Medium)

Test functions exceeding ~40 lines with multiple unrelated assertions. When they fail, identifying which behavior broke requires reading the entire function.

### Detection
```bash
# Find test functions longer than 40 lines
awk '/^ZTEST/{start=NR} /^}/{if(start && NR-start>40) print FILENAME":"start" ("NR-start" lines)"; start=0}' tests/**/*.c
```

### Fix
Split into focused tests — one behavior per test function:

```c
/* BAD: Tests init AND read AND error handling in one function */
ZTEST(sensor, test_everything)
{
    /* 60 lines of init, read, error, cleanup... */
}

/* GOOD: One behavior per test */
ZTEST(sensor, test_init_succeeds_with_ready_device) { /* 8 lines */ }
ZTEST(sensor, test_init_fails_when_device_not_ready) { /* 6 lines */ }
ZTEST(sensor, test_read_returns_valid_sample) { /* 10 lines */ }
ZTEST(sensor, test_read_propagates_fetch_error) { /* 8 lines */ }
```

## 9. Commented-Out Tests (Medium)

Tests that are commented out "temporarily" and never re-enabled. They rot as the code evolves and become impossible to re-enable without major rewrites.

### Detection
```bash
grep -rn '// *ZTEST\|/\* *ZTEST\|#if 0.*test' tests/ --include='*.c'
```

### Fix
- **If the test is valid**: Fix it and re-enable
- **If the test is obsolete**: Delete it
- **If the test needs work**: Use `ztest_test_skip()` with a comment explaining why:

```c
ZTEST(network, test_mdns_discovery)
{
    ztest_test_skip(); /* TODO(#142): Requires mDNS mock - blocked on PR #141 */
}
```

## 10. No Teardown / Resource Leaks (High)

Tests that allocate resources (memory, threads, timers, semaphores) without cleaning up. Resource leaks accumulate and cause failures in later tests.

### Detection
Look for allocations in test code without corresponding frees:

```bash
grep -rn 'k_thread_create\|k_timer_start\|k_heap_alloc\|k_work_init' tests/ --include='*.c' | \
  while read line; do
    file=$(echo "$line" | cut -d: -f1)
    if ! grep -q 'k_thread_abort\|k_timer_stop\|k_heap_free\|k_work_cancel' "$file"; then
      echo "LEAK: $line"
    fi
  done
```

### Fix
Use `after` or `teardown` callbacks:

```c
static void after(void *f)
{
    struct my_fixture *fix = f;

    /* Stop any timers */
    k_timer_stop(&fix->poll_timer);

    /* Abort spawned threads */
    k_thread_abort(fix->worker_tid);

    /* Free allocated memory */
    if (fix->buffer) {
        k_heap_free(&test_heap, fix->buffer);
        fix->buffer = NULL;
    }

    /* Cancel pending work */
    k_work_cancel(&fix->async_work);
}
```

## Quick Reference: Anti-Pattern Checklist

Use this checklist during test review:

- [ ] Tests pass when shuffled (`CONFIG_ZTEST_SHUFFLE=y`)
- [ ] Mocks are only used for external dependencies, not internal functions
- [ ] Assertions check behavior, not implementation details
- [ ] Expected values are hardcoded from specs, not computed
- [ ] Every error return code has at least one test
- [ ] No `k_sleep()` used for synchronization (use semaphores/events)
- [ ] No magic numbers without named constants
- [ ] Each test function tests ONE behavior (<40 lines)
- [ ] No commented-out tests (delete or use `ztest_test_skip`)
- [ ] All resources allocated in tests are freed in `after`/`teardown`

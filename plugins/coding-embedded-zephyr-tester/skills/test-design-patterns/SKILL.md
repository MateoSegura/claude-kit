---
name: coding-embedded-zephyr-tester:test-design-patterns
description: "Test architecture patterns for Zephyr RTOS: test pyramid for embedded systems, test isolation strategies, fixture design, test naming conventions, parameterized tests, table-driven tests, test organization, anti-patterns, and flaky test prevention."
user-invocable: false
---

# Test Design Patterns for Embedded Systems

## Test Pyramid for Embedded

The test pyramid optimizes for fast feedback and maintainability:

```
         /\
        /  \        HIL (Hardware-in-the-loop)
       /    \       10% of tests
      /------\      Minutes to execute
     /        \     BabbleSim / Renode
    /          \    Multi-device, RF, analog
   /   QEMU    \   20% of tests
  /  Integration \  Seconds to execute
 /--------------\  Real kernel, emulated HW
/   native_sim    \ 70%+ of tests
/    Unit Tests    \ Sub-second execution
/___________________\ FFF mocks, pure logic
```

### Layer Rules

1. **native_sim unit tests** catch logic bugs, API contract violations, error handling gaps, and boundary conditions. They run in milliseconds and should cover the vast majority of code paths.

2. **QEMU integration tests** catch subsystem interaction bugs, timing issues, IPC race conditions, and architecture-specific behavior. They require the real Zephyr kernel but not real hardware.

3. **HIL tests** catch hardware interaction bugs, RF behavior, analog accuracy, and real-world timing. They require physical hardware and are the slowest tier.

**Push tests down the pyramid.** If a test CAN run on native_sim, it MUST run on native_sim. Moving tests up the pyramid increases execution time, flakiness, and maintenance cost.

## Test Isolation Strategies

### Isolation Principle

Every test must be independent. It must set up its own preconditions, execute the code under test, verify the results, and clean up -- without depending on any other test's execution or side effects.

### Isolation Techniques

#### 1. FFF Mock Isolation

Mock all external dependencies at the function level. Each test configures its own mock behavior and resets all mocks in the `before` function.

```c
static void before(void *f)
{
    /* Complete reset -- every test starts from a clean state */
    RESET_FAKE(dependency_a);
    RESET_FAKE(dependency_b);
    FFF_RESET_HISTORY();
}
```

#### 2. Fixture Isolation

Each test gets a fresh fixture initialized in `before`. Never carry state between tests via the fixture.

```c
static void before(void *f)
{
    struct my_fixture *fixture = f;
    memset(fixture, 0, sizeof(*fixture));
    /* Reinitialize any required state */
    fixture->config = default_config();
}
```

#### 3. Module Re-initialization

If the module under test has internal state, reinitialize it in `before`:

```c
static void before(void *f)
{
    /* Reset internal module state */
    module_deinit();
    module_init();
}
```

#### 4. Static Variable Isolation

Static variables inside the module under test are the enemy of test isolation. Prefer designs where state is held in a struct passed to the module's functions (dependency injection). If static state is unavoidable, provide a `_reset()` or `_deinit()` function for testing.

## Fixture Design Patterns

### Stateless Fixture (No setup/teardown)

For tests that need no shared state:

```c
ZTEST_SUITE(parser, NULL, NULL, NULL, NULL, NULL);

ZTEST(parser, test_parse_valid_input)
{
    /* Each test creates its own local data */
    uint8_t input[] = {0x01, 0x02, 0x03};
    struct parsed_result result;
    int ret = parse(input, sizeof(input), &result);
    zassert_equal(ret, 0, "parse failed: %d", ret);
}
```

### Per-Test Fixture (before/after only)

For tests that share a common setup pattern but no persistent resources:

```c
struct parser_fixture {
    uint8_t buffer[256];
    struct parser_ctx ctx;
};

static void *setup(void) {
    static struct parser_fixture f;
    return &f;
}

static void before(void *f) {
    struct parser_fixture *fix = f;
    memset(fix, 0, sizeof(*fix));
    parser_init(&fix->ctx);
}

ZTEST_SUITE(parser, NULL, setup, before, NULL, NULL);
```

### Resource Fixture (setup + teardown)

For tests that need expensive one-time resource allocation:

```c
struct network_fixture {
    struct net_context *ctx;
    struct sockaddr_in addr;
};

static void *setup(void)
{
    static struct network_fixture f;
    /* One-time: create network context */
    net_context_get(AF_INET, SOCK_STREAM, IPPROTO_TCP, &f.ctx);
    return &f;
}

static void teardown(void *f)
{
    struct network_fixture *fix = f;
    net_context_put(fix->ctx);
}

ZTEST_SUITE(network, NULL, setup, before, after, teardown);
```

## Test Naming Conventions

### Pattern: test_<module>_<behavior>_<outcome>

| Component | Description | Example |
|-----------|-------------|---------|
| module | Module or class being tested | `sensor_mgr` |
| behavior | What action or scenario | `init`, `read_with_null_ptr`, `concurrent_access` |
| outcome | Expected result | `succeeds`, `returns_einval`, `blocks_caller` |

### Examples

```c
/* Module: sensor_mgr */
test_sensor_mgr_init_succeeds_with_ready_device
test_sensor_mgr_init_returns_enodev_when_device_not_ready
test_sensor_mgr_read_returns_einval_for_null_pointer
test_sensor_mgr_read_returns_valid_sample_after_init
test_sensor_mgr_start_enables_periodic_sampling
test_sensor_mgr_stop_cancels_pending_work
test_sensor_mgr_concurrent_read_is_protected_by_mutex

/* Module: protocol_handler */
test_protocol_parse_valid_header_extracts_fields
test_protocol_parse_truncated_packet_returns_enodata
test_protocol_encode_respects_max_buffer_size
test_protocol_encode_empty_payload_produces_header_only
```

### Anti-Pattern Names

```c
/* BAD: too vague */
test_init
test_error
test_basic
test_functionality

/* BAD: implementation detail, not behavior */
test_calls_k_sem_take
test_sets_flag_to_true
test_increments_counter

/* BAD: compound (tests multiple things) */
test_init_and_start_and_read
```

## Parameterized / Table-Driven Tests

When testing the same logic with multiple inputs, use table-driven patterns:

### Basic Table-Driven Test

```c
struct test_vector {
    const char *name;
    int input;
    int expected;
};

static const struct test_vector vectors[] = {
    { "zero",     0,    0 },
    { "positive", 42,   42 },
    { "negative", -1,   -EINVAL },
    { "max",      INT_MAX, INT_MAX },
    { "overflow", INT_MAX + 1, -ERANGE },
};

ZTEST(math, test_process_table_driven)
{
    for (int i = 0; i < ARRAY_SIZE(vectors); i++) {
        int ret = process(vectors[i].input);
        zassert_equal(ret, vectors[i].expected,
                      "[%d] %s: got %d, expected %d",
                      i, vectors[i].name, ret, vectors[i].expected);
    }
}
```

### Buffer/Protocol Table-Driven Test

```c
struct packet_vector {
    const char *name;
    const uint8_t *input;
    size_t input_len;
    int expected_ret;
    uint8_t expected_type;
};

static const struct packet_vector packet_tests[] = {
    {
        .name = "valid_data_packet",
        .input = (uint8_t[]){0x01, 0x04, 0xDE, 0xAD, 0xBE, 0xEF},
        .input_len = 6,
        .expected_ret = 0,
        .expected_type = 0x01,
    },
    {
        .name = "truncated_header",
        .input = (uint8_t[]){0x01},
        .input_len = 1,
        .expected_ret = -ENODATA,
        .expected_type = 0,
    },
};
```

## Test Organization

### By Module (Recommended)

```
tests/
├── unit/
│   ├── sensor_mgr/          # Tests for src/sensor_mgr/
│   ├── protocol_handler/    # Tests for src/protocol/
│   └── storage/             # Tests for src/storage/
├── integration/
│   ├── sensor_pipeline/     # Sensor → processing → storage
│   └── network_stack/       # Network → protocol → transport
└── bluetooth/
    └── gatt_service/        # BLE GATT service tests
```

### Mirror Source Structure

Test directory structure should mirror the source directory structure. A developer looking at `src/sensor_mgr/` should know to find tests at `tests/unit/sensor_mgr/`.

## Anti-Patterns

### 1. Test Interdependence

Tests that pass in order but fail when shuffled. Caused by shared mutable state, missing mock resets, or relying on previous test's setup.

**Fix:** Reset all state in `before`. Enable `CONFIG_ZTEST_SHUFFLE=y` to detect.

### 2. Over-Mocking

Mocking everything, including the module under test's own internal functions. Tests become coupled to implementation details and break on every refactor.

**Fix:** Only mock at module boundaries (external dependencies). Test through the public API.

### 3. Brittle Assertions

Asserting on exact values that are implementation details (specific log messages, exact call counts for internal helpers, precise timing values).

**Fix:** Assert on observable behavior and public API contracts. Use `zassert_within` for timing.

### 4. Test Logic Duplication

Duplicating the module's logic in the test to compute the expected value. If both have the same bug, the test passes incorrectly.

**Fix:** Use hardcoded expected values from the specification or manual calculation.

### 5. Missing Negative Tests

Only testing happy paths. Error handling code is untested and often broken.

**Fix:** For every function, write at least one test per documented error return value.

### 6. Flaky Timing Tests

Tests using `k_sleep()` for synchronization. Pass on fast machines, fail on slow CI.

**Fix:** Use `k_sem_take()` with timeout, `k_event_wait()`, or `k_poll()`.

### 7. Magic Numbers

```c
/* BAD */
zassert_equal(result, 42);

/* GOOD */
#define EXPECTED_SAMPLE_VALUE 42
zassert_equal(result, EXPECTED_SAMPLE_VALUE,
              "sample value: got %d, expected %d",
              result, EXPECTED_SAMPLE_VALUE);
```

### 8. Giant Test Functions

A single test with 50+ lines and multiple unrelated assertions. When it fails, which assertion? What behavior broke?

**Fix:** Split into focused tests. One behavior per test.

### 9. Commented-Out Tests

Tests that are commented out "temporarily" and never re-enabled. They rot and become useless.

**Fix:** Delete or fix. Use `ztest_test_skip()` with a clear reason if temporarily skipping.

### 10. No Teardown

Tests that allocate resources (memory, threads, timers) without cleaning up. Causes resource leaks that affect subsequent tests.

**Fix:** Use `after` or `teardown` to release all resources.

## Flaky Test Prevention

### Root Causes and Fixes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Timing dependency | Passes locally, fails in CI | Replace `k_sleep` with event-based sync |
| Uninitialized memory | Random values between runs | `memset` in `before`, enable ASAN |
| Test order dependency | Fails when shuffled | Reset all state in `before` |
| Resource leak | Fails after N tests | Cleanup in `after`/`teardown` |
| Shared global state | Sporadic with parallel | Use fixture-scoped state |
| Float precision | Intermittent assertion fail | Use `zassert_within` with tolerance |

### Detection Strategy

1. Run with `CONFIG_ZTEST_SHUFFLE=y` and multiple seeds
2. Run with `--retry-failed 10` to detect intermittent failures
3. Run with `CONFIG_ASAN=y` to detect memory issues
4. Run with `CONFIG_UBSAN=y` to detect undefined behavior
5. Run in CI under load (parallel builds) to stress timing

### When a Flaky Test is Found

1. Quarantine it immediately (`quarantine.yaml`)
2. File a bug with reproduction steps
3. Root cause: timing, memory, or ordering?
4. Fix the root cause (not the symptom)
5. Verify with 100 consecutive runs before removing from quarantine

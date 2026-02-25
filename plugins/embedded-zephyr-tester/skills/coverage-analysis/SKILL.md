---
name: embedded-zephyr-tester:coverage-analysis
description: "Code coverage analysis patterns for Zephyr RTOS: twister --coverage workflows, gcov/lcov toolchain, coverage report interpretation, line/branch/function metrics, coverage thresholds for CI gates, identifying untested paths, coverage improvement strategies, and LCOV_EXCL patterns."
user-invocable: false
---

# Code Coverage Analysis for Zephyr

## Coverage Toolchain

Zephyr coverage uses GCC's gcov instrumentation compiled into the test binary, with lcov/genhtml for report generation.

### Toolchain Stack

```
Test binary (native_sim) → gcov instrumentation → .gcda/.gcno files → lcov → HTML/XML reports
```

- **gcov**: GCC's coverage profiling tool. Instruments code at compile time, records execution counts at runtime.
- **lcov**: Frontend for gcov. Aggregates `.gcda` files into a unified `coverage.info`.
- **genhtml**: Converts lcov info into browsable HTML reports.
- **gcovr**: Alternative to lcov. Supports XML (Cobertura), JSON, and HTML output.

### Requirements

```bash
# Ensure tools are installed
apt install lcov gcovr       # Debian/Ubuntu
brew install lcov gcovr      # macOS
```

## Generating Coverage Reports

### Basic Coverage Run

```bash
west twister -p native_sim -T tests/ --coverage
```

This:
1. Builds all tests with `-DCONFIG_COVERAGE=y -DCONFIG_COVERAGE_GCOV=y`
2. Executes tests on native_sim
3. Collects `.gcda` files from each test build directory
4. Runs lcov to generate `twister-out/coverage/coverage.info`
5. Runs genhtml to produce `twister-out/coverage/index.html`

### Coverage for Specific Module

```bash
west twister -p native_sim -T tests/unit/sensor_mgr/ --coverage --coverage-tool lcov
```

### Coverage with Specific Tool

```bash
# lcov (default)
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov

# gcovr (supports Cobertura XML for CI)
west twister -p native_sim -T tests/ --coverage --coverage-tool gcovr
```

### Manual Coverage (Without Twister)

```bash
# Build with coverage
west build -b native_sim tests/unit/sensor_mgr/ -- -DCONFIG_COVERAGE=y -DCONFIG_COVERAGE_GCOV=y

# Run the test
./build/zephyr/zephyr.exe

# Collect coverage
lcov --capture --directory build/ --output-file coverage.info

# Filter to application code only
lcov --extract coverage.info '*/src/*' --output-file app_coverage.info

# Generate HTML report
genhtml app_coverage.info --output-directory coverage_report/
```

## Coverage Metrics

### Line Coverage

Percentage of executable lines that were executed at least once during testing. This is the primary metric.

- **Target: 80%+** for application modules
- **Target: 90%+** for safety-critical modules
- **Acceptable: 60%+** for driver abstraction layers (hardware-dependent paths)

### Branch Coverage

Percentage of conditional branches (if/else, switch cases, ternary operators) where both true and false paths were exercised.

- **Target: 70%+** for application modules
- **Target: 85%+** for safety-critical modules
- Branch coverage is harder to achieve than line coverage because it requires testing both outcomes of every condition

### Function Coverage

Percentage of functions that were called at least once. Should approach 100% for public API functions.

- **Target: 95%+** for public API functions
- Static helper functions may have lower coverage if they handle rare error conditions

## Interpreting Coverage Reports

### HTML Report Navigation

```
twister-out/coverage/index.html
├── Directory listing (sorted by coverage %)
│   └── src/sensor_mgr/
│       ├── sensor_mgr.c    — 85% line, 72% branch
│       └── filter.c        — 62% line, 45% branch  ← needs attention
```

### Color Coding

- **Green (>=75%)**: Good coverage
- **Yellow (50-75%)**: Needs improvement
- **Red (<50%)**: Critical gap

### Per-Line Analysis

In the HTML report, each source line shows:
- **Execution count**: Number of times the line was executed
- **Branch markers**: `[+]` = taken, `[-]` = not taken

```
    12      10: if (dev == NULL) {              [+ taken] [- not taken]
    13       0:     LOG_ERR("device is NULL");
    14       0:     return -EINVAL;
    15         : }
```

Line 12 was executed 10 times, but only the true branch was taken. The false branch (dev != NULL error path) was never tested.

## Identifying Untested Paths

### High-Priority Gaps

1. **Error handling paths**: Functions that return error codes but the error return was never triggered in tests. These are the most dangerous gaps because untested error handlers often have bugs.

2. **Boundary conditions**: First/last element processing, empty collections, maximum buffer sizes, zero-length inputs.

3. **State machine transitions**: Untested state transitions, especially error-recovery transitions.

4. **Timeout paths**: Code that executes when a `k_sem_take()` or `k_msgq_get()` times out.

### Low-Priority Gaps (Often Acceptable)

1. **Platform-specific branches**: Code behind `IS_ENABLED(CONFIG_*)` that targets a different platform than native_sim.

2. **Debug/logging-only code**: `LOG_DBG` paths, diagnostic dump functions.

3. **Defensive unreachable code**: Default cases in switch statements that should never execute.

## Coverage Exclusions

### LCOV Exclusion Markers

Use sparingly and only for code that genuinely cannot be tested:

```c
/* LCOV_EXCL_START - ISR path requires hardware interrupt */
static void gpio_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
    k_work_submit(&process_work);
}
/* LCOV_EXCL_STOP */
```

Single-line exclusion:

```c
__ASSERT_NO_MSG(ptr != NULL); /* LCOV_EXCL_LINE - defensive assert */
```

### Valid Exclusion Reasons

- ISR handlers that require hardware triggers
- Platform-specific paths not reachable on native_sim
- Defensive assertions for programmer errors (not runtime failures)
- Boot/init code that runs before the test framework

### Invalid Exclusion Reasons (Do Not Exclude)

- Error handling paths (these MUST be tested via mocks)
- Complex conditional logic (these need branch coverage)
- Functions you do not know how to test (learn how or ask for help)

## Coverage Improvement Strategies

### Strategy 1: Mock-Driven Error Path Testing

For each uncovered error path, configure FFF mocks to return the error code that triggers it:

```c
/* Cover the "sensor_sample_fetch fails" path */
ZTEST(sensor_mgr, test_read_handles_fetch_failure)
{
    sensor_sample_fetch_fake.return_val = -EIO;
    int ret = sensor_mgr_read(&sample);
    zassert_equal(ret, -EIO, "expected -EIO propagation, got %d", ret);
}
```

### Strategy 2: Return Value Sequences

For multi-step operations where the Nth call fails:

```c
int return_seq[] = {0, 0, -ENOMEM};  /* succeed, succeed, then fail */
SET_RETURN_SEQ(k_heap_alloc_fake, return_seq, 3);
```

### Strategy 3: Table-Driven Boundary Tests

Cover all boundary conditions with a test vector table:

```c
static const struct test_vector boundary_vectors[] = {
    { .input = 0,           .expected = 0 },
    { .input = 1,           .expected = 1 },
    { .input = MAX_VALUE,   .expected = MAX_VALUE },
    { .input = MAX_VALUE+1, .expected = -EINVAL },
    { .input = -1,          .expected = -EINVAL },
};
```

### Strategy 4: State Machine Coverage

For modules with internal state machines, write tests that drive through every state transition:

```c
ZTEST(fsm, test_idle_to_running_transition)
{
    zassert_equal(get_state(), STATE_IDLE, "initial state wrong");
    start_module();
    zassert_equal(get_state(), STATE_RUNNING, "state after start wrong");
}

ZTEST(fsm, test_running_to_error_transition)
{
    start_module();
    inject_error();
    zassert_equal(get_state(), STATE_ERROR, "state after error wrong");
}
```

## CI Coverage Gates

### Threshold Checking Script

```bash
#!/bin/bash
# check-coverage-threshold.sh
THRESHOLD_LINE=80
THRESHOLD_BRANCH=70

LINE_COV=$(lcov --summary coverage.info 2>&1 | grep "lines" | grep -oP '[\d.]+%' | tr -d '%')
BRANCH_COV=$(lcov --summary coverage.info 2>&1 | grep "branches" | grep -oP '[\d.]+%' | tr -d '%')

if (( $(echo "$LINE_COV < $THRESHOLD_LINE" | bc -l) )); then
    echo "FAIL: Line coverage ${LINE_COV}% below threshold ${THRESHOLD_LINE}%"
    exit 1
fi

if (( $(echo "$BRANCH_COV < $THRESHOLD_BRANCH" | bc -l) )); then
    echo "FAIL: Branch coverage ${BRANCH_COV}% below threshold ${THRESHOLD_BRANCH}%"
    exit 1
fi

echo "PASS: Line ${LINE_COV}%, Branch ${BRANCH_COV}%"
```

### Coverage Trend Tracking

Store coverage metrics per commit to track trends:
- Coverage increase: good (new tests added)
- Coverage decrease: flag for review (new code without tests)
- Coverage unchanged: acceptable if no code changes

## Common Pitfalls

1. **Coverage only on native_sim**: Coverage instrumentation is only supported on native_sim (and host native builds). QEMU and hardware targets do not support gcov.

2. **Coverage inflation from test code**: By default, lcov includes test source files in coverage metrics. Filter to application code only: `lcov --extract coverage.info '*/src/*'`.

3. **Branch coverage from macros**: Zephyr macros like `LOG_ERR` and `IS_ENABLED` generate branches that inflate branch count. These are legitimate but may make 100% branch coverage unrealistic.

4. **Coverage reset between tests**: Each test binary starts with fresh counters. If you run multiple test binaries targeting the same source files, lcov merges their coverage data automatically.

5. **Stale .gcda files**: Old coverage data from previous runs can contaminate results. Use `--pristine` or `lcov --zerocounters` before coverage runs.

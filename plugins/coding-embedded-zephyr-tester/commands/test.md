---
name: coding-embedded-zephyr-tester:test
description: "Run Zephyr tests via twister with smart platform selection and result analysis"
allowed-tools: Read, Glob, Grep, Bash, Write
user-invocable: true
---

# Test

You orchestrate Zephyr test execution by selecting the right platform, running twister, parsing results, and triaging failures.

## Workflow

### Step 1: Determine Test Scope

Classify the user's request:

- **Run all tests** -> `west twister -T tests/ --integration`
- **Run unit tests** -> `west twister -p native_sim -T tests/unit/`
- **Run specific module tests** -> `west twister -p native_sim -T tests/unit/<module>/`
- **Run integration tests** -> `west twister -T tests/integration/ --integration`
- **Run BLE tests** -> `west twister -p nrf52_bsim -T tests/bluetooth/`
- **Run with coverage** -> Use `/coverage` command instead
- **Rerun failed tests** -> `west twister --retry-failed 3`

### Step 2: Discover Tests

Use Glob to find testcase.yaml files and understand what tests exist:

```
Glob(pattern: "tests/**/testcase.yaml")
```

Read testcase.yaml files to understand platform requirements and tags.

### Step 3: Select Platform

Choose the platform based on test type:

| Test Type | Platform | Reason |
|-----------|----------|--------|
| Unit tests | `native_sim` | Fastest, supports ASAN/coverage |
| Integration (kernel) | `qemu_cortex_m3` | Real ARM kernel |
| Integration (general) | `native_sim` | Speed over fidelity |
| BLE protocol | `nrf52_bsim` | BabbleSim required |
| Hardware tests | Board-specific | `--device-testing` required |

### Step 4: Execute Tests

Run twister with appropriate flags:

```bash
# Basic run
west twister -p <platform> -T <test-path>

# With verbose output for failure diagnosis
west twister -p <platform> -T <test-path> -v

# With sanitizers for bug detection
west twister -p native_sim -T <test-path> --extra-args="CONFIG_ASAN=y"

# Detect flaky tests
west twister -p <platform> -T <test-path> --retry-failed 3
```

### Step 5: Parse and Report Results

After twister completes:

1. Check exit code (0 = all pass)
2. Read `twister-out/twister.log` for summary
3. For failures, read individual test logs: `twister-out/<platform>/<test>/handler.log`
4. Classify each failure:
   - **Assertion failure**: Read the message, identify root cause
   - **Build failure**: Check CMakeLists.txt, prj.conf, Kconfig dependencies
   - **Timeout**: Check for blocking operations, missing mock triggers
   - **Crash**: Check for NULL pointers, stack overflow, enable ASAN

### Step 6: Present Results

Format results as:

```
## Test Results

### Summary
- Total: N tests
- Passed: N
- Failed: N
- Skipped: N
- Duration: Xs

### Failures (if any)
| Test | Platform | Type | Details |
|------|----------|------|---------|
| sensor_mgr.unit.test_read | native_sim | assertion | Expected 0, got -EIO |

### Failure Analysis
[For each failure, provide root cause analysis and suggested fix]
```

## Quick Reference

```bash
# Unit tests (fast)
west twister -p native_sim -T tests/unit/

# All tests (CI mode)
west twister -T tests/ --integration

# Single test verbose
west twister -p native_sim -s tests/unit/sensor_mgr/sensor_mgr.unit -v

# With ASAN
west twister -p native_sim -T tests/ --extra-args="CONFIG_ASAN=y"

# Shuffle to detect order dependence
west twister -p native_sim -T tests/ --extra-args="CONFIG_ZTEST_SHUFFLE=y"

# Hardware testing
west twister --device-testing --hardware-map hw-map.yaml -T tests/hil/
```

## Error Handling

- **No testcase.yaml found** -> Inform user, suggest `/scaffold-tests` to create test infrastructure
- **Build failure** -> Read build log, identify missing CONFIG or include
- **All tests skipped** -> Check platform_allow in testcase.yaml matches selected platform
- **Twister not found** -> Check that west and Zephyr environment are set up

---
name: embedded-zephyr-tester:twister-workflows
description: "Twister test runner patterns: CLI usage, platform selection, testcase.yaml specification, quarantine lists, hardware maps, CI integration, JUnit/coverage report generation, and filter expressions for Zephyr RTOS test execution."
user-invocable: false
---

# Twister Test Runner Workflows

Twister is Zephyr's official test runner. It discovers tests via `testcase.yaml` files, builds them for target platforms, executes them (natively, via QEMU, or on hardware), and reports results in JUnit XML, JSON, and coverage formats.

## Core Concepts

### Test Discovery

Twister discovers tests by recursively scanning for `testcase.yaml` files under the specified test root(s). Each `testcase.yaml` defines one or more test scenarios with their platform requirements, tags, and configuration.

### Platform Selection

Platforms are boards/emulators that twister can build and run tests on:

- **native_sim**: Host-native execution. Fastest. Primary target for unit tests.
- **qemu_cortex_m3**: QEMU-emulated ARM Cortex-M3. For integration tests needing ARM architecture.
- **qemu_cortex_m0**: QEMU-emulated ARM Cortex-M0. For testing on constrained targets.
- **qemu_x86**: QEMU-emulated x86. For architecture-independent tests.
- **nrf52_bsim**: BabbleSim-based nRF52. For BLE protocol tests.
- **Device boards**: Real hardware via `--device-testing` and `--hardware-map`.

### Test Lifecycle

For each test scenario + platform combination, twister:
1. Creates a build directory
2. Runs CMake configuration with platform and test-specific overlays
3. Builds the test binary
4. Executes the binary (native, QEMU, or flash + serial)
5. Captures output and parses for PASS/FAIL/SKIP
6. Records results

## testcase.yaml Specification

### Minimal Example

```yaml
tests:
  sensor_mgr.unit:
    platform_allow: native_sim
    tags: unit sensor
```

### Full Specification

```yaml
common:
  # Shared settings inherited by all tests in this file
  tags: sensor
  timeout: 60
  min_ram: 32
  min_flash: 64

tests:
  sensor_mgr.unit:
    platform_allow: native_sim
    tags: unit sensor
    integration_platforms:
      - native_sim
    timeout: 30
    harness: ztest
    extra_args: CONF_FILE=prj.conf
    extra_configs:
      - CONFIG_ZTEST_SHUFFLE=y
      - CONFIG_ASAN=y

  sensor_mgr.integration:
    platform_allow:
      - native_sim
      - qemu_cortex_m3
    platform_exclude:
      - qemu_x86
    tags: integration sensor
    integration_platforms:
      - qemu_cortex_m3
    timeout: 120
    extra_configs:
      - CONFIG_TEST_INTEGRATION=y
    filter: CONFIG_SENSOR and CONFIG_I2C
    depends_on: i2c gpio

  sensor_mgr.hil:
    platform_allow:
      - nrf52840dk/nrf52840
      - nucleo_f411re
    tags: hil sensor slow
    harness: ztest
    timeout: 300
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `platform_allow` | list/string | Only build/run on these platforms |
| `platform_exclude` | list/string | Never build/run on these platforms |
| `tags` | string | Space-separated tags for filtering |
| `integration_platforms` | list | Platforms to test in `--integration` mode |
| `timeout` | int | Test timeout in seconds (default: 60) |
| `harness` | string | Test harness type: `ztest`, `console`, `bsim`, `pytest` |
| `extra_args` | string | Extra CMake arguments |
| `extra_configs` | list | Kconfig overlays appended to prj.conf |
| `extra_conf_files` | list | Additional .conf files to merge |
| `extra_overlay_confs` | list | Additional overlay .conf files |
| `filter` | string | Kconfig expression that must evaluate true |
| `depends_on` | string | Space-separated hardware features required |
| `min_ram` | int | Minimum RAM in KB |
| `min_flash` | int | Minimum flash in KB |
| `build_only` | bool | Build but do not execute |
| `skip` | bool | Skip this test entirely |
| `slow` | bool | Mark as slow test |

## Platform Selection Strategy

### For Unit Tests

```yaml
platform_allow: native_sim
integration_platforms:
  - native_sim
```

Native_sim provides the fastest execution and supports coverage, ASAN, and UBSAN. All unit tests should target native_sim exclusively.

### For Integration Tests

```yaml
platform_allow:
  - native_sim
  - qemu_cortex_m3
integration_platforms:
  - qemu_cortex_m3
```

Start with native_sim for speed, add QEMU targets when ARM-specific behavior matters.

### For BLE Tests

```yaml
platform_allow: nrf52_bsim
integration_platforms:
  - nrf52_bsim
harness: bsim
```

BabbleSim tests require the bsim harness for multi-device coordination.

### For Hardware Tests

```yaml
platform_allow:
  - nrf52840dk/nrf52840
  - nucleo_f411re
tags: hil
harness: ztest
```

Hardware tests only run with `--device-testing` and a matching hardware map.

## Common Twister Workflows

### Local Development

```bash
# Run single test suite on native_sim
west twister -p native_sim -T tests/unit/sensor_mgr/

# Run all unit tests
west twister -p native_sim -T tests/unit/

# Run with verbose output for debugging
west twister -p native_sim -T tests/unit/sensor_mgr/ -v

# Run specific test by name
west twister -p native_sim -s tests/unit/sensor_mgr/sensor_mgr.unit
```

### Coverage Analysis

```bash
# Generate coverage report
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov

# Coverage report location
ls twister-out/coverage/
```

### CI Pipeline

```bash
# Full integration run with JUnit output
west twister -T tests/ --integration -O ci-results/
# JUnit XML: ci-results/twister.xml

# Parallelized across CI workers (4 shards)
west twister -T tests/ --integration --subset 1/4
west twister -T tests/ --integration --subset 2/4
west twister -T tests/ --integration --subset 3/4
west twister -T tests/ --integration --subset 4/4
```

### Failure Recovery

```bash
# Retry failed tests (detect flaky)
west twister -T tests/ --retry-failed 3

# Re-run only failed tests from previous run
west twister --load-tests twister-out/testplan.json --retry-failed 3
```

### Device Testing

```bash
# With hardware map
west twister --device-testing --hardware-map hw-map.yaml -T tests/hil/

# Hardware map format (hw-map.yaml):
# - platform: nrf52840dk/nrf52840
#   id: 000683456789
#   serial: /dev/ttyACM0
#   runner: nrfjprog
```

## Filter Expressions

Twister filter expressions use Kconfig symbols and Python-like boolean logic:

```yaml
filter: CONFIG_SENSOR and CONFIG_I2C
filter: CONFIG_BT and not CONFIG_BT_CTLR
filter: CONFIG_ARCH_POSIX or CONFIG_SOC_SERIES_NRF52X
filter: dt_compat_enabled("bosch,bme280")
filter: dt_chosen_enabled("zephyr,console")
```

## Quarantine Lists

Quarantine known-flaky or known-broken tests without removing them:

```yaml
# quarantine.yaml
- scenarios:
    - sensor_mgr.integration.timing
  platforms:
    - qemu_cortex_m3
  comment: "Flaky timing in QEMU, tracked in ISSUE-123"

- scenarios:
    - ble_service.connection
  comment: "Known BabbleSim instability on CI, ISSUE-456"
```

Usage:

```bash
west twister -T tests/ --quarantine-list quarantine.yaml
```

Quarantined tests are built but their failures do not count toward the overall result. They appear in reports as "quarantined."

## Report Formats

### JUnit XML

Generated automatically at `twister-out/twister.xml`. Compatible with Jenkins, GitHub Actions, GitLab CI, and most CI dashboards.

### JSON Test Plan

`twister-out/testplan.json` contains the full test plan with per-test results, timing, and log paths. Used for `--load-tests` re-runs.

### Coverage Reports

With `--coverage --coverage-tool lcov`:
- `twister-out/coverage/coverage.info` -- LCOV info file
- `twister-out/coverage/index.html` -- HTML coverage report

## CLI Reference

See [twister-cli-reference.md](twister-cli-reference.md) for the complete flag reference.

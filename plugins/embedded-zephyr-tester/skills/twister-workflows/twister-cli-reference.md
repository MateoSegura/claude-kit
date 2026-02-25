# Twister CLI Reference

Complete reference for `west twister` (or `scripts/twister`) command-line flags.

## Test Selection

### -T, --testsuite-root

Specify one or more directories to scan for `testcase.yaml` files.

```bash
west twister -T tests/unit/
west twister -T tests/unit/ -T tests/integration/
```

### -s, --test

Run a specific test scenario by its full qualified name.

```bash
west twister -s tests/unit/sensor_mgr/sensor_mgr.unit
```

### -t, --tag

Filter tests by tag.

```bash
west twister -t unit                    # Only tests tagged 'unit'
west twister -t unit -t sensor          # Tests tagged both 'unit' AND 'sensor'
```

### -e, --exclude-tag

Exclude tests with specified tag.

```bash
west twister -e slow                    # Exclude slow tests
west twister -e hil -e flaky            # Exclude HIL and flaky
```

### --test-config

Specify a test configuration file (alternative to testcase.yaml discovery).

## Platform Selection

### -p, --platform

Target platform(s). Can be specified multiple times.

```bash
west twister -p native_sim
west twister -p native_sim -p qemu_cortex_m3
```

### --all

Build/run on all applicable platforms (based on testcase.yaml filters).

### --integration

Run on integration_platforms defined in testcase.yaml. Standard CI mode.

```bash
west twister -T tests/ --integration
```

### --platform-reports

Generate per-platform summary reports.

## Build Options

### --build-only

Build tests but do not execute them.

```bash
west twister -T tests/ --build-only
```

### --pristine, -z

Force pristine build (delete build directory first).

### --extra-args

Pass extra CMake arguments.

```bash
west twister -p native_sim -T tests/ --extra-args="CONFIG_ASAN=y"
```

### --overflow-as-errors

Treat memory overflow warnings as errors.

## Execution Options

### -v, --verbose

Verbose output. Shows test output as it runs.

### --retry-failed

Retry failed tests N times (for flaky test detection).

```bash
west twister -T tests/ --retry-failed 3
```

### --retry-interval

Delay in seconds between retries (default: 60).

### --timeout-multiplier

Multiply all test timeouts by this factor.

```bash
west twister -T tests/ --timeout-multiplier 2    # Double all timeouts
```

### -j, --jobs

Number of parallel build/execute jobs.

```bash
west twister -T tests/ -j 8
```

### --short

Only run the first scenario per testcase.yaml. Fast smoke test.

## Device Testing

### --device-testing

Enable device (hardware) testing mode.

```bash
west twister --device-testing --hardware-map hw-map.yaml -T tests/hil/
```

### --hardware-map

Path to hardware map YAML file.

```yaml
# hw-map.yaml
- platform: nrf52840dk/nrf52840
  id: "000683456789"
  serial: /dev/ttyACM0
  runner: nrfjprog
  baud: 115200

- platform: nucleo_f411re
  id: "0672FF535155878267251839"
  serial: /dev/ttyACM1
  runner: openocd
```

### --west-runner

Override the west runner for flashing.

```bash
west twister --device-testing --west-runner jlink
```

### --west-flash

Extra flags to pass to `west flash`.

```bash
west twister --device-testing --west-flash="--verify"
```

## Coverage

### --coverage

Enable code coverage instrumentation and reporting.

```bash
west twister -p native_sim -T tests/ --coverage
```

### --coverage-tool

Select coverage tool: `lcov` (default) or `gcovr`.

```bash
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov
```

### --coverage-basedir

Base directory for coverage paths (default: ZEPHYR_BASE).

### --coverage-formats

Output formats for coverage report.

```bash
west twister --coverage --coverage-formats html,xml
```

## Output and Reporting

### -O, --outdir

Output directory for results (default: `twister-out`).

```bash
west twister -T tests/ -O ci-results/
```

### --report-dir

Directory for generated reports.

### --report-name

Prefix for report filenames.

### --report-summary

Print summary of test results to stdout.

### --report-excluded

Include excluded/skipped tests in the report.

## Filtering

### --quarantine-list

Path to quarantine YAML file.

```bash
west twister -T tests/ --quarantine-list quarantine.yaml
```

### --quarantine-verify

Only run quarantined tests (to check if they are still flaky).

```bash
west twister -T tests/ --quarantine-list quarantine.yaml --quarantine-verify
```

### --changed-only

Only run tests affected by changed files (requires git).

### --filter

Additional filter expression (appended to testcase.yaml filters).

```bash
west twister --filter "CONFIG_SENSOR"
```

## Parallelization / Sharding

### --subset

Run a subset of tests for CI parallelization.

```bash
# Split across 4 CI workers
west twister --subset 1/4    # Worker 1
west twister --subset 2/4    # Worker 2
west twister --subset 3/4    # Worker 3
west twister --subset 4/4    # Worker 4
```

### --load-tests

Load test plan from a previous run's JSON file.

```bash
west twister --load-tests twister-out/testplan.json
```

## Environment

### --zephyr-base

Override ZEPHYR_BASE path.

### --toolchain

Specify toolchain (zephyr, gnuarmemb, etc.).

### --board-root

Additional board root directories.

## Examples

### Developer Workflow

```bash
# Quick unit test run
west twister -p native_sim -T tests/unit/ -v

# Run with ASAN for memory bug detection
west twister -p native_sim -T tests/unit/ --extra-args="CONFIG_ASAN=y"

# Shuffle test order to detect interdependence
west twister -p native_sim -T tests/unit/ --extra-args="CONFIG_ZTEST_SHUFFLE=y"
```

### CI Workflow

```bash
# Full integration run
west twister -T tests/ --integration -O ci-results/ -j $(nproc)

# With coverage gate
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov -O ci-results/

# Quarantine flaky tests
west twister -T tests/ --integration --quarantine-list quarantine.yaml -O ci-results/
```

### Hardware Testing

```bash
# Single board
west twister --device-testing --hardware-map hw-map.yaml -p nrf52840dk/nrf52840 -T tests/hil/

# All available boards
west twister --device-testing --hardware-map hw-map.yaml -T tests/hil/
```

### Debug a Failing Test

```bash
# Run single test with verbose output
west twister -p native_sim -s tests/unit/sensor_mgr/sensor_mgr.unit -v

# Check build log
cat twister-out/native_sim/tests/unit/sensor_mgr/sensor_mgr.unit/handler.log

# Build manually for GDB debugging
cd twister-out/native_sim/tests/unit/sensor_mgr/sensor_mgr.unit/
west build -t run  # or ./zephyr/zephyr.exe directly on native_sim
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 2 | Error in twister itself (bad arguments, etc.) |

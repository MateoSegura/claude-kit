# Zephyr Test Code Standards

Detailed style guide for all test code: ztest suites, FFF mock configurations, testcase.yaml files, test overlays, and test Kconfig.

## Test File Structure

### Directory Layout

```
tests/
├── unit/
│   └── sensor_mgr/
│       ├── CMakeLists.txt
│       ├── prj.conf
│       ├── testcase.yaml
│       └── src/
│           ├── main.c           # ZTEST_SUITE + test cases
│           └── mock_drivers.h   # FFF mock declarations
├── integration/
│   └── data_pipeline/
│       ├── CMakeLists.txt
│       ├── prj.conf
│       ├── testcase.yaml
│       ├── boards/
│       │   └── native_sim.overlay
│       └── src/
│           └── main.c
└── bluetooth/
    └── gatt_service/
        ├── CMakeLists.txt
        ├── prj.conf
        ├── testcase.yaml
        └── src/
            └── main.c
```

### Test Source File Template

```c
/* 1. Zephyr test framework header */
#include <zephyr/ztest.h>

/* 2. FFF framework (if using mocks) */
#include <zephyr/fff.h>
DEFINE_FFF_GLOBALS;

/* 3. Module under test */
#include "sensor_mgr.h"

/* 4. Mock declarations */
#include "mock_drivers.h"

/* 5. Logging for test diagnostics */
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(test_sensor_mgr, LOG_LEVEL_DBG);

/* 6. Test fixture (if needed) */
struct sensor_mgr_fixture {
	struct sensor_sample sample;
	int init_result;
};

/* 7. Fixture lifecycle */
static void *sensor_mgr_setup(void)
{
	static struct sensor_mgr_fixture fixture;
	return &fixture;
}

static void sensor_mgr_before(void *f)
{
	struct sensor_mgr_fixture *fixture = f;
	memset(fixture, 0, sizeof(*fixture));
	/* Reset all FFF mocks */
	RESET_FAKE(sensor_sample_fetch);
	RESET_FAKE(sensor_channel_get);
	FFF_RESET_HISTORY();
}

static void sensor_mgr_after(void *f)
{
	ARG_UNUSED(f);
	/* Additional cleanup if needed */
}

/* 8. Suite registration */
ZTEST_SUITE(sensor_mgr, NULL, sensor_mgr_setup, sensor_mgr_before,
	    sensor_mgr_after, NULL);

/* 9. Test cases */
ZTEST_F(sensor_mgr, test_init_succeeds_with_ready_device)
{
	/* Arrange */
	/* ... */

	/* Act */
	int ret = sensor_mgr_init();

	/* Assert */
	zassert_equal(ret, 0, "init returned %d, expected 0", ret);
}
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Test directory | `tests/<type>/<module>/` | `tests/unit/sensor_mgr/` |
| Test source file | `main.c` or `test_<module>.c` | `main.c` |
| Test suite name | `<module_name>` | `sensor_mgr` |
| Test function | `test_<module>_<behavior>_<outcome>` | `test_sensor_mgr_init_returns_zero` |
| Test fixture struct | `<module>_fixture` | `struct sensor_mgr_fixture` |
| Mock header | `mock_<dependency>.h` | `mock_drivers.h` |
| FFF fake name | matches original function | `sensor_sample_fetch` (FFF wraps it) |
| testcase.yaml ID | `<module>.<type>` | `sensor_mgr.unit` |

### Test Function Naming Rules

The name must describe: **what is being tested**, **what scenario/input**, and **what is expected**.

```c
/* GOOD: Clear what is tested, the scenario, and expected result */
ZTEST(sensor_mgr, test_init_succeeds_with_ready_device)
ZTEST(sensor_mgr, test_init_fails_when_device_not_ready)
ZTEST(sensor_mgr, test_read_returns_einval_for_null_pointer)
ZTEST(sensor_mgr, test_start_enables_periodic_sampling)
ZTEST(sensor_mgr, test_stop_cancels_pending_work)

/* BAD: Vague, no scenario or expected result */
ZTEST(sensor_mgr, test_init)
ZTEST(sensor_mgr, test_read)
ZTEST(sensor_mgr, test_error)
ZTEST(sensor_mgr, test_basic)
```

## Assertion Patterns

### Always Include Diagnostic Messages

```c
/* GOOD: Message helps diagnose failure in CI logs */
zassert_equal(ret, 0, "sensor_init returned %d, expected 0", ret);
zassert_not_null(dev, "DEVICE_DT_GET returned NULL for sensor node");
zassert_true(device_is_ready(dev), "device %s is not ready", dev->name);
zassert_mem_equal(buf, expected, len, "buffer mismatch at offset within %zu bytes", len);

/* BAD: No context when assertion fails */
zassert_equal(ret, 0);
zassert_not_null(dev);
zassert_true(device_is_ready(dev));
```

### Assertion Selection Guide

| Scenario | Assertion | Example |
|----------|-----------|---------|
| Integer equality | `zassert_equal` | `zassert_equal(ret, -EINVAL, "expected -EINVAL, got %d", ret)` |
| Boolean true | `zassert_true` | `zassert_true(is_initialized, "module not initialized")` |
| Boolean false | `zassert_false` | `zassert_false(is_running, "module should be stopped")` |
| Pointer not NULL | `zassert_not_null` | `zassert_not_null(ptr, "allocation returned NULL")` |
| Pointer is NULL | `zassert_is_null` | `zassert_is_null(ptr, "expected NULL after free")` |
| Memory comparison | `zassert_mem_equal` | `zassert_mem_equal(a, b, len, "buffers differ")` |
| Value within range | `zassert_within` | `zassert_within(val, expected, tolerance, "val %d outside tolerance", val)` |
| String equality | `zassert_str_equal` | `zassert_str_equal(name, "sensor0", "wrong name: %s", name)` |
| Unreachable code | `zassert_unreachable` | `zassert_unreachable("should not reach this branch")` |

### Arrange-Act-Assert Pattern

Every test body follows AAA structure with clear section comments:

```c
ZTEST_F(sensor_mgr, test_read_returns_valid_sample)
{
	/* Arrange: configure mock to return known value */
	struct sensor_value mock_val = { .val1 = 25, .val2 = 500000 };
	sensor_channel_get_fake.custom_fake = fake_channel_get_temperature;

	/* Act: call the function under test */
	struct sensor_sample result;
	int ret = sensor_mgr_read(&result);

	/* Assert: verify return value and output */
	zassert_equal(ret, 0, "read returned %d", ret);
	zassert_equal(result.temperature.val1, 25,
		      "temperature val1: got %d, expected 25",
		      result.temperature.val1);
}
```

## FFF Mock Conventions

### Mock Declaration Pattern

```c
/* In mock_drivers.h */
#include <zephyr/fff.h>
#include <zephyr/drivers/sensor.h>

/* Declare fakes for sensor driver API */
FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);
FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
		enum sensor_channel, struct sensor_value *);

/* Declare fakes for kernel APIs if needed */
FAKE_VALUE_FUNC(int, k_sem_take, struct k_sem *, k_timeout_t);
FAKE_VOID_FUNC(k_sem_give, struct k_sem *);
```

### Mock Reset Rules

1. **Always reset in `before` function** (per-test setup):
   ```c
   static void suite_before(void *f)
   {
       RESET_FAKE(sensor_sample_fetch);
       RESET_FAKE(sensor_channel_get);
       FFF_RESET_HISTORY();
   }
   ```

2. **Never reset in test body** -- that is the fixture's job.

3. **Reset ALL fakes**, not just the ones used in the current test. A previous test may have configured a fake that bleeds into the next test.

### Custom Fake Pattern

```c
/* For complex return behavior, use custom_fake */
static int fake_channel_get_temperature(const struct device *dev,
					enum sensor_channel chan,
					struct sensor_value *val)
{
	if (chan == SENSOR_CHAN_AMBIENT_TEMP) {
		val->val1 = 25;
		val->val2 = 500000;
		return 0;
	}
	return -ENOTSUP;
}

/* In test setup or test body */
sensor_channel_get_fake.custom_fake = fake_channel_get_temperature;
```

## testcase.yaml Standards

### Minimal Required Fields

```yaml
tests:
  sensor_mgr.unit:
    platform_allow: native_sim
    tags: unit sensor
    integration_platforms:
      - native_sim
```

### Full Example with Common Fields

```yaml
tests:
  sensor_mgr.unit:
    platform_allow: native_sim
    tags: unit sensor
    integration_platforms:
      - native_sim
    timeout: 30
    harness: ztest

  sensor_mgr.integration:
    platform_allow:
      - native_sim
      - qemu_cortex_m3
    tags: integration sensor
    integration_platforms:
      - qemu_cortex_m3
    timeout: 60
    extra_configs:
      - CONFIG_TEST_INTEGRATION=y

  sensor_mgr.ble:
    platform_allow: nrf52_bsim
    tags: bluetooth sensor
    integration_platforms:
      - nrf52_bsim
    timeout: 120
    harness: bsim
```

### Tag Conventions

| Tag | Meaning |
|-----|---------|
| `unit` | Unit test, runs on native_sim |
| `integration` | Integration test, may need QEMU |
| `bluetooth` | BLE test, needs BabbleSim |
| `hil` | Hardware-in-the-loop, needs device |
| `slow` | Takes >30s, may be excluded from fast CI |
| `flaky` | Known intermittent, quarantine candidate |

## CMakeLists.txt for Tests

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(test_sensor_mgr)

# Test sources
target_sources(app PRIVATE
	src/main.c
)

# Include path for module under test
target_include_directories(app PRIVATE
	${CMAKE_SOURCE_DIR}/../../../src/sensor_mgr/include
)

# Link module under test (if building as library)
# target_link_libraries(app PRIVATE sensor_mgr)
```

## Test prj.conf Standards

```ini
# ---- Test Framework ----
CONFIG_ZTEST=y
CONFIG_ZTEST_NEW_API=y

# ---- Logging (useful for test diagnostics) ----
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3

# ---- Coverage (enable for native_sim coverage runs) ----
# CONFIG_COVERAGE=y
# CONFIG_COVERAGE_GCOV=y

# ---- Module dependencies ----
CONFIG_SENSOR=y
```

## MISRA C:2012 in Test Code

Test code follows the same MISRA subset as production code, with these practical relaxations:

- **Rule 11.5 (void pointer cast):** Allowed in fixture functions where `void *f` is cast to the fixture struct type. This is inherent to the ztest fixture API.
- **Rule 17.7 (unused return value):** Still enforced. Always check return values, even in test setup code.
- All other required rules from the production coding standards apply without exception.

# Zephyr RTOS Coding Standards

Detailed style guide for all C17 code, devicetree overlays, Kconfig files, and CMake configurations in Zephyr projects.

## C Code Style

### Formatting

- **Indentation:** Tabs (8-character width), consistent with Zephyr upstream kernel style.
- **Braces:** K&R style. Opening brace on the same line as the statement, closing brace on its own line. Exception: function definitions place the opening brace on the next line.
- **Line length:** 100 characters maximum. Break long lines at logical boundaries (after commas, before operators).
- **Blank lines:** One blank line between functions. Two blank lines between major sections (includes, defines, types, functions). No trailing whitespace.

```c
/* K&R braces for control flow */
if (ret < 0) {
	LOG_ERR("failed to initialize sensor: %d", ret);
	return ret;
}

/* Function definitions: opening brace on next line */
int sensor_subsystem_init(const struct device *dev)
{
	/* ... */
}
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case`, prefixed with module name | `sensor_mgr_start()` |
| Local variables | `snake_case` | `sample_count` |
| Global variables | `snake_case`, prefixed with module name | `sensor_mgr_state` (avoid globals; use module-scoped statics) |
| Macros | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Constants | `SCREAMING_SNAKE_CASE` | `DEFAULT_SAMPLE_INTERVAL_MS` |
| Enum values | `SCREAMING_SNAKE_CASE`, prefixed with type name | `SENSOR_STATE_IDLE` |
| Struct types | `snake_case` with `struct` keyword | `struct sensor_config` |
| Typedefs | Avoid for structs (Zephyr convention). Use only for function pointers | `typedef void (*sensor_cb_t)(...)` |
| Kconfig symbols | `CONFIG_APP_<MODULE>_<FEATURE>` | `CONFIG_APP_SENSOR_SAMPLE_RATE` |

### Include Ordering

Includes are grouped and ordered as follows, with a blank line between groups:

```c
/* 1. Zephyr kernel and subsystem headers */
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

/* 2. Zephyr library headers */
#include <zephyr/sys/util.h>
#include <zephyr/sys/byteorder.h>

/* 3. Application headers */
#include "sensor_mgr.h"
#include "app_config.h"
```

### Header Guards

Use `#ifndef` / `#define` guards. The guard symbol follows the pattern `MODULE_NAME_H_` with a trailing underscore:

```c
#ifndef SENSOR_MGR_H_
#define SENSOR_MGR_H_

#ifdef __cplusplus
extern "C" {
#endif

/* ... declarations ... */

#ifdef __cplusplus
}
#endif

#endif /* SENSOR_MGR_H_ */
```

### Documentation

Every public API function MUST have a Doxygen comment:

```c
/**
 * @brief Start periodic sensor sampling.
 *
 * Configures the sensor for continuous mode and begins pushing
 * samples to the registered callback at the configured interval.
 *
 * @param dev Pointer to the sensor device. Must be ready (device_is_ready()).
 * @param interval_ms Sampling interval in milliseconds. Must be >= 10.
 *
 * @retval 0 on success.
 * @retval -EINVAL if dev is NULL or interval_ms < 10.
 * @retval -EIO if sensor communication fails.
 * @retval -EALREADY if sampling is already active.
 */
int sensor_mgr_start(const struct device *dev, uint32_t interval_ms);
```

Static (file-scoped) functions: a brief one-line comment is sufficient.

## Error Handling

### Return Convention

All fallible functions return `int` with negative `errno` values on failure and `0` on success. Data-returning functions pass output through pointer parameters:

```c
int sensor_mgr_read(const struct device *dev, struct sensor_sample *out)
{
	if (dev == NULL || out == NULL) {
		return -EINVAL;
	}

	if (!device_is_ready(dev)) {
		LOG_ERR("sensor device not ready");
		return -ENODEV;
	}

	int ret = sensor_sample_fetch(dev);
	if (ret < 0) {
		LOG_ERR("sample fetch failed: %d", ret);
		return ret;
	}

	/* ... populate out ... */
	return 0;
}
```

### Logging Before Returning

Every error return path MUST log the error with `LOG_ERR()` before returning, including the errno value and enough context to diagnose the failure without a debugger:

```c
/* GOOD */
LOG_ERR("i2c_write to addr 0x%02x failed: %d", cfg->i2c_addr, ret);
return ret;

/* BAD -- silent failure */
return ret;
```

### Device Acquisition Pattern

Always use this three-step pattern to acquire a device pointer:

```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(my_sensor));

if (dev == NULL) {
	LOG_ERR("device pointer is NULL");
	return -ENODEV;
}

if (!device_is_ready(dev)) {
	LOG_ERR("device %s is not ready", dev->name);
	return -ENODEV;
}
```

Never use the deprecated `device_get_binding()` function. `DEVICE_DT_GET()` is resolved at compile time and produces a link error if the device does not exist, which is better than a runtime `NULL` return.

## ISR Constraints

Code running in interrupt context has strict limitations:

### Allowed in ISRs
- `k_sem_give()` -- wake a waiting thread
- `k_work_submit()` / `k_work_submit_to_queue()` -- defer processing
- `k_msgq_put()` with `K_NO_WAIT` -- non-blocking enqueue
- `k_event_set()` -- signal an event
- `LOG_INF()` and family (deferred mode) -- logs are queued, not printed
- `gpio_pin_set_dt()` -- direct hardware manipulation

### Forbidden in ISRs
- `k_mutex_lock()` -- can block, causes undefined behavior
- `k_sem_take()` with timeout -- can block
- `k_msgq_put()` with timeout -- can block
- `k_sleep()` / `k_msleep()` -- blocks the interrupt context
- `k_malloc()` / `k_heap_alloc()` -- heap operations are not ISR-safe
- `printk()` -- blocks on UART output in most backends

### ISR Duration Target

All ISR code must complete within 10us on the target platform. If processing takes longer, capture the data in the ISR and defer processing to a work queue:

```c
static void sensor_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	/* Capture timestamp and submit work -- do NOT process data here */
	app_data.timestamp = k_uptime_get_32();
	k_work_submit(&app_data.process_work);
}
```

## Devicetree Overlay Standards

### Comment Requirements

Every property in an overlay MUST have a comment explaining WHY it is set:

```dts
/* Use SPI3 for the IMU because SPI0/1 are occupied by flash and display */
&spi3 {
	status = "okay";

	/* CS on P0.28 -- directly wired to IMU pin 5 per schematic rev C */
	cs-gpios = <&gpio0 28 GPIO_ACTIVE_LOW>;

	imu: imu@0 {
		compatible = "bosch,bmi270";
		reg = <0>;

		/* 8MHz is the max SPI clock per BMI270 datasheet Table 98 */
		spi-max-frequency = <8000000>;

		/* INT1 on P0.03 -- active high, push-pull per schematic */
		int1-gpios = <&gpio0 3 GPIO_ACTIVE_HIGH>;
	};
};
```

### Overlay Scope

- Board-specific overlays go in `boards/<board>.overlay` (e.g., `boards/nrf52dk_nrf52832.overlay`).
- Application-wide hardware descriptions that apply to ALL boards do NOT exist -- if it is hardware-specific, it is board-specific. Period.
- Never modify a board's default `.dts` file in the Zephyr tree. Always use overlays.

## Kconfig Standards

### Application Kconfig File

Define application-specific symbols in a `Kconfig` file at the application root:

```kconfig
menu "Application Configuration"

config APP_SENSOR_SAMPLE_RATE_MS
	int "Sensor sampling interval in milliseconds"
	default 100
	range 10 60000
	help
	  Interval between sensor readings. Lower values increase
	  power consumption. Minimum 10ms due to sensor settling time.

config APP_SENSOR_ENABLE_FILTERING
	bool "Enable moving average filter on sensor data"
	default y
	help
	  Applies a moving average filter to smooth sensor readings.
	  Adds ~200 bytes of RAM for the filter buffer.

endmenu
```

### prj.conf Style

Group related symbols with section comments. Add explanatory comments for non-obvious choices:

```ini
# ---- Logging ----
CONFIG_LOG=y
CONFIG_LOG_MODE_DEFERRED=y
# Buffer 1024 bytes to avoid dropped messages during burst logging
CONFIG_LOG_BUFFER_SIZE=1024

# ---- Bluetooth ----
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
# Need 2 connections: phone + gateway
CONFIG_BT_MAX_CONN=2

# ---- Power Management ----
CONFIG_PM=y
CONFIG_PM_DEVICE=y
CONFIG_PM_DEVICE_RUNTIME=y
```

### IS_ENABLED Usage in C

```c
/* GOOD: IS_ENABLED works in regular if-statements, compiler eliminates dead code */
if (IS_ENABLED(CONFIG_APP_SENSOR_ENABLE_FILTERING)) {
	apply_filter(&sample);
}

/* BAD: preprocessor spaghetti, typos compile silently */
#ifdef CONFIG_APP_SENSOR_ENABLE_FLTERING  /* <-- typo, compiles fine, filter never applied */
	apply_filter(&sample);
#endif
```

## CMakeLists.txt Structure

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)

# Application sources -- one target_sources per module for clarity
target_sources(app PRIVATE
	src/main.c
)

# Modular subsystems as Zephyr libraries
zephyr_library_named(sensor_mgr)
zephyr_library_sources(
	src/sensor_mgr/sensor_mgr.c
	src/sensor_mgr/filter.c
)
zephyr_library_include_directories(src/sensor_mgr/include)

# Conditional compilation tied to Kconfig
zephyr_library_sources_ifdef(CONFIG_APP_SENSOR_ENABLE_FILTERING
	src/sensor_mgr/moving_avg.c
)
```

## MISRA C:2012 Subset

The following MISRA C:2012 Required rules are enforced. These are the subset most relevant to Zephyr embedded development:

- **Rule 8.4:** A compatible declaration shall be visible when a function/object with external linkage is defined.
- **Rule 10.4:** Both operands of an operator with usual arithmetic conversions shall have the same essential type category.
- **Rule 11.3:** A cast shall not be performed between a pointer to object type and a pointer to a different object type (use `CONTAINER_OF()` for legitimate upcasts).
- **Rule 12.2:** The right-hand operand of a shift operator shall be non-negative and less than the width of the promoted left-hand operand.
- **Rule 14.4:** The controlling expression of an `if`, `while`, `for`, or `do...while` shall have essentially Boolean type.
- **Rule 15.7:** All `if...else if` constructs shall be terminated with an `else` statement.
- **Rule 17.7:** The value returned by a function having non-void return type shall be used.
- **Rule 21.3:** The memory allocation functions `malloc`, `calloc`, `realloc`, and `free` shall not be used (use `k_heap_alloc` instead).

These rules are advisory, not blocking, in existing code. Enforced as hard requirements in new code.

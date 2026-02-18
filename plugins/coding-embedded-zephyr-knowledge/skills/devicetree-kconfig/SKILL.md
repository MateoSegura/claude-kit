---
name: devicetree-kconfig
description: Zephyr devicetree and Kconfig unified configuration — DTS syntax, overlays, bindings, Kconfig symbols, dependencies, and auto-enable strategies
user-invocable: false
---

# Devicetree and Kconfig Quick Reference

Zephyr uses two complementary configuration systems:
- **Devicetree (DTS)**: Hardware description — peripherals, pins, memory, clocks
- **Kconfig**: Software configuration — feature enablement, buffer sizes, stack sizes

## Devicetree Node Syntax

```dts
/* Node with label and unit-address */
&i2c0 {
    status = "okay";
    clock-frequency = <100000>;

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
        status = "okay";
    };
};

/* GPIO LED definition */
/ {
    leds {
        compatible = "gpio-leds";
        led0: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
            label = "Green LED";
        };
    };
};
```

**Key concepts:**
- `&i2c0` — Reference to existing node via label
- `bme280:` — Node label for C code reference
- `bme280@76` — Node name with unit-address (I2C address)
- `compatible` — Matches to binding file
- `reg` — Unit address (bus-specific: I2C address, memory address, etc.)
- `status` — "okay" or "disabled"

## Devicetree Overlays

**Application overlay:** `boards/<board>.overlay` or `app.overlay`

```dts
/* nrf52840dk_nrf52840.overlay */
&i2c0 {
    status = "okay";
    /* I2C configuration... */
};

/* Disable unused peripheral */
&uart1 {
    status = "disabled";
};
```

**Build-time overlay:** Pass via `EXTRA_DTC_OVERLAY_FILE` or `DTC_OVERLAY_FILE`.

```bash
west build -b nrf52840dk_nrf52840 -- -DDTC_OVERLAY_FILE="boards/custom.overlay"
```

**Overlay precedence:** Later overlays override earlier ones.

## Common Devicetree Macros in C

```c
#include <zephyr/devicetree.h>

/* Get device from nodelabel */
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));

/* Get property value */
#define I2C_ADDR DT_REG_ADDR(DT_NODELABEL(bme280))

/* Check if node exists and is enabled */
#if DT_NODE_HAS_STATUS(DT_NODELABEL(bme280), okay)
    /* ... */
#endif

/* GPIO spec from devicetree */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);

/* Iterate instances of a compatible */
#define SENSOR_INIT(node_id) \
    DEVICE_DT_GET(node_id),

const struct device *sensors[] = {
    DT_FOREACH_STATUS_OKAY(bosch_bme280, SENSOR_INIT)
};
```

**Critical:** `DT_*` macros are evaluated at compile time. Results are constants.

## Devicetree Bindings

**Location:** `dts/bindings/*.yaml` in Zephyr tree or application.

**Example binding:**

```yaml
# dts/bindings/sensor/bosch,bme280.yaml
description: Bosch BME280 humidity and pressure sensor

compatible: "bosch,bme280"

include: [sensor-device.yaml, i2c-device.yaml]

properties:
  standby-time:
    type: int
    enum: [0, 1, 2, 3, 4, 5, 6, 7]
    default: 5
    description: Standby time between measurements
```

**Key fields:**
- `compatible` — String matched from DTS
- `include` — Inherit properties from other bindings
- `properties` — Valid properties for this node type
- `bus` — Parent bus type (i2c, spi, etc.)

## Kconfig Configuration Files

### prj.conf (project configuration)

```kconfig
# Enable subsystems
CONFIG_I2C=y
CONFIG_SENSOR=y
CONFIG_BME280=y

# Configure behavior
CONFIG_MAIN_STACK_SIZE=2048
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3

# Networking
CONFIG_NETWORKING=y
CONFIG_NET_IPV4=y
CONFIG_NET_TCP=y
```

**Format:** `CONFIG_<SYMBOL>=<value>`

**Value types:**
- Boolean: `y` (enabled) or `n` (disabled)
- Integer: `2048`
- String: `"value"`
- Hex: `0x1000`

### Board-specific configuration

**File:** `boards/<board>.conf`

```kconfig
# Automatically merged if board matches
CONFIG_BOARD_SPECIFIC_OPTION=y
```

### Multiple configuration fragments

```bash
# Merge multiple .conf files
west build -b board -- -DEXTRA_CONF_FILE="debug.conf;network.conf"
```

## Auto-Enable Strategy

**Goal:** Minimize explicit configuration. Enable dependencies automatically.

### DTS-driven auto-enable

When a devicetree node has `status = "okay"`:
1. Zephyr finds matching binding via `compatible`
2. Binding may include `bus: i2c` → auto-enables `CONFIG_I2C=y`
3. Driver Kconfig uses `select` to enable dependencies

**Example from driver Kconfig:**

```kconfig
config BME280
    bool "BME280 sensor"
    default y
    depends on DT_HAS_BOSCH_BME280_ENABLED
    depends on I2C
    select SENSOR
    help
      Enable BME280 driver
```

**Key mechanisms:**
- `default y` — Enabled by default
- `depends on DT_HAS_BOSCH_BME280_ENABLED` — Only visible if DT node exists with `status="okay"`
- `depends on I2C` — Requires I2C
- `select SENSOR` — Automatically enables SENSOR framework

**Result:** Adding BME280 node to DTS with `status="okay"` automatically enables driver if dependencies met.

## Kconfig Symbol Types

```kconfig
config EXAMPLE_BOOL
    bool "Example boolean option"
    default n

config EXAMPLE_INT
    int "Example integer"
    range 1 100
    default 10

config EXAMPLE_HEX
    hex "Example hex value"
    default 0x1000

config EXAMPLE_STRING
    string "Example string"
    default "value"

choice EXAMPLE_CHOICE
    prompt "Select mode"
    default MODE_A

config MODE_A
    bool "Mode A"

config MODE_B
    bool "Mode B"

endchoice
```

## Checking Configuration in Code

```c
#include <zephyr/autoconf.h>

#if IS_ENABLED(CONFIG_SENSOR)
    /* Sensor code... */
#endif

#define BUFFER_SIZE CONFIG_MAIN_STACK_SIZE

#if defined(CONFIG_LOG_DEFAULT_LEVEL)
    /* Logging configured */
#endif
```

**IS_ENABLED()** evaluates to 1 if symbol is `y`, 0 otherwise. Works with compiler dead-code elimination.

## Common DTS Properties

| Property | Type | Description |
|----------|------|-------------|
| `compatible` | string-array | Binding match key |
| `status` | string | "okay" or "disabled" |
| `reg` | array | Register address/size or bus address |
| `interrupts` | array | Interrupt specifier |
| `clocks` | phandle-array | Clock references |
| `gpios` | phandle-array | GPIO pin specifications |
| `label` | string | Human-readable name (deprecated) |

## Devicetree Chosen Nodes

**Purpose:** Select specific nodes for system use.

```dts
/ {
    chosen {
        zephyr,console = &uart0;
        zephyr,shell-uart = &uart0;
        zephyr,bt-c2h-uart = &uart1;
        zephyr,flash = &flash0;
        zephyr,code-partition = &slot0_partition;
    };
};
```

**Access in C:**

```c
#if DT_NODE_HAS_CHOSEN(zephyr_flash)
    const struct device *flash = DEVICE_DT_GET(DT_CHOSEN(zephyr_flash));
#endif
```

## Common Configuration Patterns

### Enable logging with custom level

```kconfig
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3    # 0=OFF, 1=ERR, 2=WRN, 3=INF, 4=DBG
CONFIG_LOG_MODE_DEFERRED=y    # Async logging (default)
CONFIG_LOG_BUFFER_SIZE=2048
```

### Enable shell for debugging

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_KERNEL_SHELL=y
CONFIG_DEVICE_SHELL=y
```

### Optimize for size

```kconfig
CONFIG_SIZE_OPTIMIZATIONS=y
CONFIG_LOG=n
CONFIG_PRINTK=n
CONFIG_ASSERT=n
```

### Enable BLE

```kconfig
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="MyDevice"
CONFIG_BT_MAX_CONN=1
```

## Additional resources

- For complete DTS syntax, node patterns, phandles, bindings format, and macro reference, see [dts-syntax-reference.md](dts-syntax-reference.md)
- For Kconfig dependency resolution, sysbuild configuration, menuconfig usage, and subsystem enablement recipes, see [kconfig-patterns.md](kconfig-patterns.md)

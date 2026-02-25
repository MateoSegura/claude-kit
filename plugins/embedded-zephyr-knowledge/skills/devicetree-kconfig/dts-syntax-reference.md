# Devicetree Syntax — Complete Reference

## Node Structure

```dts
[label:] node-name[@unit-address] {
    [properties]
    [child nodes]
};
```

### Example

```dts
i2c0: i2c@40003000 {
    compatible = "nordic,nrf-twim";
    reg = <0x40003000 0x1000>;
    interrupts = <3 1>;
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;
    clock-frequency = <100000>;

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};
```

**Parts:**
- `i2c0:` — Label for references
- `i2c` — Node name (generic component type)
- `@40003000` — Unit address (must match first `reg` entry)
- `bme280@76` — Child node with I2C address 0x76

## Property Types

### Strings

```dts
compatible = "bosch,bme280";
label = "Temperature Sensor";
```

### String Arrays

```dts
compatible = "gpio-leds", "simple-bus";
```

### Integers (32-bit cells)

```dts
clock-frequency = <100000>;
reg = <0x40003000 0x1000>;  /* address, size */
interrupts = <3 1>;         /* irq-number, priority */
```

**Multi-cell:** Use `<value1 value2 ...>`.

### Boolean (Presence)

```dts
i2c-master;   /* Present = true */
/* Absent = false */
```

### Byte Arrays

```dts
local-mac-address = [00 11 22 33 44 55];
```

### Phandles (Node References)

```dts
interrupt-parent = <&gic>;
clocks = <&sysclk>;
gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
```

**Format:** `<&label>`

### Phandle Arrays

```dts
/* <phandle cell1 cell2 ...> */
gpios = <&gpio0 13 GPIO_ACTIVE_LOW>, <&gpio1 14 GPIO_ACTIVE_HIGH>;

/* With named cells (from binding) */
pwms = <&pwm0 0 PWM_MSEC(20) PWM_POLARITY_NORMAL>;
       /* &pwm0 = phandle, 0 = channel, 20ms period, normal polarity */
```

## Node References

### By Label

```dts
&uart0 {
    status = "okay";
    current-speed = <115200>;
};
```

### By Path

```dts
&{/soc/uart@40002000} {
    status = "okay";
};
```

**Rare usage.** Prefer labels.

## Root Node

```dts
/ {
    model = "Nordic nRF52840 DK";
    compatible = "nordic,nrf52840-dk-nrf52840";

    chosen {
        zephyr,console = &uart0;
        zephyr,shell-uart = &uart0;
        zephyr,sram = &sram0;
        zephyr,flash = &flash0;
        zephyr,code-partition = &slot0_partition;
    };

    aliases {
        led0 = &led0;
        sw0 = &button0;
    };
};
```

**Special nodes:**
- `chosen` — System-selected nodes
- `aliases` — Short names for common nodes

## Overlays

**Purpose:** Modify or extend base devicetree without editing board files.

### Application Overlay

**File:** `boards/<board>.overlay` or `app.overlay`

```dts
/* Enable I2C and add sensor */
&i2c0 {
    status = "okay";
    clock-frequency = <400000>;  /* Override to 400kHz */

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};

/* Disable unused UART */
&uart1 {
    status = "disabled";
};

/* Modify existing node */
&led0 {
    gpios = <&gpio0 12 GPIO_ACTIVE_HIGH>;  /* Change pin */
};
```

### Deleting Nodes and Properties

```dts
/* Delete a property */
&i2c0 {
    /delete-property/ clock-frequency;
};

/* Delete a child node */
&i2c0 {
    /delete-node/ sensor@77;
};
```

## Address Cells and Size Cells

```dts
soc {
    #address-cells = <1>;  /* Address is 1 cell (32-bit) */
    #size-cells = <1>;     /* Size is 1 cell */

    uart0: uart@40002000 {
        reg = <0x40002000 0x1000>;
        /*      ^address   ^size  */
    };
};

i2c0 {
    #address-cells = <1>;
    #size-cells = <0>;     /* No size component */

    sensor@76 {
        reg = <0x76>;      /* Just address */
    };
};
```

**Rule:** `#address-cells` and `#size-cells` in parent define format of child `reg` properties.

## Common Devicetree Bindings

### GPIO LEDs

```dts
/ {
    leds {
        compatible = "gpio-leds";
        led0: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
            label = "Green LED";
        };
        led1: led_1 {
            gpios = <&gpio0 14 GPIO_ACTIVE_LOW>;
            label = "Red LED";
        };
    };
};
```

**Access:**

```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);
```

### GPIO Keys (Buttons)

```dts
/ {
    buttons {
        compatible = "gpio-keys";
        button0: button_0 {
            gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
            label = "Push button 0";
        };
    };
};
```

### SPI Device

```dts
&spi1 {
    status = "okay";
    cs-gpios = <&gpio0 17 GPIO_ACTIVE_LOW>;

    spi_device: spi-dev@0 {
        compatible = "vendor,device";
        reg = <0>;  /* Chip select index */
        spi-max-frequency = <8000000>;
    };
};
```

### I2C Device

```dts
&i2c0 {
    status = "okay";

    sensor: sensor@68 {
        compatible = "invensense,mpu6050";
        reg = <0x68>;
        int-gpios = <&gpio0 25 GPIO_ACTIVE_HIGH>;
    };
};
```

### Fixed Partitions (Flash Layout)

```dts
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x00000000 0x0000C000>;
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0x0000C000 0x00076000>;
        };
        slot1_partition: partition@82000 {
            label = "image-1";
            reg = <0x00082000 0x00076000>;
        };
        storage_partition: partition@f8000 {
            label = "storage";
            reg = <0x000f8000 0x00008000>;
        };
    };
};
```

### PWM

```dts
&pwm0 {
    status = "okay";
    pinctrl-0 = <&pwm0_default>;
    pinctrl-names = "default";
};

/ {
    pwmleds {
        compatible = "pwm-leds";
        pwm_led0: pwm_led_0 {
            pwms = <&pwm0 0 PWM_MSEC(20) PWM_POLARITY_NORMAL>;
            label = "PWM LED 0";
        };
    };
};
```

## Devicetree Macros

### Node Identification

```c
/* By nodelabel */
#define SENSOR_NODE DT_NODELABEL(bme280)

/* By alias */
#define LED_NODE DT_ALIAS(led0)

/* By chosen */
#define FLASH_NODE DT_CHOSEN(zephyr_flash)

/* By path */
#define I2C_NODE DT_PATH(soc, i2c_40003000)

/* By compatible (single instance) */
#define BME_NODE DT_INST(0, bosch_bme280)
```

### Property Access

```c
/* Get property value */
#define I2C_ADDR DT_PROP(SENSOR_NODE, reg)

/* Get property or default */
#define CLK_FREQ DT_PROP_OR(SENSOR_NODE, clock_frequency, 100000)

/* Check if property exists */
#if DT_NODE_HAS_PROP(SENSOR_NODE, interrupts)
    /* Has interrupt */
#endif

/* String property */
#define LABEL DT_PROP(SENSOR_NODE, label)

/* Array property length */
#define NUM_GPIOS DT_PROP_LEN(LED_NODE, gpios)

/* Array element by index */
#define FIRST_GPIO DT_PROP_BY_IDX(LED_NODE, gpios, 0)
```

### Device Access

```c
/* Get device pointer */
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(bme280));

/* Check if device exists */
#if DT_NODE_EXISTS(DT_NODELABEL(bme280))
    /* Node defined */
#endif

/* Check if enabled */
#if DT_NODE_HAS_STATUS(DT_NODELABEL(bme280), okay)
    /* Node enabled */
#endif
```

### GPIO Spec

```c
/* Get GPIO spec from DT */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios);

/* By index if multiple */
static const struct gpio_dt_spec led1 = GPIO_DT_SPEC_GET_BY_IDX(DT_NODELABEL(leds), gpios, 1);

/* Check if defined */
if (!gpio_is_ready_dt(&led)) {
    return -ENODEV;
}
```

### Iteration

```c
/* Iterate all instances of a compatible */
#define INIT_SENSOR(node_id) \
    { .dev = DEVICE_DT_GET(node_id) },

static struct {
    const struct device *dev;
} sensors[] = {
    DT_FOREACH_STATUS_OKAY(bosch_bme280, INIT_SENSOR)
};

/* Iterate child nodes */
#define INIT_LED(node_id) \
    GPIO_DT_SPEC_GET(node_id, gpios),

static const struct gpio_dt_spec leds[] = {
    DT_FOREACH_CHILD(DT_PATH(leds), INIT_LED)
};
```

### Register Address and IRQ

```c
/* Register base address */
#define UART_BASE DT_REG_ADDR(DT_NODELABEL(uart0))

/* Register size */
#define UART_SIZE DT_REG_SIZE(DT_NODELABEL(uart0))

/* Multiple register blocks */
#define CTRL_BASE DT_REG_ADDR_BY_IDX(node, 0)
#define DATA_BASE DT_REG_ADDR_BY_IDX(node, 1)

/* IRQ number */
#define UART_IRQ DT_IRQN(DT_NODELABEL(uart0))

/* IRQ priority */
#define UART_IRQ_PRIO DT_IRQ(DT_NODELABEL(uart0), priority)
```

### Phandle Reference

```c
/* Get referenced node */
#define CLK_NODE DT_PHANDLE(DT_NODELABEL(uart0), clocks)

/* Get cell value from phandle-array */
#define PWM_CHANNEL DT_PWMS_CHANNEL(DT_NODELABEL(pwm_led0))
#define PWM_PERIOD DT_PWMS_PERIOD(DT_NODELABEL(pwm_led0))
```

### Existence Checks

```c
#if DT_NODE_EXISTS(DT_NODELABEL(sensor))
    /* Node defined in devicetree */
#endif

#if DT_NODE_HAS_STATUS(DT_NODELABEL(sensor), okay)
    /* Node enabled */
#endif

#if DT_NODE_HAS_COMPAT(node, bosch_bme280)
    /* Node has this compatible */
#endif

#if DT_HAS_COMPAT_STATUS_OKAY(bosch_bme280)
    /* At least one instance of this compatible is enabled */
#endif
```

## Binding File Format

**Location:** `dts/bindings/` in Zephyr or app.

### Example Binding

```yaml
# dts/bindings/sensor/bosch,bme280.yaml

description: Bosch BME280 humidity and pressure sensor

compatible: "bosch,bme280"

include: [sensor-device.yaml, i2c-device.yaml]

properties:
  standby-time:
    type: int
    required: false
    enum: [0, 1, 2, 3, 4, 5, 6, 7]
    default: 5
    description: |
      Standby time between measurements in normal mode.
      0 = 0.5ms, 1 = 62.5ms, ..., 7 = 20ms

  filter-coefficient:
    type: int
    required: false
    enum: [0, 1, 2, 3, 4]
    default: 0
    description: IIR filter coefficient

child-binding:
  description: Child sensor configuration
  properties:
    oversampling:
      type: int
      required: true
```

### Binding Property Types

| Type | Description | Example |
|------|-------------|---------|
| `int` | Integer | `<100000>` |
| `boolean` | Presence flag | `i2c-master;` |
| `string` | String | `"value"` |
| `string-array` | Array of strings | `"a", "b"` |
| `uint8-array` | Byte array | `[01 02 03]` |
| `phandle` | Single reference | `<&gpio0>` |
| `phandle-array` | Multiple references | `<&gpio0 13 0>` |
| `path` | Node path | `"/soc/i2c@0"` |
| `compound` | Complex structure | (custom) |

### Include Directive

```yaml
include: [base.yaml, i2c-device.yaml]
```

Inherits properties and child-bindings from included files.

### Bus Property

```yaml
bus: i2c
```

Specifies parent bus type. Enables bus-specific macros.

## Pinctrl (Pin Control)

**Zephyr 3.x+ pattern for SoC pin muxing.**

```dts
/* Define pin configurations */
&pinctrl {
    uart0_default: uart0_default {
        group1 {
            psels = <NRF_PSEL(UART_TX, 0, 6)>,
                    <NRF_PSEL(UART_RX, 0, 8)>;
        };
    };

    uart0_sleep: uart0_sleep {
        group1 {
            psels = <NRF_PSEL(UART_TX, 0, 6)>,
                    <NRF_PSEL(UART_RX, 0, 8)>;
            low-power-enable;
        };
    };
};

/* Reference in peripheral */
&uart0 {
    status = "okay";
    pinctrl-0 = <&uart0_default>;
    pinctrl-1 = <&uart0_sleep>;
    pinctrl-names = "default", "sleep";
};
```

**SoC-specific.** Check board `.dts` files for examples.

## Best Practices

1. **Use nodelabels, not node names.** Labels are stable across DTS changes.
2. **Check device_is_ready()** before using `DEVICE_DT_GET()` devices.
3. **Prefer overlays over editing board files.** Keep board files pristine.
4. **Use `status = "disabled"` to disable, not deletion.** Easier to re-enable.
5. **Match unit-address to first reg entry.** Build will warn otherwise.
6. **Use compatible from existing bindings.** Check `dts/bindings/` for standard bindings.
7. **Test with `ninja devicetree_check`** to validate DTS before full build.
8. **Use `DT_HAS_COMPAT_STATUS_OKAY()` for conditional compilation** when driver may not be present.

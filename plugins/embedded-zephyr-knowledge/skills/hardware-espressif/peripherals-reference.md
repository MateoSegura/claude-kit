# ESP32 Peripherals Reference

## Peripheral Availability Matrix

| Peripheral | ESP32 | ESP32-S2 | ESP32-S3 | ESP32-C3 | ESP32-C6 | ESP32-H2 |
|-----------|-------|----------|----------|----------|----------|----------|
| **SPI (GP use)** | 2 (SPI2/3) | 2 (SPI2/3) | 2 (SPI2/3) | 1 (SPI2) | 1 (SPI2) | 1 (SPI2) |
| **SPI (host/flash)** | SPI0+1 (internal) | SPI0+1 | SPI0+1 | SPI0+1 | SPI0+1 | SPI0+1 |
| **I2C** | 2 | 2 | 2 | 1 | 2 | 2 |
| **UART** | 3 (UART0-2) | 2 | 3 | 2 | 3 | 3 |
| **I2S** | 2 | 1 | 2 (+ LCD mode) | 1 | 1 | 1 |
| **ADC** | 18 ch, 2 SAR | 20 ch, 2 SAR | 20 ch, 2 SAR | 6 ch, 1 SAR | 7 ch, 1 SAR | 5 ch, 1 SAR |
| **DAC** | 2 ch (8-bit) | 2 ch (8-bit) | None | None | None | None |
| **LEDC (PWM)** | 16 ch (HI+LO) | 8 ch | 8 ch | 6 ch | 6 ch | 6 ch |
| **MCPWM** | 2 units | None | 2 units | None | 1 unit | 1 unit |
| **PCNT** | 8 units | 4 units | 8 units | 4 units | 4 units | 4 units |
| **RMT** | 8 ch (TX+RX) | 4 ch | 8 ch | 4 ch | 4 ch | 4 ch |
| **TWAI (CAN)** | 1 | 1 | 1 | 1 | 1 | 1 |
| **SDIO/SD** | SDMMC (1-4 bit) | None | SDMMC (1-4 bit) | None | None | None |
| **USB OTG** | None | USB 1.1 FS | USB 1.1 FS | None (Serial/JTAG) | None (Serial/JTAG) | None |
| **USB Serial/JTAG** | None | Yes | Yes | Yes | Yes | None |
| **Ethernet** | MAC (ext PHY) | None | None | None | None | None |
| **LCD/Camera** | Camera + LCD | LCD (parallel) | Camera + LCD | None | None | None |
| **Touch** | 10 ch | 14 ch | 14 ch | None | None | None |
| **Temp sensor** | None | Yes | Yes | Yes | Yes | Yes |
| **IEEE 802.15.4** | None | None | None | None | Yes | Yes |
| **CRC/SHA/AES HW** | Yes | Yes | Yes | Yes | Yes | Yes |
| **RSA HW** | 4096-bit | 4096-bit | 4096-bit | 3072-bit | 3072-bit | 3072-bit |
| **ECDSA HW** | None | None | None | None | Yes | Yes |

### Notes on LEDC

LEDC is the primary general-purpose PWM controller on all ESP32 variants. On ESP32 original, LEDC has two speed groups (high-speed and low-speed, 8 channels each = 16 total). On S2/S3/Cx variants there is only one group (8 or 6 channels). Timer resolution is configurable from 1 to 20 bits; at 80 MHz APB clock, a 10-bit timer gives ~78 kHz PWM frequency.

### Notes on MCPWM

MCPWM (Motor Control PWM) provides advanced PWM with dead-time insertion, fault detection, and capture inputs. It is suited for brushless motor control (BLDC/PMSM), DC motor H-bridge control, and servo pulse generation. Available only on ESP32, ESP32-S3, ESP32-C6, and ESP32-H2.

### Notes on TWAI

TWAI (Two-Wire Automotive Interface) is Espressif's CAN-compatible controller. It implements ISO 11898-1 (CAN 2.0B) at data rates up to 1 Mbit/s. Requires an external CAN transceiver (e.g., SN65HVD230, TJA1050). TWAI does NOT implement CAN FD.

---

## GPIO Matrix

### What the GPIO Matrix Does

The GPIO matrix is a programmable crossbar switch between peripheral signal inputs/outputs and physical GPIO pads. Almost every digital peripheral signal can be routed to any GPIO pad — not just dedicated pins.

**How it works:**
1. Each GPIO pad can be configured to output a peripheral signal (e.g., SPI MOSI, I2C SDA)
2. Each GPIO pad input is sampled and can be forwarded to a peripheral input (e.g., UART RX)
3. The matrix holds configuration registers for each signal pair

**Exceptions — pin-fixed signals:**
- ADC/DAC/touch: Analog signals bypass the GPIO matrix entirely. Each ADC channel maps to exactly one physical pin.
- SPI flash/PSRAM: The internal flash SPI controller (SPI0/SPI1) uses fixed pins — you cannot reroute them.
- High-speed SPI master (ESP32 only): When SPI2 or SPI3 is in full-duplex fast mode (>26 MHz), the matrix is bypassed and pins are dedicated.

### Strapping Pins

Strapping pins are sampled at power-on or chip reset to configure boot behavior. Driving these pins externally at the wrong voltage during boot can prevent the chip from starting correctly.

#### ESP32 Strapping Pins

| GPIO | Function | Pull-down (0) | Pull-up (1) |
|------|----------|---------------|-------------|
| GPIO0 | Boot mode | Download mode (UART flashing) | SPI boot (normal run) |
| GPIO2 | Must be low in download mode | Required low | OK high after boot |
| GPIO5 | SDIO timing | SDIO falling edge | SDIO rising edge (default) |
| GPIO12 | Flash voltage (MTDI) | 3.3V flash VDD (default) | 1.8V flash VDD — DANGEROUS |
| GPIO15 | SDIO timing | Silent boot | Boot message printed |

**GPIO12 warning:** If GPIO12 is driven high at boot on most ESP32 modules (which use 3.3V flash), the chip will attempt to power the flash at 1.8V, causing a hard fault or data corruption. Avoid pulling GPIO12 high on ESP32 modules unless the module explicitly uses 1.8V flash.

#### ESP32-S2 Strapping Pins

| GPIO | Function | 0 | 1 |
|------|----------|---|---|
| GPIO0 | Boot mode | Download mode | Normal boot |
| GPIO46 | ROM message | Print boot messages | Silent boot |

#### ESP32-S3 Strapping Pins

| GPIO | Function | 0 | 1 |
|------|----------|---|---|
| GPIO0 | Boot mode | Download mode | Normal boot |
| GPIO3 | JTAG control | Software disables JTAG | JTAG enabled |
| GPIO46 | ROM message | Print messages | Silent |

#### ESP32-C3 Strapping Pins

| GPIO | Function | 0 | 1 |
|------|----------|---|---|
| GPIO2 | Boot mode | Download mode | Normal boot |
| GPIO8 | ROM message | Silent | Print messages |
| GPIO9 | Boot mode | Download mode | Normal boot |

#### ESP32-C6 Strapping Pins

| GPIO | Function | 0 | 1 |
|------|----------|---|---|
| GPIO8 | Boot mode | Download mode | Normal boot |
| GPIO9 | ROM message | Print messages | Silent |

#### ESP32-H2 Strapping Pins

| GPIO | Function | 0 | 1 |
|------|----------|---|---|
| GPIO8 | Boot mode | Download mode | Normal boot |
| GPIO9 | ROM message | Print messages | Silent |

---

## DMA Channel Allocation

### GDMA (General DMA) — S3, C3, C6, H2

ESP32-S3, C3, C6, and H2 use a centralized General DMA (GDMA) controller. Peripherals request DMA channels dynamically. There are a fixed number of channel pairs:

| Variant | GDMA RX channels | GDMA TX channels |
|---------|-----------------|-----------------|
| ESP32-S3 | 5 | 5 |
| ESP32-C3 | 3 | 3 |
| ESP32-C6 | 3 | 3 |
| ESP32-H2 | 3 | 3 |

Channels are acquired at driver init time. If all channels are in use, the driver init fails with an error. GDMA supports burst mode and can access all external SRAM (PSRAM included for S3).

**Key constraint:** DMA transfers must use DMA-capable memory (DRAM). Flash-mapped addresses (IROM/DROM) and stack-allocated buffers are not DMA-capable.

### Dedicated DMA — ESP32 original

The original ESP32 does not use GDMA. Each peripheral that supports DMA has dedicated DMA channels built in. DMA is available on: SPI2, SPI3, I2S0, I2S1, UART0/1/2, SDMMC, and I2C (slave only).

**PSRAM cache conflict on ESP32:** When PSRAM (SPIRAM) is enabled on ESP32, accessing PSRAM through the CPU cache and doing SPI/I2S DMA at the same time can cause CPU stalls or cache corruption. Use `ESP_INTR_FLAG_IRAM` and place ISRs in IRAM. See [errata-gotchas.md](errata-gotchas.md) for details.

### ESP32-S2 DMA

S2 uses a transitional model: SPI and I2S have their own DMA channels, but SPI3 (on S2, called SPI3) is shared. Total: 6 SPI DMA channels, 2 I2S DMA channels.

---

## Zephyr Devicetree Examples

### SPI Controller

```dts
/* In board overlay or application overlay */
&spi2 {
    status = "okay";
    cs-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;
    pinctrl-0 = <&spim2_default>;
    pinctrl-names = "default";

    my_device: device@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;
        spi-max-frequency = <10000000>;
        size = <0x800000>; /* 8 Mbit */
        jedec-id = [ef 40 17];
    };
};
```

### I2C Controller

```dts
&i2c0 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_STANDARD>;
    pinctrl-0 = <&i2c0_default>;
    pinctrl-names = "default";

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};
```

### LEDC (PWM) via Zephyr

```dts
/* ESP32-C3 LEDC example */
&ledc0 {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    channel0@0 {
        reg = <0>;
        io-channels = <&gpio0 2>;
        timer = <0>;
    };
};
```

```c
/* In application code */
const struct device *ledc = DEVICE_DT_GET(DT_NODELABEL(ledc0));
struct pwm_dt_spec pwm = PWM_DT_SPEC_GET(DT_NODELABEL(channel0_0));

pwm_set_dt(&pwm, PWM_USEC(20000), PWM_USEC(1500)); /* 50 Hz, 1.5 ms pulse */
```

### GPIO with Interrupt

```dts
/ {
    aliases {
        sw0 = &button0;
    };

    buttons {
        compatible = "gpio-keys";
        button0: button_0 {
            gpios = <&gpio0 9 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
            label = "Boot button";
        };
    };
};
```

```c
static const struct gpio_dt_spec button =
    GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);

static struct gpio_callback button_cb;

void button_handler(const struct device *dev, struct gpio_callback *cb,
                    uint32_t pins)
{
    printk("Button pressed\n");
}

gpio_pin_configure_dt(&button, GPIO_INPUT);
gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
gpio_init_callback(&button_cb, button_handler, BIT(button.pin));
gpio_add_callback(button.port, &button_cb);
```

### Pin Control (pinctrl) for ESP32-C3

```dts
/* In board's pinctrl file, typically boards/arm/esp32c3.../esp32c3_pinctrl.dtsi */
&pinctrl {
    uart0_default: uart0_default {
        group1 {
            pinmux = <UART0_TX_GPIO21>;
            output-high;
        };
        group2 {
            pinmux = <UART0_RX_GPIO20>;
            bias-pull-up;
            input-enable;
        };
    };

    i2c0_default: i2c0_default {
        group1 {
            pinmux = <I2C0_SDA_GPIO0>, <I2C0_SCL_GPIO1>;
            drive-open-drain;
            output-high;
            input-enable;
        };
    };
};
```

The pinctrl system in Zephyr for ESP32 uses the `espressif,esp32-pinctrl` compatible. Each signal function is encoded as a macro combining signal and GPIO number: `UART0_TX_GPIO21` means route UART0 TX to GPIO21.

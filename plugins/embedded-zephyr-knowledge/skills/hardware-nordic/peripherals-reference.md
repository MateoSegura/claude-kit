# Nordic nRF Peripheral Reference

## Peripheral Matrix

| Peripheral | nRF52832 | nRF52840 | nRF5340 app | nRF5340 net | nRF9160 |
|-----------|---------|---------|------------|------------|---------|
| UARTE | 1 | 2 | 4 | 1 | 2 |
| SPIM | 3 | 3+SPIM3 | 4+SPIM4 | 1 | 3 |
| TWIM | 2 | 3 | 4 | 1 | 3 |
| SAADC | 8 ch | 8 ch | 8 ch | No | 8 ch |
| PWM | 3 | 4 | 4 | 1 | 3 |
| TIMER | 5 | 5 | 6 | 2 | 3 |
| RTC | 3 | 3 | 4 | 2 | 2 |
| WDT | 1 | 1 | 2 | 1 | 2 |
| QDEC | 1 | 1 | 1 | — | — |
| QSPI | — | 1 | 1 | — | — |
| NFCT | 1 | 1 | 1 (net) | — | — |
| PDM | 1 | 1 | 1 | — | — |
| I2S | 1 | 1 | 1 | — | — |
| USBD | — | 1 | 1 | — | — |
| COMP | 1 | 1 | 1 | — | 1 |
| TEMP | 1 | 1 | 1 | 1 | 1 |
| DPPI/PPI | PPI | PPI | DPPI | DPPI | — |
| IPC | — | — | 1 | 1 | 1 |

## EasyDMA — Critical Requirements

All Nordic DMA-capable peripherals (UARTE, SPIM, SPIS, TWIM, SAADC, PDM, I2S, QSPI) use EasyDMA for data transfer.

**Hard constraints:**
1. **Buffers must be in RAM** — EasyDMA cannot access flash. Storing a transmit buffer in `const` (flash) causes silent data corruption or a HardFault.
2. **Word-aligned buffers** — Most peripherals require 4-byte alignment. Use `__aligned(4)`.
3. **Buffer cannot be on stack in cooperative threads** — The stack may be swapped out. Use `static` or heap-allocated buffers.
4. **nRF52 restriction**: Buffers must be in the first 256 KB of RAM (lower RAM section). On nRF52840, RAM starts at 0x20000000 and the first 256 KB ends at 0x20040000.

```c
/* WRONG — const may be placed in flash */
static const uint8_t tx_buf[] = {0x01, 0x02, 0x03};

/* CORRECT — explicitly in RAM */
static uint8_t tx_buf[] = {0x01, 0x02, 0x03};

/* CORRECT — aligned for DMA */
static uint8_t __aligned(4) spi_buf[64];
```

**Zephyr note:** Zephyr's SPI, I2C, and UART drivers handle EasyDMA automatically when you use the standard APIs. The constraint matters when writing custom drivers or using nrfx HAL directly.

## PPI / DPPI — Zero-Latency Event Routing

PPI (Programmable Peripheral Interconnect) on nRF52, DPPI (Distributed PPI) on nRF53/54, allows peripherals to directly trigger each other without CPU involvement.

### PPI (nRF52 series)

PPI connects an event from one peripheral to a task on another using configurable channels (0–19 are free; 20–31 reserved for SoftDevice).

```c
#include <nrfx_ppi.h>

nrf_ppi_channel_t ch;
nrfx_ppi_channel_alloc(&ch);
nrfx_ppi_channel_assign(ch,
    nrf_timer_event_address_get(NRF_TIMER1, NRF_TIMER_EVENT_COMPARE0),
    nrf_gpiote_task_address_get(NRF_GPIOTE, NRF_GPIOTE_TASK_OUT_0));
nrfx_ppi_channel_enable(ch);
```

Common PPI patterns:
- Timer COMPARE → GPIO toggle (precise timing without ISR)
- GPIOTE IN → SAADC SAMPLE (sample ADC on external trigger)
- RTC COMPARE → TIMER START (low-power periodic operation)
- RADIO END → PPI fork to GPIO (RF timing measurement)

### DPPI (nRF5340, nRF54)

DPPI uses publish/subscribe instead of fixed channel pairs. Any number of publishers can publish to a channel; any number of subscribers can subscribe.

```c
/* Publish TIMER1 COMPARE0 on DPPI channel 0 */
nrf_timer_publish_set(NRF_TIMER10, NRF_TIMER_EVENT_COMPARE0, 0);

/* Subscribe GPIOTE task to channel 0 */
nrf_gpiote_subscribe_set(NRF_GPIOTE20, NRF_GPIOTE_TASK_OUT_0, 0);
```

## GPIO

**Drive strength options (nRF52/53):**

| Mode | Constant | Description |
|------|----------|-------------|
| Standard | `GPIO_DRIVE_S0S1` | ~2 mA, default |
| High drive | `GPIO_DRIVE_H0H1` | ~8 mA |
| Open drain | `GPIO_DRIVE_S0D1` | Open-drain for I2C |
| Disconnect | `GPIO_DRIVE_D0D1` | High-impedance |

**GPIO sense for wakeup:**
```dts
/* Configure pin as wakeup source in devicetree */
buttons {
    button0: button_0 {
        gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
        zephyr,wakeup-source;  /* Mark as wakeup source */
    };
};
```

```kconfig
CONFIG_GPIO_WAKEUP=y  /* Enable GPIO wakeup support */
```

Sense is configured in hardware: `GPIO_INT_SENSE_LOW` or `GPIO_INT_SENSE_HIGH`. The pin retains its sense configuration in System OFF (deep sleep) and can wake the SoC.

**Port events:** GPIOTE PORT event (not per-pin GPIOTE) is the preferred wakeup mechanism — it uses a single interrupt for all GPIO wakeup pins.

## SAADC — Successive Approximation ADC

| Attribute | Value |
|-----------|-------|
| Channels | 8 (nRF52/53/91), single-ended or differential |
| Resolution | 8, 10, 12, 14 bits (oversampling) |
| Reference | Internal 0.6 V, VDD/4 |
| Gain options | 1/6, 1/5, 1/4, 1/3, 1/2, 1, 2, 4 |
| Oversampling | 2×, 4×, 8×, 16×, 32×, 64×, 128×, 256× |
| Burst mode | Sample multiple times per SAMPLE task |
| EasyDMA | Yes — results written directly to RAM buffer |

**Input range formula:** `VIN = RESULT × (REFERENCE / GAIN) / 2^(RESOLUTION-1)`

With default config (12-bit, VREF=0.6V, gain=1/6):
- Full scale: 0.6 V × 6 = 3.6 V → suitable for VDD monitoring
- Each step: 3.6 V / 4096 ≈ 879 µV

**Zephyr devicetree example:**

```dts
&adc {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;
        zephyr,gain = "ADC_GAIN_1_6";
        zephyr,reference = "ADC_REF_INTERNAL";
        zephyr,acquisition-time = <ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 40)>;
        zephyr,input-positive = <NRF_SAADC_AIN0>;
        zephyr,resolution = <12>;
        zephyr,oversampling = <4>;
    };
};
```

**Zephyr API:**

```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(adc));
struct adc_sequence sequence = {
    .channels = BIT(0),
    .buffer = &sample,
    .buffer_size = sizeof(sample),
    .resolution = 12,
};
adc_read(dev, &sequence);
```

**Errata [73] on nRF52832:** SAADC offset calibration is off by default. Always call `nrfx_saadc_calibrate_offset()` before first conversion, or apply workaround. See [errata-gotchas.md](errata-gotchas.md).

## TWIM — Two-Wire Interface (I2C Master)

Nordic's I2C peripheral is TWIM (master) / TWIS (slave). Always use `nordic,nrf-twim` compatible string for master mode.

```dts
&i2c1 {
    compatible = "nordic,nrf-twim";
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;  /* 400 kHz */
    pinctrl-0 = <&i2c1_default>;
    pinctrl-1 = <&i2c1_sleep>;
    pinctrl-names = "default", "sleep";

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};
```

**Errata [211] on nRF52832:** TWIM may generate spurious STOPPED event. Workaround: use `twim_transfer_workaround()` from nrfx. Zephyr's nRF TWIM driver includes this workaround automatically when `CONFIG_I2C=y` and target is nRF52832.

## SPIM — SPI Master

```dts
&spi2 {
    compatible = "nordic,nrf-spim";
    status = "okay";
    cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;
    pinctrl-0 = <&spi2_default>;
    pinctrl-names = "default";
    clock-frequency = <DT_FREQ_M(8)>;
};
```

**SPIM3 / SPIM4 (high-speed):**
- nRF52840 SPIM3: up to 32 MHz, supports HFXO-derived clock, DMA to any RAM
- nRF5340 SPIM4: up to 32 MHz with dedicated pin remapping
- **Errata [198] nRF52840 SPIM3**: Anomaly with certain SPI modes. See [errata-gotchas.md](errata-gotchas.md).

## QSPI

Available on nRF52840 and nRF5340 app core. Supports single/dual/quad SPI up to 32 MHz. Primary use: large external NOR flash for XIP or data storage.

```dts
&qspi {
    status = "okay";
    pinctrl-0 = <&qspi_default>;
    pinctrl-names = "default";
    mx25r6435f: mx25r6435f@0 {
        compatible = "nordic,qspi-nor";
        reg = <0>;
        sck-frequency = <DT_FREQ_M(8)>;
        quad-enable-requirements = "S2B1v1";
        size = <DT_SIZE_M(64)>;
    };
};
```

**nRF5340 QSPI cache:** Hardware XIP cache (4 KB). Errata: cache must be flushed before writing to flash while cache is enabled. Zephyr's QSPI driver handles this, but direct nrfx usage requires manual cache management.

## nRF5340 Core Peripheral Assignment

Some peripherals are hard-assigned to one core; others can be assigned via the SPU (Security Processing Unit).

| Peripheral | Core | Notes |
|-----------|------|-------|
| RADIO | Net only | BLE/802.15.4 |
| NFCT | Net only | NFC tag |
| IPC | Both | Shared memory communication |
| USBD | App only | USB |
| QSPI | App only | External flash |
| SAADC | App only | ADC |
| SPIM0-3 | App (default) | Reassignable via SPU |
| GPIO P0/P1 | App (default) | Configurable |
| Clock | App | Controls HFXO, LFXO |

**Net core GPIO:** Net core uses GPIO via `gpio0` and `gpio1` nodes in the network core overlay (`nrf5340_cpunet` DTS). Access from net core only — app core cannot directly control net core's GPIO if the net core owns them.

**IPC communication (Zephyr RPMsg):**

```kconfig
# App core
CONFIG_IPC_SERVICE=y
CONFIG_IPC_SERVICE_BACKEND_RPMSG=y

# Net core
CONFIG_IPC_SERVICE=y
CONFIG_IPC_SERVICE_BACKEND_RPMSG=y
```

Data exchange uses shared RAM at the boundary between the two cores (typically around 0x20070000). The `hci_ipc` net core sample demonstrates the standard pattern.

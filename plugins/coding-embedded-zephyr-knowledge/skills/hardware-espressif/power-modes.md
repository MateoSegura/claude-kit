# ESP32 Power Modes Reference

## Power Mode Overview

ESP32 variants support a spectrum of power modes. Unlike ARM Cortex-M WFI (Wait-For-Interrupt), which simply halts the CPU clock while maintaining register state, ESP32 deep sleep powers off the entire CPU domain. The application re-runs from reset on wakeup.

| Mode | CPU | Peripherals | WiFi/BLE | RTC | Retention | Wakeup |
|------|-----|-------------|----------|-----|-----------|--------|
| **Active** | Running | On | Active | On | — | — |
| **Modem-sleep** | Running | On | Intermittent (DTIM) | On | Full | WiFi packet interval |
| **Light-sleep** | Paused (WFI) | On | Paused | On | Registers + RTC RAM | Timer, GPIO, UART, I2C, BLE, WiFi |
| **Deep-sleep** | Off | Off | Off | On | RTC RAM only | Timer, GPIO, touch, ULP, UART (ESP32) |
| **Hibernation** | Off | Off | Off | Minimal | None | Timer, GPIO (EXT0 only on ESP32) |

### Key architectural difference from ARM

On Cortex-M, `WFI` pauses the core but keeps SRAM alive. The call stack, local variables, and thread state all survive. On ESP32, **deep sleep destroys all DRAM contents and CPU register state**. The application must explicitly save state to RTC memory before entering deep sleep and reconstruct state after wakeup.

---

## Current Consumption by Variant and Mode

The following figures are representative values from Espressif datasheets. Actual consumption depends on VDD voltage, peripherals enabled, clock speed, and temperature.

### ESP32 (original)

| Mode | Typical current |
|------|----------------|
| Active (240 MHz, WiFi TX) | 240–380 mA peak |
| Active (240 MHz, no RF) | ~68 mA |
| Modem-sleep | ~15–20 mA |
| Light-sleep | ~800 µA |
| Deep-sleep (RTC on, ULP running) | ~150 µA |
| Deep-sleep (timer wakeup, no ULP) | ~10 µA |
| Hibernation | ~5 µA |

### ESP32-S2

| Mode | Typical current |
|------|----------------|
| Active (240 MHz, WiFi TX) | 310 mA peak |
| Active (240 MHz, no RF) | ~37 mA |
| Modem-sleep | ~12 mA |
| Light-sleep | ~450 µA |
| Deep-sleep | ~22 µA |
| Deep-sleep (no RTC memory retention) | ~5 µA |

### ESP32-S3

| Mode | Typical current |
|------|----------------|
| Active (240 MHz, WiFi TX) | 355 mA peak |
| Active (240 MHz, no RF) | ~45 mA |
| Modem-sleep | ~20 mA |
| Light-sleep | ~240 µA |
| Deep-sleep | ~8 µA |

### ESP32-C3

| Mode | Typical current |
|------|----------------|
| Active (160 MHz, WiFi TX) | 350 mA peak |
| Active (160 MHz, no RF) | ~23 mA |
| Modem-sleep | ~12–15 mA |
| Light-sleep | ~130 µA |
| Deep-sleep | ~5 µA |

### ESP32-C6

| Mode | Typical current |
|------|----------------|
| Active (160 MHz, WiFi TX) | 337 mA peak |
| Active (160 MHz, LP core only) | ~1 mA |
| Modem-sleep | ~9 mA |
| Light-sleep | ~80 µA |
| Deep-sleep (HP off, LP core on) | ~20–30 µA |
| Deep-sleep (LP core off) | ~5 µA |

### ESP32-H2

| Mode | Typical current |
|------|----------------|
| Active (96 MHz, 802.15.4 TX) | 18 mA typical |
| Active (96 MHz, BLE TX) | 13 mA typical |
| Active (no RF) | ~16 mA |
| Light-sleep | ~85 µA |
| Deep-sleep | ~8 µA |

---

## Wakeup Sources by Variant

| Wakeup Source | ESP32 | ESP32-S2 | ESP32-S3 | ESP32-C3 | ESP32-C6 | ESP32-H2 |
|--------------|-------|----------|----------|----------|----------|----------|
| **Timer (RTC)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **GPIO EXT0** (single GPIO, any level) | Yes | No | No | No | No | No |
| **GPIO EXT1** (multiple GPIOs, AND/OR) | Yes | Yes | Yes | Yes | Yes | Yes |
| **Touch pad** | Yes | Yes | Yes | No | No | No |
| **ULP coprocessor** | Yes | Yes | Yes | No | Yes (LP core) | Yes (LP core) |
| **UART** | Yes (from deep-sleep, legacy) | No | No | No | No | No |
| **BLE** | No | No | No | Yes | Yes | Yes |
| **WiFi** | No | No | No | No | Yes | — |
| **USB** (from light-sleep) | No | Yes | Yes | No | No | No |
| **GPIO (any, from light-sleep)** | Yes | Yes | Yes | Yes | Yes | Yes |

### Configuring Wakeup Sources (ESP-IDF API, usable from Zephyr)

```c
#include <esp_sleep.h>

/* Timer wakeup */
esp_sleep_enable_timer_wakeup(30ULL * 1000000); /* 30 seconds in microseconds */

/* EXT1 wakeup on any of several GPIOs going HIGH */
uint64_t wakeup_pin_mask = (1ULL << GPIO_NUM_2) | (1ULL << GPIO_NUM_4);
esp_sleep_enable_ext1_wakeup(wakeup_pin_mask, ESP_EXT1_WAKEUP_ANY_HIGH);

/* Touch wakeup (ESP32/S2/S3 only) */
esp_sleep_enable_touchpad_wakeup();

/* Enter deep sleep */
esp_deep_sleep_start();

/* Enter light sleep (preserves CPU state) */
esp_light_sleep_start();

/* After wakeup from light sleep, check cause */
esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
```

---

## RTC Memory

### Purpose and Retention

RTC (Real-Time Clock) memory retains data across deep sleep. All other SRAM is erased during deep sleep. RTC memory is the only way to pass state between sleep cycles without writing to flash (NVS).

| Variant | RTC SLOW MEM | RTC FAST MEM |
|---------|-------------|--------------|
| ESP32 | 8 KB (accessible to ULP + CPU) | 8 KB (CPU only, fast) |
| ESP32-S2 | 8 KB | 8 KB |
| ESP32-S3 | 8 KB | 8 KB |
| ESP32-C3 | 16 KB (combined RTC memory) | — |
| ESP32-C6 | 16 KB (LP SRAM) | — |
| ESP32-H2 | 16 KB | — |

### Declaring RTC Variables

```c
/* Place variable in RTC SLOW memory - survives deep sleep */
static RTC_DATA_ATTR int boot_count = 0;
static RTC_DATA_ATTR uint8_t sensor_buffer[64];

/* Place in RTC FAST memory (ESP32/S2/S3 only) - accessible in ISR */
static RTC_FAST_ATTR uint32_t irq_state;

void main(void)
{
    boot_count++;

    if (boot_count == 1) {
        /* First boot - initialize */
        memset(sensor_buffer, 0, sizeof(sensor_buffer));
    } else {
        /* Subsequent boots - data is valid */
        printk("Boot #%d, last sensor: %d\n", boot_count, sensor_buffer[0]);
    }

    /* Check what caused the wakeup */
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    switch (cause) {
    case ESP_SLEEP_WAKEUP_TIMER:
        printk("Timer wakeup\n");
        break;
    case ESP_SLEEP_WAKEUP_EXT1:
        printk("GPIO wakeup, mask: 0x%llx\n",
               esp_sleep_get_ext1_wakeup_status());
        break;
    default:
        printk("Other/first boot\n");
    }
}
```

---

## ULP Coprocessor

### Overview

The ULP (Ultra-Low-Power) coprocessor allows simple programs to run while the main CPU is in deep sleep. It can sample GPIOs, ADC channels, and I2C sensors, and wake the main CPU when a threshold is met.

### ULP Variants by Chip

| Variant | ULP type | Max instructions | ADC access | GPIO | I2C |
|---------|----------|-----------------|------------|------|-----|
| ESP32 | FSM (state machine) | ~256 instructions | Yes (ADC1) | Yes | Bit-bang only |
| ESP32-S2 | FSM + RISC-V | FSM: ~256 + RISC-V: 8KB SRAM | Yes | Yes | Bit-bang |
| ESP32-S3 | FSM + RISC-V | RISC-V: 8KB code | Yes | Yes | Bit-bang |
| ESP32-C6 | LP RISC-V core | Full 16KB LP SRAM | Yes (LP ADC) | Yes (LP GPIO) | LP I2C |
| ESP32-H2 | LP RISC-V core | Full 16KB LP SRAM | Yes (LP ADC) | Yes (LP GPIO) | LP I2C |
| ESP32-C3 | None | — | — | — | — |

### ULP RISC-V Example (ESP32-S2/S3)

```c
/* ulp_main.c — compiled with ulp_riscv toolchain */
#include "ulp_riscv.h"
#include "ulp_riscv_adc.h"

/* Shared variable between ULP and main CPU */
uint32_t ulp_adc_value;
uint32_t ulp_wakeup_threshold = 2048;

int main(void)
{
    /* Initialize ADC in ULP context */
    ulp_riscv_adc_init(ADC_UNIT_1, ADC_ATTEN_DB_11);

    while (1) {
        ulp_adc_value = ulp_riscv_adc_read_channel(ADC_UNIT_1, ADC_CHANNEL_3);

        if (ulp_adc_value > ulp_wakeup_threshold) {
            /* Wakeup main CPU */
            ulp_riscv_wakeup_main_processor();
        }

        ulp_riscv_delay_cycles(1000 * ULP_RISCV_CYCLES_PER_MS);
    }
}
```

### LP Core (ESP32-C6 / ESP32-H2)

The LP (Low-Power) core on C6 and H2 is a full RISC-V processor with access to LP peripherals (LP GPIO, LP UART, LP I2C, LP ADC). It can run independently while the HP core is in deep sleep. Unlike the FSM ULP, the LP core runs standard C programs compiled with the ESP-IDF LP core toolchain.

---

## Zephyr PM Integration

### What Zephyr PM Covers

Zephyr's power management (`CONFIG_PM=y`) integrates with the ESP32 power management at the light-sleep level. When the Zephyr scheduler determines all threads are idle, it evaluates available low-power states and enters the deepest feasible state.

```kconfig
# Enable Zephyr system power management
CONFIG_PM=y

# Enable device power management (peripheral suspend/resume)
CONFIG_PM_DEVICE=y

# Enable runtime PM (devices can self-suspend)
CONFIG_PM_DEVICE_RUNTIME=y
```

### Power State Mapping

| Zephyr PM state | ESP32 equivalent |
|----------------|-----------------|
| `PM_STATE_RUNTIME_IDLE` | Modem-sleep |
| `PM_STATE_SUSPEND_TO_IDLE` | Light-sleep |
| `PM_STATE_SOFT_OFF` | Deep-sleep (with wakeup source) |

### Known Limitations of Zephyr PM on ESP32

1. **Deep sleep via Zephyr PM is not fully integrated** as of Zephyr 3.x. For production deep-sleep, use the ESP-IDF API directly (`esp_deep_sleep_start()`). Zephyr's `PM_STATE_SOFT_OFF` path may not properly save all peripheral state.

2. **WiFi modem-sleep** requires the WiFi stack to be active. If `CONFIG_WIFI=y` and a WiFi connection is active, modem-sleep is managed by the WiFi driver, not directly by Zephyr PM.

3. **BLE and PM interaction**: BLE maintains connection intervals that constrain how long the radio can sleep. When a BLE connection is active, light-sleep duration is bounded by the BLE connection interval.

4. **Zephyr PM states on RISC-V ESP32 variants** (C3, C6, H2): Light-sleep support in Zephyr is more stable on C3 than on C6/H2, which have the additional LP core complexity.

5. **RTC alarm as wakeup**: To wake from light-sleep on a timer, the `esp32_rtc_timer` driver must be enabled. Configure via:
   ```kconfig
   CONFIG_RTC=y
   CONFIG_RTC_ESP32=y
   ```

### Recommended Pattern for Deep Sleep

```c
#include <zephyr/kernel.h>
#include <esp_sleep.h>

/* Use RTC_DATA_ATTR to retain counter across deep sleep */
static RTC_DATA_ATTR uint32_t deep_sleep_count;

void enter_deep_sleep_30s(void)
{
    deep_sleep_count++;

    /* Flush any pending log messages */
    LOG_INF("Entering deep sleep #%u", deep_sleep_count);
    k_sleep(K_MSEC(100)); /* Allow UART TX to complete */

    /* Configure wakeup source */
    esp_sleep_enable_timer_wakeup(30ULL * 1000000ULL);

    /* Enter deep sleep — this call does not return */
    esp_deep_sleep_start();
}
```

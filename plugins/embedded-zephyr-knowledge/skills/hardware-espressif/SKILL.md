---
name: embedded-zephyr-knowledge:hardware-espressif
description: Espressif ESP32 hardware families — ESP32, S2, S3, C3, C6, H2 — Xtensa vs RISC-V cores, WiFi/BLE capabilities, GPIO matrix, deep sleep wakeup sources, esptool flash, and Zephyr board support
user-invocable: false
---

# Espressif ESP32 Quick Reference

## Family Overview

| Variant | CPU | Freq | WiFi | BLE | RAM | Flash |
|---------|-----|------|------|-----|-----|-------|
| ESP32 | Dual Xtensa LX6 | 240 MHz | 802.11 b/g/n | BT 4.2 + Classic | 520 KB SRAM | External |
| ESP32-S2 | Single Xtensa LX7 | 240 MHz | 802.11 b/g/n | None | 320 KB SRAM | External |
| ESP32-S3 | Dual Xtensa LX7 | 240 MHz | 802.11 b/g/n | BLE 5.0 | 512 KB SRAM | External |
| ESP32-C3 | Single RISC-V RV32IMC | 160 MHz | 802.11 b/g/n | BLE 5.0 | 400 KB SRAM | External |
| ESP32-C6 | Single RISC-V RV32IMAC + LP core | 160 MHz | 802.11 b/g/n/ax (WiFi 6) | BLE 5.3 | 512 KB SRAM | External |
| ESP32-H2 | Single RISC-V RV32IMAC + LP core | 96 MHz | None | BLE 5.3 | 320 KB SRAM | External |

**Key distinction:** ESP32/S2/S3 use Xtensa cores (proprietary ISA, requires Xtensa toolchain). C3/C6/H2 use RISC-V (standard open ISA, uses standard riscv32 toolchain).

## Variant Selection Quick Guide

| Need | Choose |
|------|--------|
| Maximum performance + BLE + WiFi | ESP32-S3 |
| Low-cost WiFi + BLE 5 | ESP32-C3 |
| WiFi 6 + Thread/Zigbee + BLE 5.3 | ESP32-C6 |
| IEEE 802.15.4 only (no WiFi) | ESP32-H2 |
| USB OTG (native) + no BLE | ESP32-S2 |
| Legacy designs, max GPIO count | ESP32 |

## Common Kconfig for ESP32 Targets

```kconfig
# WiFi stack (all WiFi-capable variants)
CONFIG_WIFI=y
CONFIG_ESP32_WIFI_STA_AUTO_CONNECT=n

# BLE (S3, C3, C6, H2)
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y

# ESP32 power management integration
CONFIG_PM=y
CONFIG_PM_DEVICE=y

# Serial flash / PSRAM
CONFIG_ESP_SPIRAM=y           # Enable PSRAM (if module has it)
CONFIG_ESP_SPIRAM_SIZE=4194304 # 4 MB example
```

## Flash Commands

```bash
# Build for specific ESP32 board
west build -b esp32s3_devkitc/esp32s3/procpu -- -DBOARD_FLASH_RUNNER=openocd

# Flash via west (uses esptool.py internally)
west flash --esp-device /dev/ttyUSB0 --esp-baud-rate 921600

# Flash directly with esptool.py
esptool.py --chip esp32s3 --port /dev/ttyUSB0 --baud 921600 \
    write_flash -z 0x0 build/zephyr/zephyr.bin

# Erase entire flash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# Read MAC address and chip info
esptool.py --chip esp32 --port /dev/ttyUSB0 chip_id
```

## Deep Sleep Overview

ESP32 deep sleep fully powers off the CPU — this is NOT a Zephyr `PM_STATE_SUSPEND_TO_RAM`. The application restarts from the reset vector on wakeup.

```c
#include <zephyr/pm/pm.h>

/* RTC_DATA_ATTR survives deep sleep */
static RTC_DATA_ATTR int boot_count;

void main(void) {
    boot_count++;

    /* Configure timer wakeup (Zephyr PM path) */
    /* Or use ESP-IDF API directly for deep sleep */
    esp_sleep_enable_timer_wakeup(10ULL * 1000000); /* 10 s */
    esp_deep_sleep_start();
}
```

**Wakeup sources by variant:** Timer, GPIO (EXT0/EXT1), touch pad (ESP32/S2/S3), ULP program, UART (ESP32 only). See [power-modes.md](power-modes.md) for full matrix.

**RTC memory:** 16 KB on ESP32/S2/S3; 16 KB on C3/C6/H2. Annotate with `RTC_DATA_ATTR` to retain across deep sleep.

## Zephyr Board Names (west build -b)

```bash
# ESP32 (original)
esp32_devkitc_wroom/esp32/procpu

# ESP32-S2
esp32s2_saola/esp32s2/procpu

# ESP32-S3
esp32s3_devkitc/esp32s3/procpu

# ESP32-C3
esp32c3_devkitm/esp32c3

# ESP32-C6
esp32c6_devkitc/esp32c6

# ESP32-H2
esp32h2_devkitm/esp32h2
```

## GPIO Matrix

All ESP32 variants feature a programmable GPIO matrix that allows most digital signals to be routed to any GPIO pin. Certain peripherals (ADC, DAC, touch, analog comparator) are pin-fixed. SPI in high-speed (master) mode requires specific pins.

**Strapping pins** must not be driven externally at boot — see [peripherals-reference.md](peripherals-reference.md) for per-variant strapping pin tables.

## ADC Gotcha — ESP32 Original

**CRITICAL:** On original ESP32 (not S2/S3/Cx), ADC2 cannot be used while WiFi is active. ADC2 shares hardware with the WiFi RF subsystem. Use ADC1 channels only when WiFi is enabled.

## Additional resources

- For CPU architecture details, RAM/flash specs, GPIO counts, interface counts, and selection decision matrix, see [families-overview.md](families-overview.md)
- For peripheral availability matrix, GPIO matrix deep dive, strapping pins, DMA allocation, and devicetree examples, see [peripherals-reference.md](peripherals-reference.md)
- For power modes, current consumption, wakeup sources, RTC memory, ULP coprocessor, and Zephyr PM integration, see [power-modes.md](power-modes.md)
- For hardware errata, ADC/WiFi conflicts, PSRAM cache issues, memory layout gotchas, and secure boot warnings, see [errata-gotchas.md](errata-gotchas.md)
- For Zephyr board support table, feature support matrix, ESP-IDF dependency model, MCUboot/OTA, and debugging setup, see [zephyr-support.md](zephyr-support.md)
- For esptool.py commands, espefuse.py, JTAG debugging, west flash integration, and environment setup, see [tooling-reference.md](tooling-reference.md)

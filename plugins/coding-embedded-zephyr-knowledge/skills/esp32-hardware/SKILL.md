---
name: esp32-hardware
description: ESP32 hardware support — ESP32/S3/C3/C6 families, WiFi/BLE coexistence, GPIO matrix, deep sleep with RTC wakeup, esptool flash configuration
user-invocable: false
---

# ESP32 Quick Reference

## ESP32 Families

| Family | Core | Features |
|--------|------|----------|
| ESP32 | Dual Xtensa | WiFi, BLE Classic |
| ESP32-S3 | Dual Xtensa | WiFi, BLE 5, AI accelerator |
| ESP32-C3 | RISC-V | WiFi, BLE 5, low-cost |
| ESP32-C6 | RISC-V | WiFi 6, BLE 5.3, Thread |

## Deep Sleep

**CRITICAL:** ESP32 cannot "sleep" like Cortex-M. Deep sleep fully shuts down CPU. Use RTC memory for state persistence.

```c
#include <zephyr/drivers/rtc.h>

/* Save state to RTC memory */
static RTC_DATA_ATTR int boot_count;

void main(void) {
    boot_count++;
    printk("Boot count: %d\n", boot_count);
    
    /* Configure wakeup */
    esp_sleep_enable_timer_wakeup(10 * 1000000);  /* 10 seconds */
    esp_deep_sleep_start();
}
```

## WiFi Configuration

```kconfig
CONFIG_WIFI=y
CONFIG_NET_L2_ETHERNET=y
CONFIG_ESP32_WIFI_STA_AUTO=y
```

## Flash Tool

```bash
west flash --esp-device /dev/ttyUSB0
```

## Additional resources

- For ESP32 devicetree, WiFi/BLE coexistence, and deep sleep details, see [esp32-reference.md](esp32-reference.md)
- For ESP32-specific examples including WiFi STA and OTA, see [esp32-examples.md](esp32-examples.md)

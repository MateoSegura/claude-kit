---
name: coding-embedded-zephyr-knowledge:stm32-hardware
description: STM32 hardware support — F4/L4/H7/U5/WB/WL families, clock tree configuration, HAL integration, power modes, ST-Link/OpenOCD debug
user-invocable: false
---

# STM32 Quick Reference

## STM32 Families

| Family | Core | Features |
|--------|------|----------|
| STM32F4 | Cortex-M4 | General purpose, FPU |
| STM32L4 | Cortex-M4 | Ultra-low-power |
| STM32H7 | Cortex-M7 | High-performance, 480MHz |
| STM32U5 | Cortex-M33 | Ultra-low-power with TrustZone |
| STM32WB | Dual-core M4+M0+ | BLE, Zigbee |

## Clock Tree Configuration

**DTS:**

```dts
&rcc {
    clocks = <&pll>;
    clock-frequency = <180000000>;
};

&pll {
    div-m = <8>;
    mul-n = <360>;
    div-p = <2>;
    clocks = <&clk_hse>;
};
```

## Power Modes

```c
#include <zephyr/pm/pm.h>

/* Enter Stop mode */
pm_state_force(0, &(struct pm_state_info){PM_STATE_SUSPEND_TO_IDLE, 0, 0});
```

**Kconfig:**

```kconfig
CONFIG_PM=y
CONFIG_PM_DEVICE=y
```

## Flash and Debug

**ST-Link:**

```bash
west flash --runner openocd
west debug
```

## Additional resources

- For STM32 devicetree pinctrl, clock configuration, and HAL integration, see [stm32-reference.md](stm32-reference.md)
- For STM32-specific examples including STM32WB BLE, see [stm32-examples.md](stm32-examples.md)

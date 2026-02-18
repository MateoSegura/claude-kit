---
name: coding-embedded-zephyr-knowledge:nordic-hardware
description: Nordic nRF hardware support — nRF52/53/54/91 families, BLE controller, power management (DCDC, RAM retention), nrfjprog/nrfutil, cellular modem
user-invocable: false
---

# Nordic nRF Quick Reference

## nRF Families

| Family | Core | Features |
|--------|------|----------|
| nRF52840 | Cortex-M4 | BLE 5, USB, 1MB flash |
| nRF5340 | Dual Cortex-M33 | BLE 5.3, app+net cores |
| nRF9160 | Cortex-M33 | LTE-M, NB-IoT, GPS |
| nRF54L/H | Cortex-M33 | BLE 5.4, next-gen |

## Power Optimization

**DCDC regulators:**

```kconfig
CONFIG_DCDC_HV=y  # High-voltage DCDC
CONFIG_DCDC_LV=y  # Low-voltage DCDC (nRF53/91)
```

**RAM retention:**

```kconfig
CONFIG_RAM_POWER_DOWN_LIBRARY=y
```

## BLE Controller

Zephyr uses native Bluetooth controller (no SoftDevice needed).

```kconfig
CONFIG_BT=y
CONFIG_BT_LL_SOFTDEVICE=n  # Use Zephyr controller
```

## Flash Tools

```bash
# nrfjprog
nrfjprog --program build/zephyr/zephyr.hex --chiperase
nrfjprog --reset

# nrfutil (newer)
nrfutil device program --firmware build/zephyr/zephyr.hex
```

## Additional resources

- For nRF devicetree bindings, BLE configuration, and power modes, see [nrf-reference.md](nrf-reference.md)
- For nRF-specific examples including dual-core nRF5340 and cellular nRF9160, see [nrf-examples.md](nrf-examples.md)

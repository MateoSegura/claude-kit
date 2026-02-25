---
name: embedded-zephyr-knowledge:hardware-nordic
description: Nordic Semiconductor nRF hardware reference — nRF52/53/54/91 family specs, peripheral matrix, power modes (DCDC/System OFF), known errata, Zephyr board support, and nrfjprog/nrfutil tooling
user-invocable: false
---

# Nordic nRF Hardware Quick Reference

## Family Overview

| SoC | Core | Freq | Flash | RAM | BLE | Protocols | Key Feature |
|-----|------|------|-------|-----|-----|-----------|-------------|
| nRF52810 | M4 (no FPU) | 64 MHz | 192 KB | 24 KB | 5.0 | BLE, ANT | Ultra low-cost |
| nRF52832 | M4F | 64 MHz | 512 KB | 64 KB | 5.0 | BLE, ANT, NFC | Most popular 52 |
| nRF52833 | M4F | 64 MHz | 512 KB | 128 KB | 5.1 | BLE, ANT, 802.15.4, NFC | Thread/Zigbee capable |
| nRF52840 | M4F | 64 MHz | 1 MB | 256 KB | 5.0 | BLE, 802.15.4, NFC, USB | Full-featured flagship |
| nRF5340 | Dual M33 | 128/64 MHz | 1 MB/256 KB | 512/64 KB | 5.4 | BLE, 802.15.4, NFC | Dual-core, TrustZone |
| nRF54L15 | M33 | 128 MHz | 1.5 MB | 256 KB | 5.4 | BLE, 802.15.4 | Next-gen low-power |
| nRF54H20 | Dual M33+PPR | 320 MHz | (ext) | 1 MB | 5.4 | BLE, 802.15.4 | High-performance |
| nRF9151 | M33 | 64 MHz | 1 MB | 256 KB | — | LTE-M, NB-IoT | Integrated SiP |
| nRF9160 | M33 | 64 MHz | 1 MB | 256 KB | — | LTE-M, NB-IoT, GPS | First cellular SiP |
| nRF9161 | M33 | 64 MHz | 1 MB | 256 KB | — | LTE-M, NB-IoT, GPS | Improved RF SiP |

## Selection Guide

| Need | Recommended |
|------|-------------|
| BLE only, cost-constrained | nRF52832 |
| BLE + USB | nRF52840 |
| BLE + Thread/Zigbee | nRF52833 or nRF52840 |
| High-performance dual-core BLE | nRF5340 |
| Next-gen BLE, ultra-low power | nRF54L15 |
| Cellular LTE-M/NB-IoT | nRF9160 / nRF9161 / nRF9151 |

## DCDC Configuration (Critical for Power)

Always enable DCDC regulators — saves 2-3x power vs LDO-only mode.

```kconfig
# nRF52 series
CONFIG_DCDC_HV=y          # High-voltage DCDC (VDDMAIN → 1.8 V rail)

# nRF5340 and nRF91
CONFIG_DCDC_HV=y           # Main DCDC
CONFIG_DCDC_LV=y           # Low-voltage DCDC (internal)
```

For nRF5340, apply separately in both `cpuapp` and `cpunet` builds.

## BLE Controller Selection

```kconfig
# Zephyr native LL (vanilla Zephyr — default)
CONFIG_BT=y
# SoftDevice Controller (nRF Connect SDK — better certification)
CONFIG_BT_LL_SOFTDEVICE=y
CONFIG_MPSL=y
```

Zephyr LL: open-source, suitable for most projects. SoftDevice Controller: Nordic-certified, required for Bluetooth SIG qualification, better RF performance on nRF5340.

## Common Kconfig by Task

| Task | Kconfig |
|------|---------|
| Enable BLE peripheral | `CONFIG_BT=y`, `CONFIG_BT_PERIPHERAL=y` |
| Enable BLE central | `CONFIG_BT=y`, `CONFIG_BT_CENTRAL=y` |
| Enable Thread | `CONFIG_NET_L2_OPENTHREAD=y` |
| Enable USB CDC-ACM | `CONFIG_USB_DEVICE_STACK=y`, `CONFIG_USB_CDC_ACM=y` |
| Enable NFC | `CONFIG_NFC_T2T_NRFXLIB=y` (nRF Connect SDK) |
| Enable ADC | `CONFIG_ADC=y` |
| System power management | `CONFIG_PM=y`, `CONFIG_PM_DEVICE=y` |
| RAM power down | `CONFIG_RAM_POWER_DOWN_LIBRARY=y` |

## nRF52 vs nRF5340 Pin Qualification

nRF5340 uses core-qualified pin names in overlay files:

```dts
/* nRF52840 — no qualifier */
&uart0 { pinctrl-0 = <&uart0_default>; }

/* nRF5340 cpuapp — must qualify */
&uart0 { pinctrl-0 = <&uart0_default>; }
/* pins defined in cpuapp_common-pinctrl.dtsi */
```

## Common Gotchas

- **NFC pins P0.09/P0.10**: Reserved for NFC by default on nRF52 — must reclaim if using as GPIO (`CONFIG_NFCT_PINS_AS_GPIOS=y`)
- **nRF5340 dual-core**: Always build with `--sysbuild`; net core image is flashed automatically
- **EasyDMA buffers**: Must be in RAM (not flash), word-aligned — peripheral DMA cannot access flash
- **DCDC off by default**: Boards enable DCDC in DTS via `reg-init-microvolt`, always verify with PPK2
- **nRF9160 modem firmware**: Modem lib version must match modem firmware version exactly

## Additional Resources

- [families-overview.md](families-overview.md) — Detailed per-family specs, I/O counts, package options, selection guide
- [peripherals-reference.md](peripherals-reference.md) — Complete peripheral matrix, EasyDMA rules, PPI/DPPI, SAADC, nRF5340 core assignment
- [power-modes.md](power-modes.md) — System ON/OFF states, DCDC setup, RAM retention, current tables, nRF9160 PSM/eDRX
- [errata-gotchas.md](errata-gotchas.md) — Silicon errata per variant, NFC pin conflicts, EasyDMA pitfalls, common mistakes
- [zephyr-support.md](zephyr-support.md) — Board names, feature matrix, BLE controllers, MCUboot/SMP DFU, debug
- [tooling-reference.md](tooling-reference.md) — nrfjprog, nrfutil, west flash/debug, PPK2 profiling, SEGGER RTT

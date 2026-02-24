# Nordic nRF Family Detailed Specifications

## nRF52 Series — Bluetooth Low Energy

### nRF52810

| Attribute | Value |
|-----------|-------|
| CPU | Cortex-M4 (no FPU) @ 64 MHz |
| Flash | 192 KB |
| RAM | 24 KB |
| GPIO | 32 (P0.00–P0.31) |
| ADC (SAADC) | 8 channels, 12-bit |
| SPI (SPIM) | 1× SPIM, 1× SPIS |
| I2C (TWIM) | 1× TWIM, 1× TWIS |
| UART (UARTE) | 1× UARTE |
| USB | No |
| NFC | No |
| BLE version | 5.0 (2 Mbps PHY) |
| Radio | BLE, ANT |
| Security | AES-CCM hardware |
| Debug | SWD (2-pin) |
| Package | QFN48, WLCSP |

**Use case:** Cost-optimized BLE beacons, simple sensor nodes. No FPU means avoid floating-point in hot paths.

### nRF52832

| Attribute | Value |
|-----------|-------|
| CPU | Cortex-M4F (with FPU) @ 64 MHz |
| Flash | 512 KB |
| RAM | 64 KB |
| GPIO | 32 (P0.00–P0.31) |
| ADC (SAADC) | 8 channels, 12-bit |
| SPI (SPIM/SPIS) | 3× SPIM, 2× SPIS |
| I2C (TWIM/TWIS) | 2× TWIM, 2× TWIS |
| UART (UARTE) | 1× UARTE |
| USB | No |
| NFC | Yes (NFC-A, Type 2 Tag) — pins P0.09/P0.10 |
| BLE version | 5.0 (2 Mbps PHY, long range PHY not supported) |
| Radio | BLE, ANT, 2.4 GHz proprietary |
| Security | AES-CCM, AES-ECB, CSPRNG, BPROT |
| CryptoCell | No |
| Debug | SWD (2-pin) |
| Package | QFN48, WLCSP |

**Use case:** The workhorse nRF52. Use when 512 KB flash and 64 KB RAM are sufficient. Most community libraries and examples target this SoC.

**Known errata of concern:** [73] SAADC calibration offset, [89] SPI slave mode, [108] RAM powering, [211] TWIM spurious STOPPED event. See [errata-gotchas.md](errata-gotchas.md).

### nRF52833

| Attribute | Value |
|-----------|-------|
| CPU | Cortex-M4F (with FPU) @ 64 MHz |
| Flash | 512 KB |
| RAM | 128 KB |
| GPIO | 48 (P0.00–P0.31, P1.00–P1.15) |
| ADC (SAADC) | 8 channels, 12-bit |
| SPI (SPIM/SPIS) | 3× SPIM + 1× SPIM3 (high-speed), 2× SPIS |
| I2C (TWIM/TWIS) | 3× TWIM, 3× TWIS |
| UART (UARTE) | 2× UARTE |
| USB | Yes (Full-speed, 12 Mbps) |
| NFC | Yes (NFC-A) — pins P0.09/P0.10 |
| BLE version | 5.1 (AoA/AoD direction finding) |
| Radio | BLE, ANT, 802.15.4 (Thread, Zigbee) |
| Security | AES-CCM, BPROT |
| CryptoCell | No |
| Debug | SWD (2-pin) |
| Package | QFN40, QFN48, WLCSP |

**Use case:** Thread/Zigbee mesh applications needing 802.15.4 alongside BLE. USB for DFU or CDC-ACM logging. Direction finding for indoor positioning.

### nRF52840

| Attribute | Value |
|-----------|-------|
| CPU | Cortex-M4F (with FPU) @ 64 MHz |
| Flash | 1 MB |
| RAM | 256 KB |
| GPIO | 48 (P0.00–P0.31, P1.00–P1.15) |
| ADC (SAADC) | 8 channels, 12-bit |
| SPI (SPIM/SPIS) | 3× SPIM + 1× SPIM3 (32 MHz capable), 2× SPIS |
| I2C (TWIM/TWIS) | 3× TWIM, 3× TWIS |
| UART (UARTE) | 2× UARTE |
| USB | Yes (Full-speed, 12 Mbps) |
| NFC | Yes (NFC-A) — pins P0.09/P0.10 |
| BLE version | 5.0 (2 Mbps, Long Range Coded PHY) |
| Radio | BLE, ANT, 802.15.4 (Thread, Zigbee) |
| Security | ARM CryptoCell-310 (AES, SHA, ECDH, RSA, RNG) |
| Debug | SWD (2-pin), ETM trace |
| Package | aQFN73, QFN48 |

**Use case:** Full-featured flagship. Best choice when you need USB + BLE + Thread, or large firmware/RAM. Most Zephyr examples target `nrf52840dk_nrf52840`.

**Known errata of concern:** [198] SPIM3, [218] USB VBUS detection, [219] HFXO startup. See [errata-gotchas.md](errata-gotchas.md).

---

## nRF53 Series — Dual-Core

### nRF5340

| Attribute | App Core | Net Core |
|-----------|----------|----------|
| CPU | Cortex-M33 (with DSP, FPU) | Cortex-M33 |
| Frequency | 128 MHz | 64 MHz |
| Flash | 1 MB | 256 KB |
| RAM | 512 KB | 64 KB |
| BLE version | 5.4 (via net core) | — |
| Radio | — | BLE, 802.15.4, NFC |
| USB | Yes (Full-speed) | No |
| GPIO | 48 (P0+P1) | Shared with app core |
| Security | ARM TrustZone, CryptoCell-312, SWD lock | — |
| Debug | SWD with separate app/net AP | — |
| Package | AQFN94 |

**Architecture:** Application core runs the user application. Network core runs the BLE/802.15.4 radio controller. They communicate via the IPC peripheral (shared RAM at 0x20070000). Zephyr handles IPC automatically in the `hci_ipc` net core image.

**Build:** Always use `--sysbuild`. West builds and flashes both cores:
```bash
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
west flash
```

---

## nRF54 Series — Next Generation

### nRF54L15

| Attribute | Value |
|-----------|-------|
| CPU | Cortex-M33 @ 128 MHz (with TrustZone, FPU, DSP) |
| Flash | 1.5 MB (internal NVM) |
| RAM | 256 KB |
| GPIO | 47 |
| BLE version | 5.4 (LE Audio, CIS, BIS, HADM) |
| Radio | BLE, 802.15.4, 2.4 GHz proprietary |
| USB | Yes (FS) |
| Security | CryptoCell-312, PSA Level 3 capable |
| Power | Sub-1 µA System OFF, improved DCDC |
| Package | WLCSP |

**Key improvements over nRF52840:** Lower active current (~30% reduction), longer battery life in low-power modes, Bluetooth LE Audio support (LC3 codec), improved security.

**Zephyr status:** Supported from Zephyr 3.6+ (`nrf54l15dk_nrf54l15_cpuapp`). nRF Connect SDK preferred for LE Audio.

### nRF54H20

| Attribute | Value |
|-----------|-------|
| CPU | Dual Cortex-M33 (app+rad) + PPR (Cortex-M33 @ 16 MHz, ultra-low-power) |
| Frequency | 320 MHz (app), 256 MHz (rad) |
| RAM | 1 MB (shared) |
| Flash | External (no internal NOR) |
| BLE version | 5.4 |
| Radio | BLE, 802.15.4 |
| Security | TrustZone, Global Master Security Policy |
| Package | LGA94 |

**Use case:** High-performance IoT gateway, LE Audio sink, products requiring sustained compute. Requires external flash. Not pin-compatible with nRF52 family.

---

## nRF91 Series — Cellular SiP

All nRF91 variants are Systems-in-Package: nRF9160/9161/9151 contain the application MCU, a separate modem MCU, and an LTE RF front-end in one package. The modem runs Nordic's closed-source firmware.

### nRF9160

| Attribute | Value |
|-----------|-------|
| App MCU | Cortex-M33 @ 64 MHz (TrustZone) |
| Modem MCU | Separate (runs Nordic modem firmware) |
| Flash (app) | 1 MB |
| RAM (app) | 256 KB |
| Cellular | LTE-M Cat-M1, NB-IoT Cat-NB1/NB2 |
| GNSS | Integrated GPS/AGPS/PGPS |
| Interface | UART, SPI, I2C, GPIO (application domain only) |
| Security | ARM TrustZone, separate modem domain |
| Peripherals | Limited vs nRF52 — no USB, no TWIS, limited SPIM |
| Package | LGA94 (10.0 × 16.0 mm) |

**Modem firmware:** Separate from application firmware. Must match the modem library version. Update via `nrfutil device` or FOTA. Current stable: v1.3.x.

**Application isolation:** Application runs in non-secure domain by default. Modem controlled via AT commands over IPC (not physical UART).

### nRF9161

Functionally identical to nRF9160 with improved RF performance and a different package option (LGA94 pin-compatible). Preferred for new designs.

### nRF9151

Enhanced version with:
- Improved low-power performance
- Better RF sensitivity
- Same pin-compatible LGA94 package as nRF9161
- Tighter integration (fewer external components needed)

---

## Package Compatibility

| Package | Compatible SoCs |
|---------|-----------------|
| QFN48 | nRF52810, nRF52832, nRF52833, nRF52840 (not pin-compatible across all) |
| WLCSP | nRF52832, nRF54L15 |
| aQFN73 | nRF52840 |
| AQFN94 | nRF5340 |
| LGA94 | nRF9160, nRF9161, nRF9151 (pin-compatible between 9161/9151) |

**nRF52840 → nRF5340 migration:** Not pin-compatible. Different package. Software is portable for the application core, but peripheral assignments and build system differ significantly.

## Peripheral I/O Instance Counts Summary

| Peripheral | nRF52810 | nRF52832 | nRF52833 | nRF52840 | nRF5340 app | nRF91 |
|-----------|---------|---------|---------|---------|------------|-------|
| UARTE | 1 | 1 | 2 | 2 | 4 | 2 |
| SPIM | 1+0hs | 3+0hs | 3+1hs | 3+1hs | 4+1hs | 3 |
| TWIM | 1 | 2 | 3 | 3 | 4 | 3 |
| SAADC chan | 8 | 8 | 8 | 8 | 8 | 8 |
| PWM | 1 | 3 | 4 | 4 | 4 | 3 |
| TIMER | 3 | 5 | 5 | 5 | 6 | 3 |
| RTC | 2 | 3 | 3 | 3 | 4 | 2 |
| GPIO total | 32 | 32 | 48 | 48 | 48 | 9 (app domain) |

*hs = high-speed SPIM (32 MHz, SPIM3 on nRF52 / SPIM4 on nRF5340 app)*

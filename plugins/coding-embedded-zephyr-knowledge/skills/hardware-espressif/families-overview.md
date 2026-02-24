# ESP32 Families — Detailed Overview

This reference covers the six main ESP32 product families, their architecture differences, peripheral counts, and how to choose among them.

## Detailed Comparison Table

| Feature | ESP32 | ESP32-S2 | ESP32-S3 | ESP32-C3 | ESP32-C6 | ESP32-H2 |
|---------|-------|----------|----------|----------|----------|----------|
| **CPU ISA** | Xtensa LX6 | Xtensa LX7 | Xtensa LX7 | RISC-V RV32IMC | RISC-V RV32IMAC | RISC-V RV32IMAC |
| **CPU cores** | 2 | 1 | 2 | 1 | 1 + LP core | 1 + LP core |
| **Max frequency** | 240 MHz | 240 MHz | 240 MHz | 160 MHz | 160 MHz | 96 MHz |
| **SRAM** | 520 KB | 320 KB | 512 KB | 400 KB | 512 KB | 320 KB |
| **ROM** | 448 KB | 128 KB | 384 KB | 384 KB | 384 KB | 128 KB |
| **RTC SRAM** | 16 KB slow + 8 KB fast | 16 KB | 16 KB | 16 KB | 16 KB | 16 KB |
| **Internal flash** | None (external only) | None | None | 384 KB ROM + external | None | None |
| **PSRAM support** | Up to 8 MB (Octal SPI) | Up to 32 MB | Up to 8 MB Octal, 32 MB Quad | No | No | No |
| **WiFi standard** | 802.11 b/g/n (2.4 GHz) | 802.11 b/g/n | 802.11 b/g/n | 802.11 b/g/n | 802.11 b/g/n/ax | None |
| **Bluetooth** | BT 4.2 (Classic + BLE) | None | BLE 5.0 | BLE 5.0 | BLE 5.3 | BLE 5.3 |
| **IEEE 802.15.4** | No | No | No | No | Yes (Thread/Zigbee) | Yes (Thread/Zigbee) |
| **GPIO count** | 34 | 43 | 45 | 22 | 30 | 27 |
| **ADC channels** | 18 (2x SAR) | 20 (2x SAR) | 20 (2x SAR) | 6 (1x SAR) | 7 (1x SAR) | 5 (1x SAR) |
| **DAC channels** | 2 | 2 | None | None | None | None |
| **SPI controllers** | 4 (2 usable) | 4 (2 usable) | 4 (2 usable) | 3 (1 usable) | 1 GP SPI | 1 GP SPI |
| **I2C controllers** | 2 | 2 | 2 | 1 | 2 | 2 |
| **UART ports** | 3 | 2 | 3 | 2 | 3 | 3 |
| **I2S ports** | 2 | 1 | 2 | 1 | 1 | 1 |
| **USB** | None | USB 1.1 OTG (native) | USB 1.1 OTG (native) | USB Serial/JTAG only | USB Serial/JTAG only | USB Serial/JTAG only |
| **Ethernet MAC** | Yes (external PHY) | No | No | No | No | No |
| **CAN/TWAI** | 1 | 1 | 1 | 1 | 1 | 1 |
| **RMT channels** | 8 | 4 | 8 | 4 | 4 | 4 |
| **LEDC channels** | 16 (2 speed) | 8 | 8 | 6 | 6 | 6 |
| **Touch sensors** | 10 | 14 | 14 | None | None | None |
| **Crypto HW** | RSA-4096, SHA, AES, RNG | + RSA-4096, SHA, AES, RNG, DS | RSA-4096, SHA, AES-XTS, DS | RSA-3072, SHA, AES, RNG | RSA-3072, SHA, AES, ECDSA | RSA-3072, SHA, AES, ECDSA |
| **Secure boot** | v1 (ECDSA-based) | v2 | v2 | v2 | v2 | v2 |
| **Flash encryption** | AES-256 XTS | AES-256 XTS | AES-256 XTS | AES-256 XTS | AES-256 XTS | AES-256 XTS |
| **JTAG** | External (GPIO12-15) | External + USB | USB Serial/JTAG | USB Serial/JTAG | USB Serial/JTAG | External JTAG |
| **Package options** | QFN48, QFN38 (bare die) | QFN56 | QFN56 | QFN32 | QFN40 | QFN32 |
| **Release year** | 2016 | 2019 | 2020 | 2020 | 2022 | 2022 |

## Per-Family Sections

### ESP32 (Original)

The original dual-core Xtensa LX6 SoC. Most peripheral-rich in terms of ADC channels, GPIO count, and connectivity options (Ethernet MAC, Bluetooth Classic + BLE, DAC). The ESP32 is the longest-shipping variant with the largest ecosystem.

**Target use cases:**
- Audio applications (I2S, DAC)
- Ethernet-connected gateways (requires external PHY like LAN8720)
- Legacy designs requiring Bluetooth Classic SPP/A2DP
- Applications needing maximum GPIO or ADC channels
- Products where proven field reliability outweighs cost

**Key limitations:**
- ADC2 cannot be used concurrently with WiFi (hardware conflict)
- Xtensa LX6 is older microarchitecture than LX7
- Secure boot v1 is weaker than v2 on later variants
- No USB OTG; USB requires external bridge chip

**Notable sub-variants:** ESP32-D0WD (bare), ESP32-D0WDQ6 (bare), modules: ESP-WROOM-32, ESP32-WROVER (includes PSRAM)

---

### ESP32-S2

Single-core Xtensa LX7 with native USB 1.1 OTG. The S2 trades Bluetooth entirely for USB capability and an improved ADC (though still dual-SAR). Large GPIO count (43) and wide PSRAM support make it attractive for HMI and display applications.

**Target use cases:**
- USB HID devices (keyboard, mouse, gamepad, MIDI)
- USB DFU (Device Firmware Upgrade over USB)
- Display-connected IoT nodes (no BLE overhead)
- Applications requiring large PSRAM (up to 32 MB)

**Key limitations:**
- No Bluetooth (neither Classic nor BLE)
- Single core — may bottleneck WiFi + application concurrency
- Smaller ecosystem than ESP32 original or S3
- WiFi only (no WiFi 6, no 802.15.4)

---

### ESP32-S3

Dual-core Xtensa LX7 with BLE 5.0 and native USB. The most capable Espressif SoC for general-purpose IoT: fastest Xtensa cores, full BLE 5.0, native USB OTG, up to 8 MB Octal SPI PSRAM, and an AI/ML vector extension (PIE). Best choice when maximum performance is needed alongside wireless.

**Target use cases:**
- Edge AI/ML inference (face detection, keyword spotting)
- HMI with touchscreen + BLE remote control
- High-throughput WiFi + BLE coexistence
- USB Audio class devices
- Camera + streaming applications

**Key limitations:**
- No Ethernet MAC (unlike original ESP32)
- No DAC (unlike ESP32 and S2)
- Higher power and cost than C-series

---

### ESP32-C3

First Espressif RISC-V SoC. Single-core RV32IMC at 160 MHz with WiFi + BLE 5.0. Smaller footprint and lower cost than S-series. Built-in USB Serial/JTAG eliminates the need for an external USB-UART bridge during development.

**Target use cases:**
- Cost-sensitive IoT sensors with WiFi + BLE
- Drop-in ESP8266 replacement with BLE added
- Battery-powered nodes (lower active power than ESP32)
- Simple UART-free debug via USB Serial/JTAG

**Key limitations:**
- Single core; context-switching between WiFi and application can introduce latency
- Smaller GPIO count (22) limits peripheral connections
- No touch sensor, no DAC, no Ethernet
- RISC-V means existing Xtensa assembly routines need porting

---

### ESP32-C6

RISC-V SoC with WiFi 6 (802.11ax), BLE 5.3, and native IEEE 802.15.4 (Thread/Zigbee). The C6 also introduces a dedicated low-power (LP) RISC-V core that can run while the main core is in sleep, enabling always-on sensing at low power.

**Target use cases:**
- Matter protocol devices (WiFi + Thread dual-radio)
- Zigbee coordinator or end device
- WiFi 6 TWT (Target Wake Time) for battery savings
- Always-on sensor fusion (LP core runs during main sleep)
- Smart home devices requiring multi-protocol support

**Key limitations:**
- IEEE 802.15.4 and WiFi share the RF front-end — true simultaneous dual-radio not possible (time-multiplexed)
- LP core is RV32IMC (no A or C extensions in LP context)
- Newer platform; fewer third-party examples than C3

---

### ESP32-H2

RISC-V SoC optimized for IEEE 802.15.4 (Thread/Zigbee) + BLE 5.3. No WiFi. Designed for mesh network devices where WiFi is handled by a separate gateway or coordinator.

**Target use cases:**
- Thread end devices and routers
- Zigbee sensors and actuators
- BLE + Thread combo (e.g., Matter over Thread with BLE commissioning)
- Ultra-low-power mesh nodes (96 MHz max is intentionally lower)

**Key limitations:**
- No WiFi — cannot connect to WiFi network directly
- Lower clock speed (96 MHz max) limits compute-intensive tasks
- Smaller ecosystem than WiFi-capable variants
- External JTAG pins required (no USB Serial/JTAG)

---

## Selection Guide Decision Matrix

```
Start here: Does the product need WiFi?
│
├─ YES: Does it need BLE?
│  │
│  ├─ YES: Does it need USB OTG or AI acceleration?
│  │  ├─ YES → ESP32-S3 (dual-core LX7, USB, BLE 5.0, AI ext)
│  │  └─ NO: Cost-sensitive?
│  │     ├─ YES → ESP32-C3 (RISC-V, cheap, BLE 5.0, WiFi)
│  │     └─ NO: Need WiFi 6 / Thread / Zigbee?
│  │        ├─ YES → ESP32-C6 (WiFi 6, BLE 5.3, 802.15.4)
│  │        └─ NO → ESP32-S3 or ESP32-C3 per cost target
│  │
│  └─ NO (WiFi only, no BLE): Need USB OTG?
│     ├─ YES → ESP32-S2
│     └─ NO: Need Ethernet MAC?
│        ├─ YES → ESP32 (original)
│        └─ NO → ESP32-S2 or ESP32-C3
│
└─ NO: Does it need Thread/Zigbee?
   │
   ├─ YES + BLE: Does it need WiFi later via companion chip?
   │  ├─ YES (full Matter) → ESP32-C6 (has WiFi too)
   │  └─ NO (mesh only) → ESP32-H2 (no WiFi, lower power)
   └─ NO: Reconsider — most ESP32 products need WiFi
```

## Toolchain Architecture Differences

| Attribute | Xtensa (ESP32, S2, S3) | RISC-V (C3, C6, H2) |
|-----------|------------------------|----------------------|
| Toolchain | `xtensa-esp32-elf-gcc` | `riscv32-esp-elf-gcc` |
| ISA | Proprietary Xtensa | Open RISC-V RV32IMC[A] |
| West SDK path | `--toolchain espressif` | `--toolchain espressif` |
| GDB | `xtensa-esp32-elf-gdb` | `riscv32-esp-elf-gdb` |
| Key difference | Wider SIMD, 3-operand MAC | Standard open toolchain ecosystem |

Both toolchains are downloaded via `espup` (Espressif's toolchain installer) and configured in `~/.espressif/`.

## Memory Architecture

All ESP32 variants use an external SPI flash (typically QSPI or OPI/Octal-SPI). The flash contains the application binary, partition table, NVS data, and OTA slots.

```
ESP32 Memory Map (typical):
┌─────────────────┬──────────────┐
│ External Flash  │ Mapped via   │
│ (up to 16 MB)   │ cache/MMU    │
├─────────────────┼──────────────┤
│ DRAM            │ 0x3FFC_0000  │
│ (dynamic RAM)   │ (varies)     │
├─────────────────┼──────────────┤
│ IRAM            │ 0x4007_0000  │
│ (instruction)   │ (varies)     │
├─────────────────┼──────────────┤
│ RTC SLOW MEM    │ 0x5000_0000  │
│ (survives sleep)│              │
├─────────────────┼──────────────┤
│ RTC FAST MEM    │ 0x6001_C000  │
│ (survives sleep)│              │
└─────────────────┴──────────────┘
```

Code executing from flash goes through the instruction cache (ICACHE). Performance-critical routines must be placed in IRAM using `IRAM_ATTR`. DMA transfers cannot use flash-mapped addresses — always use DRAM buffers.

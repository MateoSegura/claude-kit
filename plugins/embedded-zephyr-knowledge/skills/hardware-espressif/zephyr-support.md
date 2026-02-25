# ESP32 Zephyr Support Reference

## Supported Boards Table

The following boards are in the official Zephyr tree. Board names are used directly with `west build -b`.

| Board target | Variant | SoC | Notes |
|---|---|---|---|
| `esp32_devkitc_wroom/esp32/procpu` | ESP32 | ESP32 D0WD | WROOM-32 module, dual-core procpu |
| `esp32_devkitc_wroom/esp32/appcpu` | ESP32 | ESP32 D0WD | appcpu (secondary core) |
| `esp32_devkitc_wrover/esp32/procpu` | ESP32 WROVER | ESP32 D0WD + PSRAM | WROVER module with 4MB PSRAM |
| `esp32s2_saola/esp32s2/procpu` | ESP32-S2 | ESP32-S2 | SAOLA-1 dev board |
| `esp32s2_franzininho` | ESP32-S2 | ESP32-S2 | Franzininho WiFi board |
| `esp32s3_devkitc/esp32s3/procpu` | ESP32-S3 | ESP32-S3 | DevKitC-1, dual-core procpu |
| `esp32s3_devkitc/esp32s3/appcpu` | ESP32-S3 | ESP32-S3 | appcpu (secondary core) |
| `esp32s3_luatos_core_esp32s3` | ESP32-S3 | ESP32-S3 | Luatos CORE board |
| `esp32c3_devkitm/esp32c3` | ESP32-C3 | ESP32-C3 | DevKitM-1 |
| `esp32c3_rust_devkit` | ESP32-C3 | ESP32-C3 | Espressif Rust DevKit |
| `esp32c6_devkitc/esp32c6` | ESP32-C6 | ESP32-C6 | DevKitC-1 |
| `esp32h2_devkitm/esp32h2` | ESP32-H2 | ESP32-H2 | DevKitM-1 |

### Build Commands

```bash
# Basic build for ESP32-C3
west build -b esp32c3_devkitm/esp32c3 app/

# Build for ESP32-S3 primary core
west build -b esp32s3_devkitc/esp32s3/procpu app/

# Build with extra config overlay
west build -b esp32c6_devkitc/esp32c6 app/ -- -DEXTRA_CONF_FILE="wifi.conf"

# Flash after build
west flash --esp-device /dev/ttyUSB0

# Flash with higher baud rate for speed
west flash --esp-device /dev/ttyUSB0 --esp-baud-rate 921600

# Monitor serial output
west espressif monitor
```

---

## Feature Support Matrix (Zephyr 3.x)

| Feature | ESP32 | ESP32-S2 | ESP32-S3 | ESP32-C3 | ESP32-C6 | ESP32-H2 |
|---------|-------|----------|----------|----------|----------|----------|
| **WiFi (station)** | Yes | Yes | Yes | Yes | Yes | — |
| **WiFi (AP)** | Yes | Yes | Yes | Yes | Partial | — |
| **WiFi 6** | — | — | — | — | Partial | — |
| **BLE (peripheral)** | Yes | — | Yes | Yes | Yes | Yes |
| **BLE (central)** | Yes | — | Yes | Yes | Yes | Yes |
| **BT Classic** | Partial | — | — | — | — | — |
| **IEEE 802.15.4** | — | — | — | — | Partial | Partial |
| **USB (CDC ACM)** | — | Yes | Yes | Serial/JTAG | Serial/JTAG | — |
| **USB (HID, MSC)** | — | Yes | Yes | — | — | — |
| **SPI (master)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **SPI (slave)** | Yes | Yes | Yes | Partial | Partial | Partial |
| **I2C (master)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **I2C (slave)** | Partial | Partial | Partial | Partial | Partial | Partial |
| **UART** | Yes | Yes | Yes | Yes | Yes | Yes |
| **ADC** | Yes | Yes | Yes | Yes | Yes | Yes |
| **DAC** | Yes | Yes | — | — | — | — |
| **PWM (LEDC)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **PWM (MCPWM)** | Yes | — | Yes | — | — | — |
| **GPIO** | Yes | Yes | Yes | Yes | Yes | Yes |
| **GPIO interrupt** | Yes | Yes | Yes | Yes | Yes | Yes |
| **I2S** | Yes | Partial | Yes | Partial | Partial | — |
| **Timer** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Watchdog** | Yes | Yes | Yes | Yes | Yes | Yes |
| **RTC timer** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Flash (NVS)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **TWAI (CAN)** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Light sleep (PM)** | Partial | Partial | Partial | Partial | Partial | Partial |
| **Deep sleep (PM)** | Via ESP-IDF | Via ESP-IDF | Via ESP-IDF | Via ESP-IDF | Via ESP-IDF | Via ESP-IDF |
| **Ethernet** | Yes (ext PHY) | — | — | — | — | — |
| **MCUboot** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Pinctrl** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Shell** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Logging** | Yes | Yes | Yes | Yes | Yes | Yes |

**Partial** = driver exists but has known limitations or incomplete feature coverage.

---

## ESP-IDF Dependency Model

### Why Zephyr Needs ESP-IDF

Espressif's hardware abstraction layer (HAL) and low-level drivers are distributed as part of the ESP-IDF (Espressif IoT Development Framework). Zephyr does not reimplement these from scratch — it consumes ESP-IDF as a Zephyr HAL module.

This creates a two-layer driver model:

```
Application code
     │
Zephyr driver API (e.g., spi_transceive(), gpio_pin_set())
     │
Zephyr ESP32 driver (in zephyr/drivers/)
     │
ESP-IDF HAL / LL layer (in modules/hal/espressif/)
     │
ESP32 hardware registers
```

**Implication:** The version of ESP-IDF used by Zephyr is pinned in the Zephyr west manifest. Upgrading ESP-IDF independently of Zephyr is not supported and will likely break the build.

### HAL Module Location

```bash
# After west update, ESP-IDF HAL is at:
<workspace>/modules/hal/espressif/

# To check the pinned ESP-IDF version:
cat <workspace>/modules/hal/espressif/version.h
```

### Calling ESP-IDF APIs Directly

You can call ESP-IDF APIs directly from Zephyr application code when Zephyr's driver doesn't cover a needed feature. For example, deep sleep uses ESP-IDF APIs:

```c
/* Zephyr header for core kernel */
#include <zephyr/kernel.h>

/* Direct ESP-IDF include */
#include <esp_sleep.h>
#include <esp_wifi.h>
#include <nvs_flash.h>

/* This is valid in Zephyr ESP32 applications */
esp_sleep_enable_timer_wakeup(30ULL * 1000000ULL);
esp_deep_sleep_start();
```

**Caution:** Directly calling ESP-IDF APIs that conflict with Zephyr driver state (e.g., calling `esp_wifi_set_mode()` while Zephyr's WiFi stack is active) leads to undefined behavior. Only call ESP-IDF APIs for subsystems not covered by Zephyr drivers.

---

## Zephyr vs ESP-IDF: When to Use Which

| Scenario | Use Zephyr | Use ESP-IDF directly |
|----------|-----------|---------------------|
| GPIO control | `gpio_pin_set_dt()` | When GPIO matrix low-level config needed |
| SPI transfer | `spi_transceive()` | When DMA mode quirks need direct control |
| WiFi connect | `wifi_connect()` shell / `net_mgmt()` | For advanced WiFi features (WPS, 802.11k/r) |
| Deep sleep | — | `esp_sleep_enable_*()`, `esp_deep_sleep_start()` |
| NVS (key-value store) | Zephyr settings subsystem | `nvs_open()` / `nvs_set_*()` for fine control |
| Flash partition | `flash_write()` | `esp_partition_write()` for named partitions |
| OTA | MCUboot + `img_mgmt` | `esp_ota_*()` for ESP-IDF OTA |
| Secure boot | Board-level config | `espsecure.py` + eFuse programming |
| BLE | Zephyr BT stack | ESP-IDF Bluedroid only if using BT Classic |

---

## MCUboot and OTA

### MCUboot on ESP32

Zephyr's MCUboot integration supports ESP32 variants as of Zephyr 3.2+. MCUboot occupies the first flash partition (typically 64 KB–96 KB) and validates the application slot signature before booting.

```bash
# Build with MCUboot support
west build -b esp32c3_devkitm/esp32c3 app/ -- -DCONFIG_BOOTLOADER_MCUBOOT=y

# Build MCUboot bootloader separately
west build -b esp32c3_devkitm/esp32c3 bootloader/mcuboot/boot/zephyr/ \
    -- -DCONFIG_BOOT_SIGNATURE_TYPE_RSA=y
```

### Partition Table (ESP32 standard MCUboot layout)

```
0x0000: Bootloader (MCUboot, ~96 KB)
0x8000: Partition table (4 KB)
0x9000: NVS/settings (24 KB)
0xF000: Application slot 0 / primary (variable)
0xZZZZZ: Application slot 1 / secondary (OTA staging, same size as slot 0)
```

### OTA Update Flow with MCUboot

```c
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/storage/flash_map.h>

/* Mark current image as confirmed */
boot_write_img_confirmed();

/* Check if running from slot 0 (primary) */
if (boot_is_img_confirmed()) {
    /* Stable — proceed normally */
}

/* After downloading new image to slot 1:
   Set pending flag — MCUboot will swap on next boot */
boot_request_upgrade(BOOT_UPGRADE_TEST);
sys_reboot(SYS_REBOOT_COLD);
```

---

## Debugging Setup

### USB Serial/JTAG (ESP32-C3, C6, S3, S2)

```bash
# Install OpenOCD with ESP32 support
# On Ubuntu:
sudo apt install openocd  # may not have ESP32 support
# Recommended: use Espressif's OpenOCD fork
pip install esp-idf  # includes idf_tools
idf_tools install openocd-esp32

# Start OpenOCD for ESP32-C3 via USB Serial/JTAG
openocd -f board/esp32c3-builtin.cfg

# Connect GDB (RISC-V target for C3)
riscv32-esp-elf-gdb build/zephyr/zephyr.elf \
    -ex "target extended-remote :3333" \
    -ex "monitor reset halt"
```

### External JTAG (ESP32 original, ESP32-H2)

```bash
# ESP-Prog or ESP-WROVER-KIT (FT2232H-based)
openocd -f interface/ftdi/esp32_devkitj_v1.cfg \
        -f board/esp32-wrover-kit-3.3v.cfg

# GDB for Xtensa target
xtensa-esp32-elf-gdb build/zephyr/zephyr.elf \
    -ex "target extended-remote :3333" \
    -ex "monitor reset halt"
```

### Zephyr JTAG Config in west.yml

For west flash/debug integration:

```yaml
# west.yml — use OpenOCD runner
build:
  cmake-args:
    - -DBOARD_FLASH_RUNNER=openocd
    - -DBOARD_DEBUG_RUNNER=openocd
```

```bash
# Debug via west
west debug  # Starts OpenOCD + GDB in integrated mode
```

### Serial Monitor

```bash
# west espressif monitor (built-in, decodes panic traces)
west espressif monitor --port /dev/ttyUSB0 --baud 115200

# Or standard screen/minicom
screen /dev/ttyUSB0 115200
```

---

## Known Limitations vs. Mainstream Cortex-M Targets

1. **Deep sleep not through Zephyr PM state machine**: `PM_STATE_SOFT_OFF` on ESP32 does not fully integrate with `esp_deep_sleep_start()`. Call ESP-IDF APIs directly for reliable deep sleep.

2. **No true SMP in Zephyr on dual-core variants**: The ESP32 and ESP32-S3 have two cores, but Zephyr's SMP support on ESP32 is marked as experimental. Production applications should target single-core (procpu only) until SMP is stable.

3. **WiFi + BLE coexistence managed by ESP-IDF**: Zephyr defers to ESP-IDF coexistence algorithms. Direct control of coexistence policy is not exposed through Zephyr APIs.

4. **Flash access in ISR**: Unlike Cortex-M which can execute from flash even in ISR context, ESP32 ISRs that run during flash operations will fault if the code is in flash. Mark all ISR code with `IRAM_ATTR`.

5. **No hardware FPU on RISC-V variants**: ESP32-C3/C6/H2 lack a hardware FPU. Floating-point operations are software-emulated, increasing CPU cycles 10–50x versus hardware FPU. Use integer or fixed-point arithmetic for latency-sensitive code.

6. **ADC accuracy**: All ESP32 variants have ±5–10% ADC nonlinearity without calibration. Use `esp_adc_cal_characterize()` for accurate millivolt readings.

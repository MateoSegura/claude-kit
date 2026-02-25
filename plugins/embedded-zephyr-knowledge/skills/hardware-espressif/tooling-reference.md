# ESP32 Tooling Reference

## esptool.py — Complete Command Reference

`esptool.py` is Espressif's official chip communication tool. It handles flashing, reading, erasing, and chip information. It communicates over the ROM UART bootloader protocol.

### Installation

```bash
pip install esptool
# Or install via Espressif's espup toolchain installer
espup install  # includes esptool as part of the toolchain
```

### Chip Auto-Detection

```bash
# Auto-detect chip type (omit --chip to let esptool detect)
esptool.py --port /dev/ttyUSB0 chip_id

# Force specific chip
esptool.py --chip esp32s3 --port /dev/ttyUSB0 chip_id
```

### Flash Operations

```bash
# Write single binary to address
esptool.py --chip esp32c3 --port /dev/ttyUSB0 --baud 921600 \
    write_flash 0x0 build/zephyr/zephyr.bin

# Write multiple binaries (bootloader + partition table + app)
esptool.py --chip esp32s3 --port /dev/ttyUSB0 --baud 921600 \
    write_flash \
    0x0    build/zephyr/esp32s3-bootloader.bin \
    0x8000 build/zephyr/partition-table.bin \
    0xF000 build/zephyr/zephyr.bin

# Compressed write (faster for large images)
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 921600 \
    write_flash -z 0x0 build/zephyr/zephyr.bin

# Write to flash with specific flash mode (QIO, QOUT, DIO, DOUT)
esptool.py --chip esp32 --port /dev/ttyUSB0 \
    write_flash --flash_mode dio --flash_size 4MB 0x0 app.bin
```

### Erase Operations

```bash
# Erase entire flash (factory reset equivalent)
esptool.py --chip esp32c3 --port /dev/ttyUSB0 erase_flash

# Erase specific region (address, length in bytes)
esptool.py --chip esp32 --port /dev/ttyUSB0 \
    erase_region 0x9000 0x6000   # erase NVS partition (24 KB)
```

### Read Operations

```bash
# Read flash contents to file
esptool.py --chip esp32 --port /dev/ttyUSB0 \
    read_flash 0x0 0x400000 flash_backup.bin   # read 4 MB

# Read chip MAC address
esptool.py --chip esp32c3 --port /dev/ttyUSB0 read_mac

# Read flash ID (manufacturer, size)
esptool.py --chip esp32 --port /dev/ttyUSB0 flash_id
```

### Entering Download Mode Manually

Most ESP32 dev boards have an auto-reset circuit that puts the chip into download mode automatically. For bare chips or custom boards:

1. Hold BOOT/IO0 LOW
2. Pulse RESET (EN) LOW then HIGH
3. Release BOOT/IO0

```bash
# Some boards need explicit port configuration
esptool.py --chip esp32c3 --port /dev/ttyUSB0 --before default_reset \
    --after hard_reset write_flash ...
```

### Common Flash Mode and Size Arguments

| Argument | Values | Notes |
|----------|--------|-------|
| `--flash_mode` | `qio`, `qout`, `dio`, `dout` | QIO is fastest, DIO is most compatible |
| `--flash_size` | `2MB`, `4MB`, `8MB`, `16MB` | Auto-detect with `detect` |
| `--flash_freq` | `20m`, `26m`, `40m`, `80m` | Must match flash chip spec |
| `--compress` / `-z` | flag | Enable compression (recommended) |

---

## west flash Integration

Zephyr's `west flash` command calls `esptool.py` internally via the `esp32` runner.

```bash
# Basic flash (auto-detects port on some systems)
west flash

# Specify port explicitly
west flash --esp-device /dev/ttyUSB0

# Adjust baud rate for faster flashing
west flash --esp-device /dev/ttyUSB0 --esp-baud-rate 921600

# Flash specific binary (override default)
west flash --esp-device /dev/ttyUSB0 --bin-file custom.bin

# Show what west flash would run (dry run)
west flash --esp-device /dev/ttyUSB0 --dry-run
```

### west.yml Runner Configuration

Set the default runner in CMakeLists.txt or board configuration:

```cmake
# CMakeLists.txt
set(BOARD_FLASH_RUNNER esp32)
```

Or pass via cmake:

```bash
west build -b esp32c3_devkitm/esp32c3 app/ -- -DBOARD_FLASH_RUNNER=esp32
```

---

## espefuse.py — eFuse Programming (IRREVERSIBLE)

`espefuse.py` reads and programs the one-time-programmable eFuse bits that control security and boot configuration. **eFuse writes are PERMANENT and cannot be undone.** There is no factory reset.

### Safety First

Before running any `burn_*` command:
1. Verify the chip is the correct revision
2. Verify the key files are correct and backed up
3. Run with `--do-not-confirm` ONLY in automated CI — always confirm interactively for first-time use
4. Test the entire flow on a sacrificial device before production

```bash
# Read all eFuse values (safe — read only)
espefuse.py --port /dev/ttyUSB0 summary

# Read specific eFuse block
espefuse.py --port /dev/ttyUSB0 dump
```

### Flash Voltage eFuse (ESP32 original only)

```bash
# IRREVERSIBLE: Set flash voltage to 3.3V (for modules with 3.3V flash)
# After burning, GPIO12 no longer affects flash voltage
espefuse.py --port /dev/ttyUSB0 set_flash_voltage 3.3V

# For 1.8V flash modules (rare)
espefuse.py --port /dev/ttyUSB0 set_flash_voltage 1.8V
```

### Secure Boot eFuses

```bash
# IRREVERSIBLE: Burn secure boot key to eFuse block
espefuse.py --port /dev/ttyUSB0 burn_key \
    BLOCK_KEY0 secure_boot_key.bin SECURE_BOOT_DIGEST0

# IRREVERSIBLE: Enable secure boot
espefuse.py --port /dev/ttyUSB0 burn_efuse ABS_DONE_0
```

### Flash Encryption

```bash
# IRREVERSIBLE: Enable flash encryption (first boot will generate key and encrypt flash)
espefuse.py --port /dev/ttyUSB0 burn_efuse FLASH_ENCRYPTION_CNTR

# Check current flash encryption state
espefuse.py --port /dev/ttyUSB0 summary | grep FLASH_CRYPT
```

### Disable JTAG (for production security)

```bash
# IRREVERSIBLE: Disable JTAG (production hardening)
espefuse.py --port /dev/ttyUSB0 burn_efuse JTAG_DISABLE
```

---

## JTAG Debugging Setup

### Option 1: Built-in USB Serial/JTAG (ESP32-C3, C6, S2, S3)

No external hardware needed. Connect the board's USB port directly to the host. The USB Serial/JTAG peripheral presents as both a serial port and a JTAG interface.

```bash
# Linux: check that the USB JTAG device appears
lsusb | grep Espressif
# Should show: Espressif USB JTAG/serial debug unit

# Permissions: add user to dialout group (or use udev rule)
sudo usermod -a -G dialout $USER
# Or create udev rule:
echo 'ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", MODE="0666"' \
    | sudo tee /etc/udev/rules.d/99-esp32-jtag.rules
sudo udevadm control --reload
```

```bash
# OpenOCD with built-in JTAG (ESP32-C3)
openocd -f board/esp32c3-builtin.cfg

# Or specify interface and target separately
openocd -f interface/esp_usb_jtag.cfg \
        -f target/esp32c3.cfg
```

### Option 2: ESP-Prog (External USB-JTAG Adapter)

ESP-Prog is Espressif's dedicated JTAG + UART adapter. It uses FT2232H (same chip as popular J-Link alternatives). Connects to the target's JTAG pins via a 10-pin header.

```bash
# Wiring for ESP32 original:
# ESP-Prog TDO → ESP32 GPIO15
# ESP-Prog TDI → ESP32 GPIO12
# ESP-Prog TCK → ESP32 GPIO13
# ESP-Prog TMS → ESP32 GPIO14

# OpenOCD with ESP-Prog
openocd -f interface/ftdi/esp32_devkitj_v1.cfg \
        -f board/esp32-wrover-kit-3.3v.cfg
```

### Option 3: ESP-WROVER-KIT

The ESP-WROVER-KIT includes an onboard FT2232H providing both JTAG and UART via a single USB connector.

```bash
openocd -f board/esp32-wrover-kit-3.3v.cfg
```

### GDB Connection

```bash
# For Xtensa targets (ESP32, S2, S3)
xtensa-esp32-elf-gdb build/zephyr/zephyr.elf \
    -ex "target extended-remote :3333" \
    -ex "monitor reset halt" \
    -ex "thb main" \
    -ex "continue"

# For RISC-V targets (C3, C6, H2)
riscv32-esp-elf-gdb build/zephyr/zephyr.elf \
    -ex "target extended-remote :3333" \
    -ex "monitor reset halt" \
    -ex "thb main" \
    -ex "continue"
```

### VSCode / IDE Integration

```json
// .vscode/launch.json for ESP32-C3 (RISC-V)
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "ESP32-C3 Debug",
            "type": "cortex-debug",
            "request": "launch",
            "servertype": "openocd",
            "configFiles": ["board/esp32c3-builtin.cfg"],
            "executable": "${workspaceFolder}/build/zephyr/zephyr.elf",
            "toolchainPrefix": "riscv32-esp-elf",
            "svdFile": "",
            "runToEntryPoint": "main"
        }
    ]
}
```

---

## ESP-IDF as a Zephyr Module — Environment Setup

### Installing the Espressif Toolchain

```bash
# Install espup (Espressif's toolchain manager)
cargo install espup  # requires Rust
espup install        # downloads Xtensa + RISC-V toolchains

# Or use Espressif's Python-based installer
pip install esp-idf-tools
idf_tools install all
```

### West Workspace Setup for ESP32

```yaml
# west.yml — ensure hal_espressif is included
manifest:
  projects:
    - name: hal_espressif
      remote: https://github.com/zephyrproject-rtos/hal_espressif
      revision: main
      path: modules/hal/espressif
```

```bash
# Initialize Zephyr workspace with ESP32 support
west init -m https://github.com/zephyrproject-rtos/zephyr
west update  # Downloads all modules including hal_espressif

# Set up Zephyr environment
source zephyr/zephyr-env.sh

# Set Espressif toolchain path
export ESPRESSIF_TOOLCHAIN_PATH=~/.espressif/tools
export ZEPHYR_TOOLCHAIN_VARIANT=espressif
```

### Verifying Toolchain Installation

```bash
# Verify Xtensa toolchain (ESP32, S2, S3)
xtensa-esp32-elf-gcc --version
xtensa-esp32s3-elf-gcc --version

# Verify RISC-V toolchain (C3, C6, H2)
riscv32-esp-elf-gcc --version

# Verify esptool is accessible
esptool.py version

# Verify OpenOCD with ESP32 support
openocd --version
```

### Python Dependencies

```bash
# Install Zephyr Python requirements
pip install -r zephyr/scripts/requirements.txt

# Install west
pip install west

# Install esptool separately if not included
pip install esptool
```

---

## Partition Table

The ESP32 partition table lives at flash offset 0x8000 (default). It defines named flash regions for the bootloader, application, NVS, OTA slots, and custom data.

```csv
# partitions.csv — custom partition table
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x6000,
otadata,  data, ota,     0xf000,  0x2000,
phy_init, data, phy,     0x11000, 0x1000,
factory,  app,  factory, 0x20000, 0x180000,
ota_0,    app,  ota_0,   0x1A0000,0x180000,
ota_1,    app,  ota_1,   0x320000,0x180000,
```

```bash
# Generate binary partition table from CSV
gen_esp32part.py partitions.csv partitions.bin

# Flash partition table
esptool.py --chip esp32c3 --port /dev/ttyUSB0 \
    write_flash 0x8000 partitions.bin
```

In Zephyr, configure the partition table via DTS flash partitions:

```dts
/* In board DTS or overlay */
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x00000000 0x00010000>;  /* 64 KB */
        };

        slot0_partition: partition@10000 {
            label = "image-0";
            reg = <0x00010000 0x00180000>; /* 1.5 MB */
        };

        slot1_partition: partition@190000 {
            label = "image-1";
            reg = <0x00190000 0x00180000>; /* 1.5 MB */
        };

        storage_partition: partition@310000 {
            label = "storage";
            reg = <0x00310000 0x00008000>; /* 32 KB NVS */
        };
    };
};
```

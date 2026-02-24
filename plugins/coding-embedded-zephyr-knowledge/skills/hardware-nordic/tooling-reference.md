# Nordic nRF Tooling Reference

## nrfjprog

`nrfjprog` is Nordic's low-level command-line tool for programming and debugging nRF devices via J-Link. It is the legacy tool; `nrfutil device` is the modern replacement but `nrfjprog` remains widely used.

### Common Commands

```bash
# Program a hex file (full erase first)
nrfjprog --program build/zephyr/zephyr.hex --chiperase --verify

# Program without erasing (add to existing flash)
nrfjprog --program build/zephyr/zephyr.hex --sectorerase --verify

# Reset and run
nrfjprog --reset

# Erase all flash
nrfjprog --eraseall

# Recover a locked device (APPROTECT enabled)
nrfjprog --recover

# Read device info
nrfjprog --deviceversion
nrfjprog --memrd 0x10000000 --n 32  # Read factory info page

# nRF5340 — specify core
nrfjprog --program cpuapp.hex --coprocessor CP_APPLICATION --chiperase
nrfjprog --program cpunet.hex --coprocessor CP_NETWORK --chiperase
nrfjprog --reset
```

### Multi-Device Support

When multiple J-Link devices are connected, specify by serial number:

```bash
nrfjprog --snr 123456789 --program firmware.hex --chiperase
```

List connected devices:
```bash
nrfjprog --ids
```

### Hex File Merging

Merge bootloader + application into a single hex for production programming:

```bash
mergehex --merge bootloader.hex application.hex --output combined.hex
```

`mergehex` is installed with the nRF Command Line Tools (same package as `nrfjprog`).

---

## nrfutil

`nrfutil` is Nordic's modern unified CLI tool. It uses a plugin architecture where each command group is a separate plugin.

### Installation

```bash
# Install nrfutil
pip install nrfutil  # Or download binary from Nordic

# Install device plugin (for programming/erasing)
nrfutil install device

# Install nrf5sdk-tools plugin (for DFU package generation)
nrfutil install nrf5sdk-tools
```

### Device Programming

```bash
# Program firmware
nrfutil device program --firmware build/zephyr/zephyr.hex

# Program with specific options
nrfutil device program \
    --firmware build/zephyr/zephyr.hex \
    --options chip_erase_mode=ERASE_ALL,reset_after_program=RESET_HARD

# Erase
nrfutil device erase --all

# Recover locked device
nrfutil device recover

# List connected devices
nrfutil device list

# Select device by serial number
nrfutil device program --firmware firmware.hex --serial-number 123456789
```

### DFU Package Creation

For SMP OTA DFU (MCUmgr over BLE):

```bash
# Create DFU package (zip) for SMP upload
nrfutil pkg generate --hw-version 52 \
    --sd-req 0x0000 \
    --application build/zephyr/zephyr.signed.bin \
    --application-version 1 \
    dfu_package.zip
```

### Modem Firmware Update (nRF9160)

```bash
# Update modem firmware (downloads from Nordic or use local file)
nrfutil device program \
    --firmware mfw_nrf9160_1.3.6.zip \
    --options chip_erase_mode=ERASE_NONE,reset_after_program=RESET_HARD

# Check modem firmware version
nrfutil device recover  # If modem is in bootloader mode
```

### Trace Capture (nRF9160)

```bash
nrfutil trace modem --serial-port /dev/ttyUSB0 --output-file trace.bin
# Analyze with Wireshark + Nordic modem trace dissector
```

---

## west — Zephyr Build and Flash Integration

`west` is Zephyr's meta-tool for build, flash, and debug. It wraps nrfjprog, J-Link, and nrfutil based on the board's default runner.

### Flash and Debug Defaults by Board

| Board | Default flash runner | Default debug runner |
|-------|---------------------|---------------------|
| nRF52840DK | jlink (nrfjprog) | jlink |
| nRF52DK | jlink | jlink |
| nRF5340DK | jlink (sysbuild) | jlink |
| nRF9160DK | jlink | jlink |
| nRF54L15DK | jlink | jlink |
| Custom board | Defined in `board.cmake` | — |

### Common west Flash Commands

```bash
# Flash with default runner (J-Link)
west flash

# Flash specific hex
west flash --hex-file combined.hex

# Flash with nrfutil (newer alternative to jlink)
west flash --runner nrfutil

# Recover locked chip before flashing
west flash -- --recover  # Pass extra args to nrfjprog

# nRF5340 sysbuild flash (both cores)
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
west flash  # Automatically flashes cpuapp + cpunet

# Attach debugger to running target (no flash)
west attach
```

### west debug — OpenOCD/J-Link

```bash
# Start debug session (flashes and opens GDB)
west debug

# Attach to running target (no flash)
west attach

# Debug specific core on nRF5340
west debug -- --device nRF5340_xxAA_NET  # Net core
```

---

## PPK2 — Power Profiler Kit II

PPK2 is Nordic's hardware current measurement tool with 100 nA resolution.

### Hardware Modes

**Ampere meter mode:** DUT uses its own power supply. PPK2 measures current in series.
- Connect PPK2 VOUT to DUT VIN
- Connect GND

**Source meter mode:** PPK2 supplies DUT power AND measures current (up to 500 mA).
- Connect PPK2 VOUT+ to DUT VIN
- Connect PPK2 VOUT− / GND to DUT GND
- Set supply voltage in software

### Software: nRF Connect Power Profiler

Available via nRF Connect for Desktop (Windows/Mac/Linux).

Key settings:
- Sample rate: up to 100,000 samples/second
- Average window: configurable (1 ms–1 s)
- Export CSV for analysis

### Measurement Tips

**Disable serial logging during measurement:**

```kconfig
CONFIG_LOG_BACKEND_UART=n
CONFIG_UART_CONSOLE=n
CONFIG_RTT_CONSOLE=y   # Use RTT instead if you need logs
```

**Force System OFF and measure wakeup current:**

```c
pm_state_force(0u, &(struct pm_state_info){PM_STATE_SOFT_OFF, 0, 0});
k_sleep(K_MSEC(1));
/* Measure System OFF current on PPK2 */
/* Configure GPIO wakeup before this point */
```

**Typical measurement targets:**

| State | nRF52840 target | Actual measurement |
|-------|----------------|-------------------|
| BLE advertising, 1 s interval | ~13 µA avg | Verify DCDC on |
| System OFF, no retention | ~0.5 µA | Verify no wakeup source active |
| CPU active, 64 MHz | ~4.8 mA | Verify DCDC |
| BLE connected, 100 ms interval | ~200 µA avg | Varies with data rate |

---

## SEGGER RTT — Real-Time Logging

RTT (Real-Time Transfer) uses a ring buffer in target RAM, accessed by the debugger without halting the CPU.

### Setup in Zephyr

```kconfig
CONFIG_USE_SEGGER_RTT=y
CONFIG_RTT_CONSOLE=y
CONFIG_LOG_BACKEND_RTT=y
CONFIG_UART_CONSOLE=n
CONFIG_LOG=y
CONFIG_LOG_LEVEL_INF=y
```

### Viewing RTT Output

```bash
# Option 1: JLinkRTTViewer (SEGGER GUI tool)
JLinkRTTViewer

# Option 2: JLink RTT Client (CLI)
JLinkRTTClient

# Option 3: west (nRF Connect SDK)
west attach  # Starts J-Link GDB server and opens RTT viewer

# Option 4: nRF Connect for VS Code — built-in RTT viewer
```

### RTT with J-Link GDB Server

```bash
# Terminal 1: J-Link GDB server (also enables RTT)
JLinkGDBServerCLExe -device nRF52840_xxAA -if SWD -speed 4000 \
    -RTTTelnetPort 19021

# Terminal 2: Read RTT via telnet
telnet localhost 19021
```

---

## Common Tooling Issues

### J-Link Firmware Outdated

**Symptom:** `west flash` or `nrfjprog` fail with "J-Link firmware is outdated" or "Target voltage not detected".

**Fix:** Open J-Link Control Panel or Configurator and update firmware. Latest J-Link firmware required for nRF54 series (J-Link firmware ≥ V7.86).

### JTAG Lock / AP Protection (APPROTECT)

**Symptom:** `nrfjprog` returns "Error reading device" or "Access port protection enabled".

**Background:** nRF52/53/54 can enable APPROTECT to lock debug access. Production firmware sometimes enables this. DK boards ship unlocked.

**Recovery:**

```bash
# nrfjprog recovery (erases flash and unlocks)
nrfjprog --recover

# nrfutil recovery
nrfutil device recover

# west (nRF Connect SDK)
west flash -- --recover
```

Recovery erases the entire flash. Back up any data if possible.

### nRF5340 Net Core Not Flashed

**Symptom:** BLE doesn't work after `west flash` on nRF5340, even though BLE code exists.

**Root cause:** Built without `--sysbuild`, so only the app core image was produced. The net core running `hci_ipc` was not built or flashed.

**Fix:**

```bash
# Clean build directory first
rm -rf build/
# Rebuild with sysbuild
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
west flash
```

### Modem Trace Not Starting (nRF9160)

**Symptom:** `nrfutil trace modem` produces no output or "Could not connect to trace device".

**Fix:**
1. Ensure the nRF9160 DK has the Trace interface enabled (solder bridge or jumper setting on DK)
2. Use the correct UART port — nRF9160DK has multiple USB CDC ports; trace is typically on the second one
3. Ensure modem trace Kconfig is enabled:

```kconfig
CONFIG_NRF_MODEM_LIB_TRACE=y
CONFIG_NRF_MODEM_LIB_TRACE_MEDIUM_UART=y
```

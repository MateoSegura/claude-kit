# Probe Reference

Complete configuration reference for J-Link, OpenOCD, ST-Link, and pyOCD debug probes with Zephyr RTOS targets.

## J-Link

### GDB Server

```bash
# Basic SWD connection
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000

# JTAG connection
JLinkGDBServer -device <DEVICE> -if JTAG -speed 4000

# With specific serial number (multi-probe)
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000 -select USB=<serial_number>

# Non-default port
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000 -port 2332

# Quiet mode (less output)
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000 -silent
```

### Common Device Names

| Board | Device Name | Interface |
|-------|------------|-----------|
| nRF52840 DK | nRF52840_xxAA | SWD |
| nRF52833 DK | nRF52833_xxAA | SWD |
| nRF5340 DK (app) | nRF5340_xxAA_APP | SWD |
| nRF5340 DK (net) | nRF5340_xxAA_NET | SWD |
| nRF9160 DK | nRF9160_xxAA | SWD |
| STM32F407 Discovery | STM32F407VG | SWD |
| STM32F746 Discovery | STM32F746ZG | SWD |
| STM32L476 Nucleo | STM32L476RG | SWD |
| ESP32 | ESP32 | JTAG |
| i.MX RT1060 EVK | MIMXRT1062xxx6A | SWD |

### J-Link Commander (JLinkExe) — Read-Only Operations

```bash
JLinkExe -device <DEVICE> -if SWD -speed 4000 -autoconnect 1

# Read memory (safe, read-only)
J-Link> mem 0x00000000 0x100    # Read 256 bytes from address 0
J-Link> mem32 0xE000ED28 1      # Read CFSR (1 word)

# Save memory to file (read-only)
J-Link> savebin dump.bin 0x20000000 0x10000   # Save 64KB RAM

# Read registers
J-Link> regs

# Halt/resume (safe for analysis)
J-Link> halt
J-Link> go

# Exit
J-Link> exit
```

### nrfjprog — Read-Only Operations

```bash
# Read memory
nrfjprog --memrd <address> --n <bytes>
nrfjprog --memrd 0x00000000 --n 256

# Read device info
nrfjprog --deviceversion
nrfjprog --memrd 0x10000100 --n 4   # FICR CODEPAGESIZE

# Read UICR
nrfjprog --memrd 0x10001000 --n 256

# List connected probes
nrfjprog --ids
```

### nRF5340 Dual-Core Setup

The nRF5340 has two cores, each requiring its own probe connection:

```bash
# Terminal 1: App core GDB server (default port 2331)
JLinkGDBServer -device nRF5340_xxAA_APP -if SWD -speed 4000

# Terminal 2: Net core GDB server (port 2332)
JLinkGDBServer -device nRF5340_xxAA_NET -if SWD -speed 4000 -port 2332 -select USB=<serial>

# GDB: Connect to app core
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :2331

# GDB: Connect to net core (separate GDB instance)
arm-zephyr-eabi-gdb build/hci_ipc/zephyr/zephyr.elf
(gdb) target remote :2332
```

## OpenOCD

### Configuration Files

OpenOCD uses two config files: interface (probe) + target (MCU).

```bash
# CMSIS-DAP probe with nRF52
openocd -f interface/cmsis-dap.cfg -f target/nrf52.cfg

# ST-Link with STM32F4
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# J-Link with STM32
openocd -f interface/jlink.cfg -f target/stm32f4x.cfg

# ESP32 with ESP-PROG
openocd -f board/esp32-wrover-kit-3.3v.cfg

# ESP32-C3 (RISC-V)
openocd -f board/esp32c3-builtin.cfg

# With explicit transport
openocd -f interface/cmsis-dap.cfg -c "transport select swd" -f target/nrf52.cfg
```

### Common Interface Files

| Probe | Config File |
|-------|------------|
| CMSIS-DAP | `interface/cmsis-dap.cfg` |
| ST-Link V2 | `interface/stlink-v2.cfg` |
| ST-Link V2-1 | `interface/stlink-v2-1.cfg` |
| ST-Link V3 | `interface/stlink.cfg` |
| J-Link | `interface/jlink.cfg` |
| FTDI-based | `interface/ftdi/olimex-arm-usb-ocd-h.cfg` |

### Common Target Files

| Target | Config File |
|--------|------------|
| nRF52 | `target/nrf52.cfg` |
| nRF53 | `target/nrf5340.cfg` |
| STM32F0 | `target/stm32f0x.cfg` |
| STM32F1 | `target/stm32f1x.cfg` |
| STM32F4 | `target/stm32f4x.cfg` |
| STM32F7 | `target/stm32f7x.cfg` |
| STM32L4 | `target/stm32l4x.cfg` |
| STM32H7 | `target/stm32h7x.cfg` |
| ESP32 | `target/esp32.cfg` |
| ESP32-S3 | `target/esp32s3.cfg` |
| ESP32-C3 | `target/esp32c3.cfg` |

## ST-Link

### st-flash (Read-Only Operations)

```bash
# Read flash to file
st-flash read dump.bin 0x08000000 0x10000   # Read 64KB from flash start

# Read device info
st-info --probe
st-info --serial
st-info --chipid
```

### STM32CubeProgrammer CLI (Read-Only)

```bash
# Connect and read
STM32_Programmer_CLI -c port=SWD -r32 0x08000000 256

# Read memory to file
STM32_Programmer_CLI -c port=SWD -u 0x08000000 0x10000 dump.bin

# Read option bytes
STM32_Programmer_CLI -c port=SWD -ob displ
```

## pyOCD

### Basic Usage

```bash
# List connected probes
pyocd list

# List supported targets
pyocd list --targets

# Install target pack
pyocd pack install nordic
pyocd pack install stm32f4

# Start GDB server
pyocd gdbserver --target nrf52840
pyocd gdbserver --target stm32f407xg

# With specific probe (by serial)
pyocd gdbserver --target nrf52840 --uid <serial>

# With specific port
pyocd gdbserver --target nrf52840 --port 3334
```

### pyOCD Commander (Read-Only)

```bash
pyocd commander --target nrf52840

# Read memory
>>> read32 0x00000000 16    # Read 16 words
>>> read8 0x20000000 64     # Read 64 bytes

# Read registers
>>> reg

# Core state
>>> status
```

## Troubleshooting

### Probe Not Detected

```bash
# Check USB
lsusb | grep -i "segger\|stlink\|cmsis\|ftdi"

# Check permissions (Linux)
ls -la /dev/ttyACM*
# If permission denied, add user to dialout group:
# sudo usermod -aG dialout $USER

# J-Link specific
JLinkExe -CommandFile /dev/null   # Should print J-Link info

# pyOCD specific
pyocd list --verbose
```

### Connection Issues

| Issue | Check |
|-------|-------|
| SWD speed too high | Reduce to 1000 kHz, increase gradually |
| Wrong interface | Try SWD vs JTAG |
| Flash locked | Check readback protection settings |
| Target in reset | Release NRESET pin, check reset circuitry |
| Power issue | Measure VCC at target, ensure probe powers target or external power is connected |

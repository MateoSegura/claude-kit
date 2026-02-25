# RTT and Serial Setup

Configuration reference for Segger RTT, UART serial logging, dual logging, and timestamp correlation in Zephyr RTOS.

## Segger RTT (Real-Time Transfer)

RTT provides high-speed bidirectional communication through the debug probe without dedicated serial pins.

### Zephyr RTT Configuration

```
# Enable RTT console
CONFIG_USE_SEGGER_RTT=y
CONFIG_RTT_CONSOLE=y
CONFIG_UART_CONSOLE=n

# Enable RTT as LOG backend
CONFIG_LOG=y
CONFIG_LOG_BACKEND_RTT=y
CONFIG_LOG_BACKEND_RTT_MODE_DROP=y    # Drop messages if buffer full (recommended)

# RTT buffer sizes
CONFIG_SEGGER_RTT_BUFFER_SIZE_UP=1024    # Target -> Host
CONFIG_SEGGER_RTT_BUFFER_SIZE_DOWN=16    # Host -> Target

# RTT channel count
CONFIG_SEGGER_RTT_MAX_NUM_UP_BUFFERS=3
CONFIG_SEGGER_RTT_MAX_NUM_DOWN_BUFFERS=3
```

### RTT Control Block Address

RTT uses a control block in RAM that the probe searches for. If auto-detection fails:

```bash
# Find RTT control block address from map file
grep "_SEGGER_RTT" build/zephyr/zephyr.map

# Specify manually in J-Link RTT Viewer
# Settings > RTT Control Block > Address: 0x2000XXXX
```

### RTT Viewer vs JLinkRTTClient

```bash
# JLinkRTTClient — simple terminal
# Requires JLinkGDBServer or JLinkExe already running
JLinkRTTClient

# JLinkRTTViewer — GUI with channel selection
JLinkRTTViewerExe

# JLinkRTTLogger — log to file
JLinkRTTLogger -device <DEVICE> -if SWD -speed 4000 -RTTChannel 0 output.log
```

### RTT Channel Configuration

Zephyr uses multiple RTT channels:

| Channel | Purpose | Direction |
|---------|---------|-----------|
| 0 | Console (printk, LOG) | Up (target -> host) |
| 1 | Shell (if CONFIG_SHELL_BACKEND_RTT) | Bidirectional |
| 2+ | Custom application channels | Configurable |

### Custom RTT Channel (for structured debug data)

```c
/* In application code */
#include <SEGGER_RTT.h>

/* Channel 2 for binary debug data */
static char rtt_buf[512];
SEGGER_RTT_ConfigUpBuffer(2, "DebugData", rtt_buf, sizeof(rtt_buf),
                          SEGGER_RTT_MODE_NO_BLOCK_SKIP);
```

## UART Serial Setup

### Zephyr UART Console Configuration

```
# Basic UART console
CONFIG_SERIAL=y
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y

# UART settings (usually inherited from board DTS)
# Override in prj.conf if needed:
CONFIG_UART_CONSOLE_ON_DEV_NAME="UART_0"

# LOG backend via UART
CONFIG_LOG=y
CONFIG_LOG_BACKEND_UART=y
```

### Common Baud Rates

| Board | Default Baud | Notes |
|-------|-------------|-------|
| nRF52840 DK | 115200 | Via on-board J-Link CDC |
| nRF5340 DK | 115200 | Via on-board J-Link CDC |
| nRF9160 DK | 115200 | Via on-board J-Link CDC |
| STM32 Nucleo | 115200 | Via ST-Link VCP |
| ESP32 DevKitC | 115200 | Via CP2102 USB-UART |
| Custom board | Varies | Check board DTS for `current-speed` |

### USB-UART Adapter Connection

```
# Find the serial device
ls /dev/ttyACM* /dev/ttyUSB*

# Connect with minicom
minicom -D /dev/ttyACM0 -b 115200

# Connect with screen
screen /dev/ttyACM0 115200

# Connect with picocom (recommended — clean exit with Ctrl-A Ctrl-X)
picocom -b 115200 /dev/ttyACM0

# Log to file while viewing
picocom -b 115200 /dev/ttyACM0 --logfile serial.log
```

### Flow Control

```
# Hardware flow control (RTS/CTS)
# In board overlay:
&uart0 {
    hw-flow-control;
};

# No flow control (default for most dev kits)
# Most USB-CDC virtual COM ports do not need flow control
```

## Dual Logging (RTT + UART)

Enable both backends simultaneously for redundancy or to separate debug channels:

```
CONFIG_LOG=y
CONFIG_LOG_BACKEND_RTT=y
CONFIG_LOG_BACKEND_UART=y

# Different log levels per backend
CONFIG_LOG_BACKEND_RTT_LOG_LEVEL_DBG=y    # Verbose on RTT
CONFIG_LOG_BACKEND_UART_LOG_LEVEL_INF=y   # Info only on UART
```

### When to Use Dual Logging

| Scenario | RTT | UART |
|----------|-----|------|
| Development with probe | Primary (fast, no pin cost) | Backup |
| Field debugging | Not available (no probe) | Primary |
| Production logging | Not available | Primary or disabled |
| Performance-critical timing | Primary (lower overhead) | Disabled |
| Customer-facing serial | Disabled | Primary |

## Runtime Log Filtering via Zephyr Shell

If `CONFIG_SHELL=y` and `CONFIG_LOG_RUNTIME_FILTERING=y`:

```
# Show current log levels
uart:~$ log status

# Set module log level at runtime
uart:~$ log enable dbg my_module
uart:~$ log disable my_module

# Set backend-specific level
uart:~$ log backend uart set_level inf
uart:~$ log backend rtt set_level dbg

# Halt/resume logging
uart:~$ log halt
uart:~$ log go
```

## Timestamp Correlation

When correlating events across RTT logs, UART logs, and GDB output, timestamps must be aligned.

### Zephyr Timestamp Source

```
# System clock based (default)
CONFIG_LOG_TIMESTAMP_64BIT=y

# Cycle-accurate timestamps
CONFIG_LOG_OUTPUT_FORMAT_TIMESTAMP_US=y
```

### Correlation Procedure

1. **Note the boot time** — Record the wall-clock time when the device boots (first log message).
2. **Use Zephyr uptime** — All Zephyr log timestamps are relative to boot. `k_uptime_get()` returns milliseconds since boot.
3. **GDB time reference** — When breaking in GDB, note the cycle counter or uptime to correlate with log timestamps.
4. **Cross-reference** — Match log timestamps to GDB events using the uptime offset.

```
# In GDB, read system uptime
(gdb) p k_uptime_get()
$1 = 12345    # milliseconds since boot

# Match this to log output timestamp
# [00:00:12.345] <inf> my_module: Event occurred
```

### Timestamp Accuracy

| Source | Resolution | Drift |
|--------|-----------|-------|
| CONFIG_SYS_CLOCK_TICKS_PER_SEC=1000 | 1ms | Low |
| CONFIG_SYS_CLOCK_TICKS_PER_SEC=10000 | 100us | Low |
| Cycle counter | CPU-clock dependent | None (hardware) |
| RTC-based | 30.5us (32768 Hz) | Depends on crystal |

# Zephyr GDB Reference

Complete GDB reference for Zephyr RTOS debugging: probe connection, thread inspection, memory examination, breakpoints, multi-image symbol loading, and core dump loading.

## Probe Connection

### J-Link GDB Server

```bash
# Basic SWD connection
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000

# With specific serial number (multi-probe setup)
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000 -select USB=<serial>

# Common device names
# nRF52840: nRF52840_xxAA
# nRF5340 app core: nRF5340_xxAA_APP
# nRF5340 net core: nRF5340_xxAA_NET
# STM32F4: STM32F407VG
# ESP32: ESP32 (requires ESP-specific J-Link)

# GDB connection
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :2331
(gdb) monitor reset halt
(gdb) load                    # Optional: reload firmware
(gdb) continue
```

### OpenOCD

```bash
# Generic CMSIS-DAP
openocd -f interface/cmsis-dap.cfg -f target/nrf52.cfg

# ST-Link
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# With specific transport
openocd -f interface/cmsis-dap.cfg -c "transport select swd" -f target/nrf52.cfg

# GDB connection
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :3333
(gdb) monitor reset halt
```

### pyOCD

```bash
# List connected probes
pyocd list

# Start GDB server
pyocd gdbserver --target <target_name>

# List supported targets
pyocd list --targets

# Install pack for target
pyocd pack install <vendor>

# GDB connection
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :3333
```

## Thread Inspection

### Listing Threads

```
(gdb) info threads
  Id   Target Id         Frame
* 1    Thread 1 "main"   0x00012345 in k_sem_take ()
  2    Thread 2 "idle"   0x00012678 in arch_cpu_idle ()
  3    Thread 3 "sysworkq" 0x00012abc in k_work_queue_run ()
```

### Thread State Analysis

```
# Switch to thread
(gdb) thread 3

# Full backtrace
(gdb) bt full

# Thread metadata
(gdb) p z_current_get()->base.name
(gdb) p z_current_get()->base.prio
(gdb) p z_current_get()->base.thread_state

# Thread state values:
#   0 = _THREAD_DUMMY
#   1 = _THREAD_PENDING (waiting on something)
#   2 = _THREAD_PRESTART (created but not started)
#   4 = _THREAD_DEAD (terminated)
#   8 = _THREAD_SUSPENDED
#  16 = _THREAD_ABORTING
#  32 = _THREAD_QUEUED (in ready queue)

# All thread backtraces
(gdb) thread apply all bt
(gdb) thread apply all bt full    # With local variables
```

### Kernel Object Inspection

```
# Mutex state
(gdb) p *(struct k_mutex *)<addr>
(gdb) p ((struct k_mutex *)<addr>)->owner           # Owning thread
(gdb) p ((struct k_mutex *)<addr>)->lock_count       # Nesting depth

# Semaphore state
(gdb) p *(struct k_sem *)<addr>
(gdb) p ((struct k_sem *)<addr>)->count              # Current count

# Message queue
(gdb) p *(struct k_msgq *)<addr>
(gdb) p ((struct k_msgq *)<addr>)->used_msgs         # Messages in queue

# Timer
(gdb) p *(struct k_timer *)<addr>
(gdb) p ((struct k_timer *)<addr>)->period            # Period in ticks

# Work queue
(gdb) p *(struct k_work_q *)<addr>
```

## Memory Examination

### Basic Memory Commands

```
# Examine memory at address
(gdb) x/16x 0x20000000          # 16 words in hex
(gdb) x/32xb 0x20000000         # 32 bytes in hex
(gdb) x/8xh 0x20000000          # 8 halfwords in hex
(gdb) x/s 0x20000100            # String at address

# Disassemble
(gdb) x/10i $pc                 # 10 instructions from PC
(gdb) disassemble <function>    # Disassemble entire function

# Memory regions
(gdb) info mem                   # Memory region info
(gdb) p/x &__rom_region_start
(gdb) p/x &__rom_region_end
(gdb) p/x &__ram_region_start
(gdb) p/x &__ram_region_end
```

### Fault Register Reading

```
# Cortex-M fault registers
(gdb) p/x *(uint32_t*)0xE000ED28   # CFSR
(gdb) p/x *(uint32_t*)0xE000ED2C   # HFSR
(gdb) p/x *(uint32_t*)0xE000ED30   # DFSR
(gdb) p/x *(uint32_t*)0xE000ED34   # MMFAR
(gdb) p/x *(uint32_t*)0xE000ED38   # BFAR

# NVIC registers
(gdb) x/8x 0xE000E100              # NVIC_ISER (enabled interrupts)
(gdb) x/8x 0xE000E200              # NVIC_ISPR (pending interrupts)
(gdb) x/8x 0xE000E300              # NVIC_IABR (active interrupts)
(gdb) x/64x 0xE000E400             # NVIC_IPR (interrupt priorities)

# Stacked exception frame
(gdb) x/8x $psp                    # Thread mode stack (most common in Zephyr)
(gdb) x/8x $msp                    # Handler mode stack
# Frame: R0, R1, R2, R3, R12, LR, PC, xPSR
```

## Breakpoints

### Hardware Breakpoints (for flash code)

```
# Hardware breakpoint (limited to 4-6 on most Cortex-M)
(gdb) hbreak main
(gdb) hbreak z_fatal_error          # Break on any fatal error
(gdb) hbreak arch_system_halt       # Break on system halt
(gdb) hbreak k_panic                # Break on kernel panic

# At specific address
(gdb) hbreak *0x00008000
```

### Conditional Breakpoints

```
# Break when variable has specific value
(gdb) break my_function if count > 100

# Break on specific error code
(gdb) break device_init if ret < 0

# Break on Nth hit
(gdb) break my_isr
(gdb) ignore 1 99                   # Skip first 99 hits
```

## Multi-Image Symbol Loading

For MCUboot + application or nRF53 dual-core builds, load symbols from multiple ELF files:

```
# Load application symbols (primary)
(gdb) file build/zephyr/zephyr.elf

# Add MCUboot symbols at its load address
(gdb) add-symbol-file build/mcuboot/zephyr/zephyr.elf 0x00000000

# nRF5340: Add network core symbols
# (Connect GDB to network core's GDB server port, typically :2332)
(gdb) add-symbol-file build/hci_ipc/zephyr/zephyr.elf <net_core_flash_base>

# Verify loaded symbols
(gdb) info files
```

### Finding Image Base Addresses

```bash
# From partition manager output
cat build/partitions.yml

# From devicetree
grep -A5 "boot_partition" build/zephyr/zephyr.dts
grep -A5 "slot0_partition" build/zephyr/zephyr.dts

# From MCUboot image header
arm-zephyr-eabi-objdump -h build/zephyr/zephyr.elf | head -20
```

## Core Dump Loading

### Zephyr Coredump (CONFIG_DEBUG_COREDUMP)

```bash
# Extract coredump from serial log
python3 -m west coredump extract <serial_log> -o coredump.bin

# Load into GDB
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target core coredump.bin
(gdb) bt
(gdb) info threads
(gdb) info registers
```

### J-Link Core Dump

```bash
# Save memory dump via J-Link Commander
JLinkExe -device <DEVICE> -if SWD -speed 4000
J-Link> savebin dump.bin <start_addr> <size>

# Load into GDB (requires ELF for symbols)
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) restore dump.bin binary <start_addr>
```

## Batch Mode Commands

For automated/scripted debugging (safe for read-only analysis):

```bash
# Run GDB commands non-interactively
arm-zephyr-eabi-gdb -batch \
  -ex "target remote :2331" \
  -ex "info threads" \
  -ex "thread apply all bt" \
  -ex "p/x *(uint32_t*)0xE000ED28" \
  -ex "p/x *(uint32_t*)0xE000ED2C" \
  -ex "quit" \
  build/zephyr/zephyr.elf

# From core dump
arm-zephyr-eabi-gdb -batch \
  -ex "target core coredump.bin" \
  -ex "bt full" \
  -ex "info registers" \
  -ex "quit" \
  build/zephyr/zephyr.elf
```

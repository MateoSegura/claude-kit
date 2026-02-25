# Crash Dump Reference

Detailed procedures for extracting, loading, and analyzing crash dumps from Zephyr RTOS firmware.

## Zephyr Coredump (CONFIG_DEBUG_COREDUMP)

### Configuration

```
# Enable coredump generation
CONFIG_DEBUG_COREDUMP=y

# Backend selection
CONFIG_DEBUG_COREDUMP_BACKEND_LOGGING=y      # Output via LOG (serial/RTT)
CONFIG_DEBUG_COREDUMP_BACKEND_FLASH_PARTITION=y  # Save to flash partition

# Memory regions to include
CONFIG_DEBUG_COREDUMP_MEMORY_DUMP_MIN=y      # Registers + current stack only
CONFIG_DEBUG_COREDUMP_MEMORY_DUMP_LINKER_RAM=y  # All RAM (larger but complete)
```

### Extraction from Serial Log

When `CONFIG_DEBUG_COREDUMP_BACKEND_LOGGING=y`, the coredump is output as base64-encoded data in the serial log:

```
[00:00:05.123] <err> os: >>> ZEPHYR FATAL ERROR 0: CPU exception on CPU 0
[00:00:05.123] <err> os: Current thread: 0x20001234 (main)
...
#CD:BEGIN#
#CD:AAAAAQAAAA...base64data...#
#CD:END#
```

```bash
# Extract coredump binary from serial log
python3 scripts/coredump/coredump_serial_log_parser.py serial.log coredump.bin

# Or using west (Zephyr SDK)
west coredump extract serial.log -o coredump.bin
```

### Extraction from Flash Partition

When `CONFIG_DEBUG_COREDUMP_BACKEND_FLASH_PARTITION=y`:

```bash
# Read coredump partition via J-Link
# First find partition address from DTS
grep -A5 "coredump_partition" build/zephyr/zephyr.dts

# Example: coredump at 0x000F0000, size 0x10000
JLinkExe -device <DEVICE> -if SWD -speed 4000
J-Link> savebin coredump_raw.bin 0x000F0000 0x10000

# Parse the raw flash dump
python3 scripts/coredump/coredump_flash_parser.py coredump_raw.bin coredump.bin
```

### Loading into GDB

```bash
# Basic loading
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target core coredump.bin

# Verify load
(gdb) bt                    # Should show backtrace
(gdb) info registers        # Should show register values
(gdb) info threads          # May show thread list (depends on dump completeness)

# If symbols don't match
(gdb) info files            # Check loaded sections
(gdb) info symbol <addr>    # Test if addresses resolve
```

### Coredump Format

Zephyr coredump uses a simple binary format:

| Offset | Size | Content |
|--------|------|---------|
| 0x00 | 4 | Magic: `CD` (0x43440001) |
| 0x04 | 2 | Version |
| 0x06 | 2 | Architecture (0=ARM, 1=x86, 2=Xtensa, 3=RISC-V) |
| 0x08 | var | Register block (architecture-dependent) |
| varies | var | Memory blocks (address + size + data) |

### Completeness Assessment

| Check | Command | Expected |
|-------|---------|----------|
| Registers present | `info registers` | All core registers visible |
| Stack readable | `x/32x $sp` | Valid stack data |
| Code readable | `x/4i $pc` | Valid instructions |
| Variables accessible | `p <global_var>` | Valid value (if RAM included) |
| Threads visible | `info threads` | Thread list (MIN dump may not have this) |

## J-Link Core Dump

### Saving Memory Dump

```bash
JLinkExe -device <DEVICE> -if SWD -speed 4000 -autoconnect 1

# Halt target first
J-Link> halt

# Save specific regions
J-Link> savebin ram_dump.bin 0x20000000 0x40000     # 256KB RAM
J-Link> savebin flash_dump.bin 0x00000000 0x100000  # 1MB Flash

# Save all relevant regions
J-Link> savebin vectors.bin 0x00000000 0x400        # Vector table
J-Link> savebin ram.bin 0x20000000 <ram_size>       # Full RAM
```

### Region Selection Guide

| Region | Address (typical) | Size | Purpose |
|--------|------------------|------|---------|
| Vector table | 0x00000000 | 0x400 | ISR entry points |
| Flash (code) | 0x00000000 | varies | Code and const data |
| SRAM | 0x20000000 | varies | Variables, stacks, heap |
| Peripheral regs | 0x40000000+ | varies | Hardware state |
| System regs | 0xE000E000 | 0x1000 | NVIC, SCB, fault regs |

### Loading into GDB

```bash
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf

# Restore RAM dump to correct address
(gdb) restore ram.bin binary 0x20000000

# Set registers manually (if saved separately)
(gdb) set $pc = 0x<value>
(gdb) set $sp = 0x<value>
(gdb) set $lr = 0x<value>

# Now examine
(gdb) bt
(gdb) info threads    # May not work without full Zephyr thread context
```

## Register Context Extraction

### From Serial Log (Cortex-M)

Zephyr's fatal error handler prints registers:

```
>>> ZEPHYR FATAL ERROR 0: CPU exception on CPU 0
Current thread: 0x20001234 (main)
 r0/a1:  0x00000000  r1/a2:  0x20002000
 r2/a3:  0x00000042  r3/a4:  0xDEADBEEF
r12/ip:  0x00000000 r14/lr:  0x00008A24
 r15/pc:  0x00008B10  xpsr:  0x21000000
Faulting instruction address: 0x00008B10
```

Extract key values:
- **PC** (0x00008B10): The faulting instruction
- **LR** (0x00008A24): The return address (caller)
- **SP**: Not always printed directly — check stacked frame

```bash
# Resolve addresses
arm-zephyr-eabi-addr2line -e build/zephyr/zephyr.elf -f -p 0x00008B10
arm-zephyr-eabi-addr2line -e build/zephyr/zephyr.elf -f -p 0x00008A24
```

### From Xtensa Backtrace (ESP32)

ESP32 prints a different format:

```
Backtrace: 0x400D1234:0x3FFB5678 0x400D5678:0x3FFB5690
```

Format: `<PC>:<SP>` pairs. Decode with:

```bash
# Use xtensa addr2line
xtensa-esp32-elf-addr2line -e build/zephyr/zephyr.elf -f -p 0x400D1234
```

### From RISC-V

```
>>> ZEPHYR FATAL ERROR 0: CPU exception on CPU 0
 mepc:   0x20010234
 mstatus: 0x00001880
 mcause:  0x00000005  (Load access fault)
 mtval:   0xDEAD0000
```

Key values:
- **mepc**: Faulting instruction address
- **mcause**: Exception cause code
- **mtval**: Faulting address (for memory access faults)

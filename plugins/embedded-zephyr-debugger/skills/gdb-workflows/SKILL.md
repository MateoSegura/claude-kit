---
name: embedded-zephyr-debugger:gdb-workflows
description: "GDB debugging workflows for Zephyr RTOS including probe connection, thread-aware inspection, memory examination, watchpoints, multi-image symbol loading, and core dump analysis. Quick reference for common GDB commands used in embedded firmware debugging."
user-invocable: false
---

# GDB Workflows Quick Reference

Common GDB commands and workflows for Zephyr RTOS debugging. Covers probe connection, thread inspection, memory analysis, and watchpoints.

## Probe Connection Quick Start

```bash
# J-Link
JLinkGDBServer -device <DEVICE> -if SWD -speed 4000 &
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf -ex "target remote :2331"

# OpenOCD
openocd -f interface/cmsis-dap.cfg -f target/<target>.cfg &
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf -ex "target remote :3333"

# pyOCD
pyocd gdbserver --target <target> &
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf -ex "target remote :3333"

# Core dump (offline)
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf -ex "target core <dump_file>"
```

## Thread-Aware Commands

Zephyr GDB integration provides thread awareness when connected to a live target:

```
info threads              # List all Zephyr threads with state
thread <N>                # Switch to thread N
thread apply all bt       # Backtrace ALL threads
thread apply all bt full  # Full backtrace with locals for ALL threads

# Thread details
p z_current_get()->base.name    # Current thread name
p z_current_get()->base.prio    # Current thread priority
p z_current_get()->base.sched_locked  # Scheduler lock count
```

## Memory Examination Essentials

```
x/Nx <addr>    # Examine N words at address
x/Nxb <addr>   # Examine N bytes
x/Nxh <addr>   # Examine N halfwords
x/s <addr>     # Print string at address
x/i <addr>     # Disassemble instruction at address
x/10i $pc      # Disassemble 10 instructions from PC

# Common Zephyr memory regions
p/x __rom_region_start    # Flash start
p/x __rom_region_end      # Flash end
p/x __ram_region_start    # RAM start
p/x __ram_region_end      # RAM end
```

## Breakpoint Types

```
# Software breakpoint (RAM only, unlimited)
break <function>
break <file>:<line>

# Hardware breakpoint (flash, limited to ~4-6)
hbreak <function>
hbreak *0x<address>

# Data watchpoint (triggers on memory access)
watch *(uint32_t*)0x<address>        # Write watchpoint
rwatch *(uint32_t*)0x<address>       # Read watchpoint
awatch *(uint32_t*)0x<address>       # Read/write watchpoint

# Conditional breakpoint
break <function> if <condition>
```

## Decision Tree: Which Workflow?

```
What do you have?
├── Live target with probe → See zephyr-gdb-reference.md
│   ├── Crash/fault → Set breakpoint in z_fatal_error, examine registers
│   ├── Hang → Break in, dump all threads, find blocked ones
│   └── Wrong behavior → Set watchpoints on suspect variables
├── Core dump file → Load with 'target core', see zephyr-gdb-reference.md
│   ├── Has register context → Decode fault registers, get backtrace
│   └── Memory only → Inspect stack, look for sentinel corruption
├── Serial/RTT log with addresses → Use addr2line, see postmortem-analysis
└── No artifacts → Ask user to reproduce with logging enabled
```

## Additional Resources
- For complete GDB reference including multi-image symbol loading and kernel object inspection, see [zephyr-gdb-reference.md](zephyr-gdb-reference.md)
- For concrete watchpoint recipes for common debugging scenarios, see [watchpoint-examples.md](watchpoint-examples.md)

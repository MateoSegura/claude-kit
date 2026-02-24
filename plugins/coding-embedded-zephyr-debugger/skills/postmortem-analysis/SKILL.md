---
name: coding-embedded-zephyr-debugger:postmortem-analysis
description: "Offline crash dump analysis, GDB core dump loading, flash forensics, MCUboot image header parsing, and retained RAM inspection for Zephyr RTOS firmware postmortem debugging. Reference for reconstructing crash context from saved dumps without a live target."
user-invocable: false
---

# Postmortem Analysis Quick Reference

Offline crash dump analysis when no live target is available. Covers dump formats, GDB loading, symbol matching, and evidence quality assessment.

## Crash Dump Formats

| Format | Source | Contents | GDB Support |
|--------|--------|----------|-------------|
| Zephyr coredump | CONFIG_DEBUG_COREDUMP | Registers + selected RAM | `target core` |
| J-Link memory dump | JLinkExe `savebin` | Raw memory regions | `restore` + manual |
| OpenOCD dump | `dump_image` command | Raw memory regions | `restore` + manual |
| Serial log with addresses | printk/LOG output | PC, LR, stack trace text | `addr2line` only |

## Offline GDB Workflow

```
1. Obtain the ELF file matching the firmware that crashed
2. Obtain the crash dump (coredump binary, memory dump, or serial log)
3. Load into GDB:
   arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
   (gdb) target core coredump.bin     # For Zephyr coredump
   (gdb) bt                           # Backtrace from crash point
   (gdb) info registers               # Register state at crash
   (gdb) info threads                 # Thread states (if available)
4. Decode fault registers from saved context
5. Correlate addresses with source using addr2line
```

## Symbol File Matching

The ELF file MUST match the firmware version that crashed. Mismatched symbols produce wrong source mappings.

**Verification:**
```bash
# Check build ID in ELF
arm-zephyr-eabi-readelf -n build/zephyr/zephyr.elf | grep "Build ID"

# Compare with running firmware (if accessible)
# Store build ID in firmware at build time for matching
```

## Evidence Quality Assessment

| Quality | Criteria | Confidence Impact |
|---------|----------|------------------|
| Complete dump | Full RAM + registers + flash | High confidence possible |
| Partial dump | Registers + stack only | Medium confidence typical |
| Serial log only | PC, LR, call trace text | Low-medium, depends on detail |
| Second-hand report | User description only | Low, triage only |

## Additional Resources
- For detailed crash dump extraction and GDB loading procedures, see [crash-dump-reference.md](crash-dump-reference.md)
- For MCUboot header parsing, swap status analysis, and flash forensics, see [flash-forensics.md](flash-forensics.md)

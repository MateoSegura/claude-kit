---
name: coding-embedded-zephyr-debugger:probe-setup
description: "Debug probe selection, configuration, and connection verification for Zephyr RTOS debugging. Covers J-Link, OpenOCD, ST-Link, and pyOCD setup, RTT and UART serial logging, and common probe failure troubleshooting."
user-invocable: false
---

# Probe Setup Quick Reference

Debug probe selection matrix, connection verification, and common failure troubleshooting.

## Probe Selection Matrix

| Target Family | Recommended Probe | Alternate | GDB Server Port |
|--------------|-------------------|-----------|----------------|
| Nordic (nRF52, nRF53, nRF91) | J-Link (on-board) | OpenOCD + CMSIS-DAP | 2331 |
| STM32 | ST-Link (on-board) | OpenOCD, J-Link | 3333 (OpenOCD), 2331 (J-Link) |
| ESP32 (Xtensa) | OpenOCD + ESP-PROG | J-Link | 3333 |
| ESP32-C3/C6 (RISC-V) | OpenOCD + ESP-PROG | J-Link | 3333 |
| NXP (i.MX RT, LPC, Kinetis) | J-Link or CMSIS-DAP | pyOCD | 2331 or 3333 |
| General / Multi-vendor | J-Link | pyOCD | 2331 |

## Connection Verification Steps

1. **Probe detected?** — `JLinkExe` or `pyocd list` should show the probe.
2. **Target detected?** — `monitor halt` in GDB or `JLinkExe > connect` should respond.
3. **Symbols loaded?** — `info functions main` should list main().
4. **Threads visible?** — `info threads` should list Zephyr threads (requires RTOS awareness).
5. **Breakpoint works?** — `hbreak main` + `continue` should hit.

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "No J-Link found" | USB not connected, driver missing | Check USB cable, install J-Link Software |
| "Could not connect to target" | Wrong device name, SWD/JTAG mismatch | Verify -device name, try -if JTAG |
| "Target not halted" | Target running, no debug access | `monitor reset halt`, check SWDIO/SWCLK |
| "No RTOS threads" | Thread awareness not loaded | Load Zephyr RTOS plugin for GDB |
| "Cannot set breakpoint" | Flash protection or breakpoint limit | Use `hbreak`, check flash protection |
| "Connection refused :2331" | GDB server not running | Start JLinkGDBServer first |
| "Remote connection closed" | Probe lost connection | Reduce SWD speed, check wiring |

## Additional Resources
- For complete probe configuration details (J-Link, OpenOCD, ST-Link, pyOCD), see [probe-reference.md](probe-reference.md)
- For RTT and UART serial setup, see [rtt-serial-setup.md](rtt-serial-setup.md)

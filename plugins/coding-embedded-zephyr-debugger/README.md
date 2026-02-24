# coding-embedded-zephyr-debugger

> **Role:** Debugger · **Version:** 0.0.5

Zephyr RTOS embedded debugger — diagnoses hard faults, memory corruption, kernel panics, stack overflows, peripheral failures, boot/MCUboot issues, network stack failures, and field-return crash dumps with structured evidence-based diagnostic reports.

```bash
claude-kit --kit coding-embedded-zephyr-debugger
# or load the full team:
claude-kit --kit coding-embedded-zephyr
```

**Companion auto-loaded:** `coding-embedded-zephyr-knowledge` (kernel APIs, devicetree, hardware targets, peripheral drivers, build system, design patterns)

---

## Agents

| Agent | Description |
|-------|-------------|
| `triage-analyst` | Classifies Zephyr RTOS debug artifacts into failure domains. Analyzes crash logs, serial dumps, GDB output, and symptom descriptions to determine which specialist debugger should investigate. Use when a debugging session begins and the failure type is unknown. |
| `fault-analyzer` | Diagnoses hard faults, memory corruption, and stack overflows in Zephyr RTOS firmware. Decodes CFSR/HFSR/MMFAR/BFAR (Cortex-M), EXCCAUSE (Xtensa), mcause (RISC-V). Use when triage classifies a failure as hard_fault or stack_overflow. |
| `kernel-debugger` | Diagnoses Zephyr RTOS kernel panics, deadlocks, ISR timing violations, and priority inversion. Inspects thread states, mutex hierarchies, and interrupt priorities. Use when triage classifies a failure as kernel_panic or deadlock_timing. |
| `peripheral-debugger` | Diagnoses Zephyr RTOS device driver failures, bus errors (I2C/SPI/UART/GPIO), DMA issues, and peripheral configuration problems. Analyzes devicetree bindings, pin mux settings, and driver initialization. Use when triage classifies a failure as peripheral_failure. |
| `boot-debugger` | Diagnoses MCUboot failures, DTS/Kconfig errors, partition layout mismatches, and sysbuild multi-image issues in Zephyr RTOS. Analyzes boot sequences, image signing, and swap/revert states. Use when triage classifies a failure as boot_failure. |
| `network-debugger` | Diagnoses BLE, LTE, WiFi, Thread, and Zigbee failures in Zephyr RTOS. Analyzes protocol state machines, connection parameters, modem traces, and socket errors. Use when triage classifies a failure as network_failure. |
| `postmortem-analyst` | Reconstructs crash context from offline dumps, flash forensics, and retained RAM data for Zephyr RTOS firmware. Analyzes core dumps, MCUboot image integrity, and swap status without a live target. Use when triage classifies a failure as postmortem or when no live target is available. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-embedded-zephyr-debugger:debug` | Triage and diagnose failures in Zephyr RTOS firmware. Classifies symptoms into failure domains, routes to specialist agents, and delivers structured diagnostic reports. Read-only — never writes or modifies code. |

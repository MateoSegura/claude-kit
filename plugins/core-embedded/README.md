# core-embedded

> **Role:** Knowledge companion · **Version:** 0.0.1

RTOS-agnostic embedded systems — RTOS fundamentals, memory management, power optimization, communication protocols, and HAL patterns.

This plugin is **auto-loaded as a companion** by any plugin with `domain: "embedded"` in its `ctl.json`. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `rtos-fundamentals` | Tasks/threads, priority scheduling (preemptive vs cooperative), synchronization primitives (semaphores, mutexes, condition variables), message queues, timers, interrupt handling (ISR design, deferred processing), watchdog patterns |
| `memory-management` | Static vs dynamic allocation tradeoffs, memory pools, stack sizing strategies, heap fragmentation prevention, memory-mapped I/O, DMA concepts, linker script basics (sections, placement) |
| `power-optimization` | Sleep modes (idle, standby, deep sleep), wake sources, peripheral clock gating, voltage scaling, duty cycling strategies, power state machines, battery monitoring |
| `comm-protocols` | SPI (modes, chip select), I2C (addressing, clock stretching), UART (baud rate, flow control), CAN bus basics, BLE concepts (GAP, GATT, advertising), TCP/IP on constrained devices (CoAP, MQTT-SN, LwM2M) |
| `hal-patterns` | Hardware abstraction layer design, register access patterns, peripheral driver lifecycle (init/configure/enable/disable), DMA-based transfers, interrupt-safe APIs, board support packages |

---

## Auto-Loading

This plugin is loaded automatically by any embedded-domain plugin that declares `"domain": "embedded"` in its `ctl.json`. It provides framework-agnostic fundamentals that complement RTOS-specific knowledge plugins (e.g., `embedded-zephyr-knowledge`).

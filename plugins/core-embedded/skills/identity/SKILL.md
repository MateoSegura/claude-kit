---
name: core-embedded:identity
description: "Domain overview for RTOS-agnostic embedded systems knowledge base"
user-invocable: false
---

# Embedded Systems — Domain Knowledge

This plugin provides shared domain reference material for embedded systems development. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent, RTOS-agnostic domain expertise.

## Domain Scope

- **RTOS fundamentals**: Tasks/threads, scheduling, synchronization primitives, interrupt handling, timers, watchdogs
- **Memory management**: Static vs dynamic allocation, memory pools, stack sizing, heap fragmentation, DMA, linker scripts
- **Power optimization**: Sleep modes, wake sources, clock gating, voltage scaling, duty cycling, power state machines
- **Communication protocols**: SPI, I2C, UART, CAN bus, BLE concepts, constrained-device networking (CoAP, MQTT-SN, LwM2M)
- **HAL patterns**: Hardware abstraction layer design, register access, peripheral driver lifecycle, interrupt-safe APIs, BSP design

## What This Plugin Contains

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains:

- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded)
- Reference files — Detailed patterns, design guidance, examples (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No RTOS-specific APIs (Zephyr, FreeRTOS, ThreadX, etc. are covered by their own knowledge plugins)
- No vendor-specific hardware details (covered by hardware-specific knowledge plugins)

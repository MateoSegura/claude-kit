---
name: coding-embedded-zephyr-knowledge:identity
description: "Domain overview for Zephyr RTOS embedded development knowledge base"
user-invocable: false
---

# Zephyr RTOS Embedded Development — Domain Knowledge

This plugin provides shared domain reference material for Zephyr RTOS embedded systems development. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent domain expertise.

## Domain Scope

- **RTOS**: Zephyr Project (v3.x+) — kernel primitives, scheduling, synchronization, memory management
- **Configuration**: Devicetree overlays, Kconfig symbols, board/SoC definitions
- **Build system**: West meta-tool, CMake, sysbuild, MCUboot integration
- **Hardware targets**: ESP32, Nordic nRF52/nRF53/nRF91, NXP i.MX RT, STM32 families
- **Networking**: Zephyr networking stack, Bluetooth LE, Thread, Matter, socket API
- **Security**: Secure boot (MCUboot), TF-M integration, hardware crypto
- **Serialization**: Protocol Buffers (nanopb), CBOR (zcbor), JSON
- **Testing**: Zephyr twister framework, QEMU/native_sim, Unity test harness
- **Design patterns**: Domain-specific initialization, concurrency, memory, communication, and error handling patterns

## What This Plugin Contains

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains:

- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded)
- Reference files — Detailed API docs, pattern catalogs, examples (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No role-specific identity or persona
- No role-specific hooks (only domain-wide safety hooks)

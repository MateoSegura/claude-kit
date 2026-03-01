---
name: embedded-zephyr-knowledge:identity
description: "Domain overview for Zephyr RTOS embedded development knowledge base"
user-invocable: false
---

# Zephyr RTOS Embedded Development — Domain Knowledge

This plugin provides shared domain reference material for Zephyr RTOS embedded systems development. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent domain expertise.

## Domain Scope

- **RTOS**: Zephyr Project (v3.x+) — kernel primitives, scheduling, synchronization, memory management
- **Configuration**: Devicetree overlays, Kconfig symbols, board/SoC definitions
- **Build system**: West meta-tool, CMake, sysbuild, MCUboot integration
- **Hardware targets**: Espressif ESP32/S2/S3/C3/C6/H2, Nordic nRF52/nRF53/nRF54/nRF91, NXP i.MX RT/LPC/Kinetis, STM32 F4/L4/H7/U5/WB families
- **Networking**: Zephyr networking stack, Bluetooth LE, Thread, Matter, socket API
- **Security**: Secure boot (MCUboot), TF-M integration, hardware crypto
- **Serialization**: Protocol Buffers (nanopb), CBOR (zcbor), JSON
- **Testing**: Zephyr twister framework, QEMU/native_sim, Unity test harness
- **Design patterns**: Domain-specific initialization, concurrency, memory, communication, and error handling patterns

## Expertise Areas

This knowledge base covers Zephyr-specific implementation details that go beyond what generic embedded references provide. Key expertise areas include:

- **Kernel internals**: Thread priority inversion handling, scheduler lock semantics, ISR-safe API usage rules, idle thread hooks, and tickless kernel configuration trade-offs
- **Memory strategies**: Static allocation via `K_HEAP_DEFINE`, memory slabs for fixed-size pools, `k_malloc` heap sizing, MPU-backed thread stack protection, and userspace memory domains
- **Devicetree mastery**: Overlay composition for multi-board support, `DT_NODELABEL` / `DT_ALIAS` resolution order, custom binding YAML for out-of-tree drivers, and chosen-node conventions for application-level peripherals
- **Multi-target firmware**: Sysbuild configuration for MCUboot + application image pairs, partition manager integration for Nordic boards, and DFU image signing workflows
- **Peripheral abstractions**: Zephyr's device driver model (`DEVICE_DT_INST_DEFINE`), sensor subsystem channels, GPIO callback registration, and the distinction between polling and interrupt-driven UART/SPI/I2C patterns
- **Power management**: Device PM actions, system PM policy selection, suspend-to-RAM vs. suspend-to-idle trade-offs, and SoC-specific deep-sleep errata workarounds

## Hardware Target Coverage

Four vendor-specific skills provide board-level detail for the most common Zephyr targets. Each covers peripheral initialization, clock tree configuration, power modes, errata workarounds, and vendor-specific tooling:

- **Nordic** (`hardware-nordic`): nRF Connect SDK overlay, SoftDevice controller vs. Zephyr BLE controller, nrfutil device management, SEGGER RTT logging
- **STM32** (`hardware-stm32`): CubeMX clock tree import, DMA channel assignment, low-power mode entry/exit sequences, ST-Link debugging
- **Espressif** (`hardware-espressif`): ESP-IDF component integration, WiFi/BLE coexistence scheduling, flash encryption, secure boot v2
- **NXP** (`hardware-nxp`): MCUXpresso SDK modules, FlexSPI configuration, i.MX RT crossover processor boot modes

## Skill Reference Map

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains a `SKILL.md` entry point (auto-loaded) and supplemental reference files (loaded on demand via Read).

| Skill | What It Provides |
|-------|-----------------|
| `zephyr-kernel` | Thread creation, semaphores, mutexes, message queues, work queues, timers, memory slabs — runtime vs. compile-time initialization guidance |
| `design-patterns` | Subsystem decomposition, initialization orchestration, state machines, memory management patterns, error handling — Zephyr-specific implementations |
| `devicetree-kconfig` | DTS overlay syntax, binding YAML, Kconfig fragments, shield definitions, board-level customization |
| `build-system` | West meta-tool, sysbuild, CMakeLists patterns, module manifests, out-of-tree builds |
| `networking-protocols` | TCP/IP stack, MQTT, CoAP, BLE, 802.15.4, OpenThread, LTE-M |
| `security-boot` | MCUboot chain-of-trust, TF-M secure partitions, key provisioning |
| `testing` | ztest framework, Twister runner, BabbleSim, Renode, coverage tooling |
| `serialization` | zcbor CDDL schemas, Protobuf in Zephyr (nanopb), CBOR patterns |
| `hardware-nordic` | nRF52/53/54/91 peripherals, power modes, BLE controller, nrfjprog/nrfutil, SEGGER RTT |
| `hardware-stm32` | STM32 F4/L4/H7/U5/WB clock tree, HAL integration, power modes, ST-Link/OpenOCD |
| `hardware-espressif` | ESP32/S2/S3/C3/C6/H2 GPIO matrix, WiFi/BLE coexistence, esptool, ESP-IDF integration |
| `hardware-nxp` | i.MX RT, LPC, Kinetis board support, MCUXpresso integration |

See also `coding-standards.md` for content accuracy and formatting conventions, and `workflow-patterns.md` for the consumption model and maintenance workflows.

## Core Companion Plugins

General-purpose knowledge that applies across all domains has been extracted into core plugins. Zephyr-specific content remains here. Core plugins that complement this domain knowledge:

- `core-architecture` — SOLID principles, GoF design patterns, clean architecture, API design
- `core-testing` — Test philosophy, test doubles, coverage strategy, TDD/BDD
- `core-security` — Secure coding, secrets management, dependency scanning, threat modeling
- `core-embedded` — RTOS fundamentals, HAL patterns, memory management, power optimization, communication protocols
- `core-git` — Git workflow, branching strategies, commit conventions

When a role plugin (engineer, grader, tester, debugger) references a concept covered by a core plugin, this knowledge plugin provides the Zephyr-specific implementation details while the core plugin supplies the underlying theory. For example, `core-embedded` covers generic RTOS scheduling theory; this plugin's `zephyr-kernel` skill covers Zephyr's cooperative vs. preemptive priority model, `CONFIG_NUM_PREEMPT_PRIORITIES`, and the meta-IRQ scheduling class.

## What This Plugin Does NOT Contain

- No agents — role plugins (engineer, grader, tester, debugger) provide those
- No commands — role plugins provide workflow orchestration commands
- No role-specific identity or persona — each role plugin defines its own
- No role-specific hooks — only domain-wide safety hooks live here
- No language-agnostic embedded theory — that belongs in `core-embedded`

# embedded-zephyr-knowledge

> **Role:** Knowledge companion · **Version:** 0.2.2

Shared domain knowledge for Zephyr RTOS embedded development — kernel APIs, devicetree, hardware targets, design patterns, build system, networking, security, and serialization reference material.

This plugin is **auto-loaded as a companion** by the engineer, grader, tester, and debugger plugins. Do not launch it directly.

General-purpose architecture, testing, and security knowledge has been extracted into core plugins (`core-architecture`, `core-testing`, `core-security`, `core-embedded`). This plugin retains **Zephyr-specific** content only and cross-references core plugins where appropriate.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `zephyr-kernel` | Kernel APIs: threads, semaphores, mutexes, message queues, work queues, timers, memory slabs |
| `design-patterns` | Zephyr-specific firmware patterns: subsystem decomposition, initialization orchestration, state machines, memory management, error handling. Generic design patterns in `core-architecture`. |
| `devicetree-kconfig` | DTS overlay syntax, binding YAML, Kconfig fragments, shield definitions |
| `build-system` | west commands, sysbuild, CMakeLists patterns, module manifests, out-of-tree builds |
| `networking-protocols` | TCP/IP stack, MQTT, CoAP, BLE, 802.15.4, OpenThread, LTE-M reference |
| `security-boot` | MCUboot chain-of-trust, TF-M secure partitions, key provisioning |
| `testing` | ztest framework, Twister runner, BabbleSim, Renode, coverage tooling |
| `serialization` | zcbor CDDL schemas, Protobuf in Zephyr, CBOR patterns |
| `hardware-nordic` | nRF52/53/54/91 families, peripherals, power modes, errata, BLE controller, nrfjprog/nrfutil, SEGGER RTT |
| `hardware-stm32` | STM32 F4/L4/H7/U5/WB families, clock tree configuration, HAL integration, power modes, ST-Link/OpenOCD |
| `hardware-espressif` | ESP32/S2/S3/C3/C6/H2 families, GPIO matrix, power modes, errata, WiFi/BLE coexistence, esptool, ESP-IDF integration |
| `hardware-nxp` | i.MX RT, LPC, Kinetis board support, MCUXpresso integration |

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `embedded-zephyr-engineer`
- `embedded-zephyr-grader`
- `embedded-zephyr-tester`
- `embedded-zephyr-debugger`

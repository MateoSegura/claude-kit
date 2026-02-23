# coding-embedded-zephyr-knowledge

> **Role:** Knowledge companion · **Version:** 0.0.0

Shared domain knowledge for Zephyr RTOS embedded development — kernel APIs, devicetree, hardware targets, design patterns, build system, networking, security, and serialization reference material.

This plugin is **auto-loaded as a companion** by the engineer and tester plugins. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `zephyr-kernel` | Kernel APIs: threads, semaphores, mutexes, message queues, work queues, timers, memory slabs |
| `design-patterns` | Zephyr idioms: runtime init, callback registration, subsystem drivers, error propagation |
| `devicetree-kconfig` | DTS overlay syntax, binding YAML, Kconfig fragments, shield definitions |
| `build-system` | west commands, sysbuild, CMakeLists patterns, module manifests, out-of-tree builds |
| `networking-protocols` | TCP/IP stack, MQTT, CoAP, BLE, 802.15.4, OpenThread, LTE-M reference |
| `security-boot` | MCUboot chain-of-trust, TF-M secure partitions, key provisioning |
| `testing` | ztest framework, Twister runner, BabbleSim, Renode, coverage tooling |
| `serialization` | zcbor CDDL schemas, Protobuf in Zephyr, CBOR patterns |
| `nordic-hardware` | nRF52, nRF53, nRF91 board files, softdevice, SEGGER RTT, nRF Connect SDK |
| `stm32-hardware` | STM32 board targets, STM32CubeIDE integration, HAL driver usage |
| `esp32-hardware` | ESP32 port specifics, Espressif IDF integration, wifi/BLE on ESP32 |
| `nxp-hardware` | i.MX RT, LPC, Kinetis board support, MCUXpresso integration |

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `coding-embedded-zephyr-engineer`
- `coding-embedded-zephyr-tester`
- `coding-embedded-zephyr-grader`

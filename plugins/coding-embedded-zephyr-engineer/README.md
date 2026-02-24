# coding-embedded-zephyr-engineer

> **Role:** Engineer · **Version:** 0.0.4

Zephyr RTOS embedded systems development agent — master-level firmware specialist with cloud-native patterns, runtime-driven initialization, full hardware portability, secure boot integration, and comprehensive architecture design patterns.

```bash
claude-kit --kit coding-embedded-zephyr-engineer
# or load the full team:
claude-kit --kit coding-embedded-zephyr
```

**Companion auto-loaded:** `coding-embedded-zephyr-knowledge` (kernel APIs, devicetree, hardware targets, design patterns)

---

## Agents

| Agent | Description |
|-------|-------------|
| `firmware-engineer` | Primary Zephyr firmware implementation agent. Writes C17 application code, device drivers, DTS overlays, Kconfig fragments, CMakeLists, west manifests, zcbor CDDL schemas, and protobuf definitions. Use when the user needs new code written, existing code modified, or any implementation task involving Zephyr RTOS firmware. |
| `devicetree-specialist` | Expert on Zephyr devicetree: writes DTS overlays, binding YAML files, pinctrl configurations, clock trees, flash partition layouts, shield overlays, and multi-instance peripheral setups. Use when the user needs help with devicetree configuration, hardware description, pin assignments, or when build errors involve DTS bindings. |
| `build-debug-analyst` | Expert diagnostician for Zephyr build failures, runtime crashes, hard faults, flash/debug issues, and hardware interaction problems. Use when the user reports errors, test failures, unexpected behavior, crash dumps, or needs help with west build/flash/debug commands. |
| `code-reviewer` | Reviews Zephyr firmware code for MISRA C:2012 compliance, Zephyr coding guidelines, the 10 non-negotiable anti-patterns, devicetree correctness, Kconfig completeness, memory safety, and architecture quality. Use when the user requests a code review, wants to check code quality, or before merging changes. |
| `test-engineer` | Creates and maintains Zephyr test suites using ztest, writes testcase.yaml configurations, manages twister execution, builds BabbleSim/Renode/HIL test harnesses, and generates coverage reports. Use when the user needs tests written, wants to run the test suite, or needs help with test infrastructure. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-embedded-zephyr-engineer:develop` | Primary entry point for firmware development. Routes feature builds, bug fixes, and refactors to the appropriate specialist subagent. Handles requirements analysis, context gathering, and agent dispatch. |
| `/coding-embedded-zephyr-engineer:review` | Performance-focused code review for Zephyr code. Analyzes memory usage, execution efficiency, Zephyr patterns, and MISRA compliance. Produces prioritized, actionable recommendations. Does NOT modify code. |

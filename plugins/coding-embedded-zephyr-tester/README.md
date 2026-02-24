# coding-embedded-zephyr-tester

> **Role:** Tester · **Version:** 0.0.3

Zephyr RTOS test engineering specialist — ztest unit/integration tests, twister execution, FFF mocking, gcov/lcov coverage analysis, test scaffolding, and CI-ready test infrastructure for embedded firmware.

```bash
claude-kit --kit coding-embedded-zephyr-tester
# or load the full team:
claude-kit --kit coding-embedded-zephyr
```

**Companion auto-loaded:** `coding-embedded-zephyr-knowledge` (kernel APIs, testing patterns, hardware reference)

---

## Agents

| Agent | Description |
|-------|-------------|
| `unit-test-writer` | Writes ztest unit test suites for Zephyr modules. Creates test_main.c files with ZTEST_SUITE, test cases, setup/teardown, FFF mocks, and testcase.yaml configuration. Targets native_sim for fast iteration. |
| `integration-test-writer` | Writes integration tests that validate subsystem interactions. Creates multi-module test scenarios targeting QEMU, BabbleSim (BLE), and Renode. Configures complex test fixtures with real Zephyr subsystems. |
| `mock-specialist` | Creates FFF (Fake Function Framework) mock configurations, custom fakes, and test doubles for Zephyr drivers and subsystems. Builds reusable mock libraries for hardware abstraction layers. |
| `test-runner` | Executes test suites via twister, interprets results, triages failures, and suggests fixes. Manages test platform selection (native_sim, QEMU, device), handles flaky test detection, and optimizes test execution time. |
| `coverage-analyzer` | Analyzes code coverage reports, identifies untested paths, and generates targeted test recommendations. Runs twister with coverage flags, parses gcov/lcov output, and produces actionable coverage improvement plans. |
| `test-reviewer` | Reviews test code for quality, coverage gaps, anti-patterns, and maintainability. Evaluates test isolation, assertion quality, mock correctness, and test naming. Provides structured feedback with severity ratings. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-embedded-zephyr-tester:scaffold-tests` | Test scaffolding orchestrator. Generates ztest file templates, testcase.yaml, and FFF mock stubs for a given source module. |
| `/coding-embedded-zephyr-tester:test` | Test execution orchestrator. Runs unit/integration tests via twister with platform selection, failure triage, and structured results output. |
| `/coding-embedded-zephyr-tester:coverage` | Coverage analysis orchestrator. Runs twister with `--coverage`, parses gcov/lcov reports, identifies untested paths, and produces a prioritized improvement plan. |

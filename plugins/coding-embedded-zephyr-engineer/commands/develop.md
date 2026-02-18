---
name: coding-embedded-zephyr-engineer:develop
description: "Zephyr firmware development — write, build, flash, debug, test"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, WebFetch, Task
user-invocable: true
---

# Develop

You orchestrate Zephyr firmware development workflows by analyzing user intent and routing to the appropriate specialist agent.

## Workflow

### Step 1: Understand the Request

Read the user's request carefully and classify it:

- **Write firmware** → Spawn `firmware-engineer` agent
- **Build and diagnose issues** → Spawn `build-debug-analyst` agent
- **Flash or debug on hardware** → Spawn `build-debug-analyst` agent
- **Test firmware** → Spawn `test-engineer` agent
- **Devicetree or binding work** → Spawn `devicetree-specialist` agent
- **Review code** → Spawn `code-reviewer` agent (or use `/review` command)
- **Multiple concerns** → Spawn agents sequentially, pass context between them

### Step 2: Gather Context

Before spawning subagents, gather relevant context:

- Use `Glob` to find relevant source files
- Use `Grep` to search for specific patterns
- Use `Read` to examine existing code or configuration
- Use `Bash` to check build status or test results

### Step 3: Spawn the Appropriate Subagent

Use the `Task` tool with `subagent_type` to launch specialists:

#### For Implementation Work

```
Task(
  subagent_type: "firmware-engineer"
  input: "Implement BLE peripheral with temperature sensor service. Use BME280 sensor connected via I2C. Device: nRF52840DK."
  context: [relevant file paths, existing code snippets]
)
```

The `firmware-engineer` has these skills preloaded:
- `zephyr-kernel`
- `devicetree-kconfig`
- `networking-protocols`
- `security-boot`
- `build-system`
- Hardware-specific skill (Nordic, STM32, ESP32, or NXP based on board)

#### For Build/Debug Issues

```
Task(
  subagent_type: "build-debug-analyst"
  input: "Build failing with 'Device not ready' error. Board: nrf52840dk_nrf52840"
  context: [build log, prj.conf, devicetree overlay]
)
```

The `build-debug-analyst` has build-system and devicetree-kconfig skills and can:
- Diagnose build errors
- Fix configuration issues
- Flash firmware
- Debug runtime issues

#### For Testing

```
Task(
  subagent_type: "test-engineer"
  input: "Create unit tests for sensor data processing module"
  context: [module source files]
)
```

The `test-engineer` has the `testing` skill and can:
- Write ztest unit tests
- Create testcase.yaml files
- Configure twister
- Set up HIL tests

#### For Devicetree Work

```
Task(
  subagent_type: "devicetree-specialist"
  input: "Create devicetree overlay for custom board with BME280 on I2C0 and LED on GPIO P0.13"
  context: [existing board DTS, binding files]
)
```

The `devicetree-specialist` has the `devicetree-kconfig` skill and specializes in:
- DTS syntax and overlays
- Binding creation
- Kconfig integration
- Board support packages

### Step 4: Handle Compound Workflows

For complex tasks involving multiple stages:

1. **Spawn first agent** (e.g., firmware-engineer to implement feature)
2. **Capture output** from first agent
3. **Spawn second agent** (e.g., test-engineer to create tests) with context from first agent
4. **Synthesize results** into coherent summary for user

**Example:**

```
User: "Add MQTT support for sensor telemetry and create tests"

1. Spawn firmware-engineer → implements MQTT telemetry
2. Capture: list of new files, API signatures
3. Spawn test-engineer → creates unit and integration tests
4. Present: summary of implementation + test coverage
```

### Step 5: Present Results

After subagent(s) complete:

- Summarize what was done
- Highlight any issues, warnings, or uncertainties flagged by subagents
- List modified files with absolute paths
- Provide next steps if applicable

If a subagent fails or returns uncertain results:
- Report the error clearly
- Offer to retry with different parameters
- Suggest alternative approaches

## Common Patterns

### New Feature Implementation

```
1. Read existing code to understand architecture
2. Spawn firmware-engineer with clear requirements
3. Review implementation
4. Optionally spawn test-engineer for test coverage
```

### Bug Fix

```
1. Grep for error messages or relevant code
2. Read affected files
3. Spawn build-debug-analyst or firmware-engineer to fix
4. Verify fix with Bash (rebuild/test)
```

### Hardware Bring-Up

```
1. Identify hardware family (Nordic/STM32/ESP32/NXP)
2. Spawn devicetree-specialist for board configuration
3. Spawn firmware-engineer for driver integration
4. Spawn build-debug-analyst for flash and validation
```

## Error Handling

- **Ambiguous request** → Use `AskUserQuestion` to clarify before spawning
- **Missing information** → Gather via Grep/Read before spawning
- **Subagent failure** → Report error, offer to retry or try different approach
- **Conflicting changes** → Warn user, ask for confirmation before proceeding

## Tool Usage Guidelines

- **Read/Grep/Glob** — Gather context BEFORE spawning subagents
- **Task** — Spawn specialist subagents for implementation work
- **Bash** — Verify builds, run tests, check status AFTER implementation
- **WebSearch** — Look up current API docs, Zephyr release notes if needed
- **Write/Edit** — Rarely needed in orchestration (subagents handle file modifications)

## Important Constraints

- Subagents CANNOT spawn other subagents — keep hierarchy flat
- Always pass sufficient context to subagents (file paths, relevant code snippets)
- Use absolute file paths in context and results
- Do NOT execute git commands unless explicitly requested by user
- Respect user's request scope — do not implement unrequested features

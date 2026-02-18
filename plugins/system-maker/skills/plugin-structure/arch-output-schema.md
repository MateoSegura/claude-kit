# Architecture Proposal — Output Schema

This is the complete JSON schema and example for the arch-designer agent's output. The arch-reviewer parses all three proposals (minimal, comprehensive, progressive) using this format.

## Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | string | "minimal", "comprehensive", or "progressive" |
| `agent_name` | string | Plugin name (framework-level, not target-specific) |
| `agent_name_rationale` | string | Why this name was chosen (required if different from input) |
| `knowledge_mode` | boolean | Whether to split domain knowledge into a companion plugin |
| `knowledge_plugin` | string | Companion plugin name (if knowledge_mode is true) |
| `knowledge_skills` | string[] | Skills that go in the knowledge plugin |
| `companions` | string[] | Companion plugin names |
| `domain_hierarchy` | object | **REQUIRED** — framework/target/tooling decomposition |
| `directory_tree` | string | ASCII tree of the complete plugin structure |
| `components` | object | All commands, agents, skills, lsp_config, hooks, mcp_servers |
| `roadmap` | object | Progressive strategy only — phased additions |
| `trade_offs` | string[] | Acknowledged limitations of this design |
| `estimated_files` | integer | Total file count |

## Complete Example (Progressive Strategy)

```json
{
  "strategy": "progressive",
  "agent_name": "coding-embedded-zephyr-engineer",
  "agent_name_rationale": "Zephyr RTOS is the framework layer. ESP32 is a hardware target — one of many. The agent generalizes to all Zephyr-supported boards.",
  "knowledge_mode": true,
  "knowledge_plugin": "coding-embedded-zephyr-knowledge",
  "knowledge_skills": ["zephyr-kernel", "devicetree-kconfig", "design-patterns"],
  "companions": ["coding-embedded-zephyr-knowledge"],
  "domain_hierarchy": {
    "framework_layer": {
      "name": "Zephyr RTOS",
      "description": "Real-time operating system with device driver model, kernel primitives, and networking stack",
      "becomes": "Agent identity + core framework skills (zephyr-kernel, devicetree)"
    },
    "target_layer": {
      "name": "ESP32",
      "description": "Espressif ESP32 SoC — Xtensa LX6 dual-core, WiFi/BLE, specific peripheral set",
      "becomes": "Extension skill (esp32-hardware/) — removable, replaceable with nrf52-hardware/, stm32-hardware/, etc."
    },
    "tooling_layer": {
      "name": "west + esptool + clangd",
      "description": "Build system (west), flash tool (esptool for ESP32), language server (clangd for C)",
      "becomes": "LSP config (.lsp.json) + tool-specific hooks + optional MCP servers"
    },
    "generalization_proof": "Adding nRF52 support requires ONLY creating skills/nrf52-hardware/. Zero changes to agents, commands, hooks, or core skills."
  },
  "directory_tree": "coding-embedded-zephyr-engineer/\n├── .claude-plugin/\n│   └── plugin.json\n├── .lsp.json\n├── commands/\n│   └── develop.md\n├── agents/\n│   ├── code-writer.md\n│   └── debug-assistant.md\n├── skills/\n│   ├── identity/\n│   │   ├── SKILL.md\n│   │   ├── coding-standards.md\n│   │   └── workflow-patterns.md\n│   └── esp32-hardware/\n│       ├── SKILL.md\n│       └── reference.md\n├── hooks/\n│   └── hooks.json\n└── scripts/\n    ├── block-dangerous.sh\n    └── lint-after-write.sh",
  "components": {
    "commands": [
      {
        "name": "develop",
        "file": "commands/develop.md",
        "purpose": "Primary entry point for development tasks",
        "subagents_spawned": ["code-writer", "debug-assistant"],
        "rationale": "Single command that routes to the right specialist"
      }
    ],
    "agents": [
      {
        "name": "code-writer",
        "file": "agents/code-writer.md",
        "role": "Writes and modifies application code",
        "model": "sonnet",
        "model_justification": "Code generation is sonnet's strength",
        "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
        "skills": ["identity", "esp32-hardware"],
        "color": "#32CD32",
        "rationale": "Separating code writing from debugging prevents context pollution"
      }
    ],
    "skills": [
      {
        "name": "identity",
        "directory": "skills/identity/",
        "files": ["SKILL.md", "coding-standards.md", "workflow-patterns.md"],
        "content_areas": ["Agent persona", "Non-negotiable rules", "Coding conventions"],
        "used_by": ["code-writer", "debug-assistant"],
        "user_invocable": false,
        "rationale": "Centralizes identity so all agents share the same methodology"
      },
      {
        "name": "esp32-hardware",
        "directory": "skills/esp32-hardware/",
        "files": ["SKILL.md", "reference.md"],
        "content_areas": ["ESP32 pinmux", "WiFi/BLE", "esptool config"],
        "used_by": ["code-writer"],
        "layer": "target",
        "rationale": "Target-specific knowledge isolated as an extension"
      }
    ],
    "lsp_config": {
      "file": ".lsp.json",
      "servers": [
        {
          "name": "clangd",
          "command": "clangd",
          "args": ["--background-index"],
          "languages": {"c": [".c", ".h"], "cpp": [".cpp", ".hpp"]},
          "rationale": "C/C++ diagnostics and completions for kernel code"
        }
      ]
    },
    "hooks": [
      {
        "event": "PreToolUse",
        "matcher": "Bash",
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/block-dangerous.sh",
        "category": "dangerous-command-blocking",
        "purpose": "Block dangerous commands without confirmation",
        "rationale": "Safety net for destructive operations"
      },
      {
        "event": "PostToolUse",
        "matcher": "Write|Edit",
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint-after-write.sh",
        "category": "smart-linting",
        "purpose": "Run domain-specific linting after code writes",
        "rationale": "Catch anti-patterns that the language server misses"
      },
      {
        "event": "Stop",
        "matcher": "",
        "type": "agent",
        "prompt": "Verify build compiles and no TODOs remain",
        "timeout": 30,
        "category": "work-verification",
        "purpose": "Prevent stopping with broken work",
        "rationale": "Embedded builds have long feedback cycles"
      }
    ],
    "mcp_servers": []
  },
  "roadmap": {
    "phase_2": {
      "timeline": "Week 2-3",
      "additions": [
        {
          "name": "nrf52-hardware skill",
          "files_to_create": ["skills/nrf52-hardware/SKILL.md", "skills/nrf52-hardware/reference.md"],
          "files_to_modify": [],
          "capability_unlocked": "Full Nordic nRF52 support"
        }
      ]
    }
  },
  "trade_offs": [
    "Only one target extension skill in Phase 1",
    "MCP deferred to later phases"
  ],
  "estimated_files": 14
}
```

## Hook Categories (Required)

Every architecture MUST include at least one hook from each category:

| Category | Event | Type | Purpose |
|----------|-------|------|---------|
| `dangerous-command-blocking` | PreToolUse | command | Block risky shell commands |
| `smart-linting` | PostToolUse | command/prompt | Domain-specific code quality checks |
| `work-verification` | Stop | agent/prompt | Verify work before session ends |
| `async-test-running` | PostToolUse | command | Background test execution |

## Model Assignment Rules

| Model | Use For |
|-------|---------|
| opus | Complex reasoning, multi-step analysis, debugging |
| sonnet | Code generation, structured output |
| haiku | Simple validation, format checking |

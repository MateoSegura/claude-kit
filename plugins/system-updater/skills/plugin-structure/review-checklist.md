# Plugin Review Checklist

Comprehensive check tables used by the plugin-reviewer agent. Execute ALL checks for ALL applicable files.

## Category 1: Structure & File Inventory

| Check ID | Check | Severity |
|----------|-------|----------|
| S1 | `.claude-plugin/plugin.json` exists | CRITICAL |
| S2 | `hooks/hooks.json` exists | CRITICAL |
| S3 | `skills/identity/SKILL.md` exists | CRITICAL |
| S4 | `skills/identity/coding-standards.md` exists | CRITICAL |
| S5 | `skills/identity/workflow-patterns.md` exists | CRITICAL |
| S6 | Every skill in APPROVED_ARCH has a `skills/<name>/SKILL.md` | CRITICAL |
| S7 | Every agent in APPROVED_ARCH has an `agents/<name>.md` file | CRITICAL |
| S8 | Every command in APPROVED_ARCH has a `commands/<name>.md` file | CRITICAL |
| S9 | Every script referenced in hooks.json exists in `scripts/` | CRITICAL |
| S10 | NO `CLAUDE.md` file exists anywhere in the build | CRITICAL |
| S11 | No unexpected files exist that aren't in the architecture or standard files | WARNING |

## Category 2: JSON Validity

| Check ID | Check | Severity |
|----------|-------|----------|
| J1 | `plugin.json` parses as valid JSON | CRITICAL |
| J2 | `plugin.json` has `name` field | CRITICAL |
| J3 | `plugin.json` has `description` field | WARNING |
| J4 | `plugin.json` has `version` field | WARNING |
| J5 | `hooks.json` parses as valid JSON | CRITICAL |
| J6 | `hooks.json` has top-level `"hooks"` object | CRITICAL |
| J7 | `hooks.json` uses event-based keys inside `"hooks"` (e.g., `PreToolUse`, `PostToolUse`, `Stop`) | CRITICAL |
| J8 | `.mcp.json` (if present) parses as valid JSON and has `mcpServers` key | CRITICAL |
| J9 | `.lsp.json` (if present) parses as valid JSON | CRITICAL |

## Category 3: Agent Frontmatter

For EACH agent file in `agents/*.md`, check ALL of these:

| Check ID | Check | Severity |
|----------|-------|----------|
| A1 | File starts with `---` YAML frontmatter delimiter | CRITICAL |
| A2 | Frontmatter contains `name:` field | CRITICAL |
| A3 | Frontmatter contains `model:` field with value `opus`, `sonnet`, or `haiku` | CRITICAL |
| A4 | Frontmatter contains `description:` field (quoted string) | CRITICAL |
| A5 | Frontmatter contains `tools:` field (NOT `allowed-tools:`) | CRITICAL |
| A6 | Frontmatter contains `skills:` field | CRITICAL |
| A7 | `skills:` list includes `identity` | CRITICAL |
| A8 | Frontmatter contains `permissionMode:` field with value `plan`, `acceptEdits`, or `default` | CRITICAL |
| A9 | Frontmatter contains `color:` field with a hex color value | WARNING |
| A10 | Read-only agents (tools lack Write AND Edit) use `permissionMode: plan` | WARNING |
| A11 | Write agents (tools include Write or Edit) use `permissionMode: acceptEdits` | WARNING |
| A12 | Frontmatter does NOT contain `allowed-tools:` (wrong field name for agents) | CRITICAL |

## Category 4: Command Frontmatter

For EACH command file in `commands/*.md`, check ALL of these:

| Check ID | Check | Severity |
|----------|-------|----------|
| C1 | File starts with `---` YAML frontmatter delimiter | CRITICAL |
| C2 | Frontmatter contains `description:` field | CRITICAL |
| C3 | Frontmatter contains `allowed-tools:` field (NOT `tools:`) | CRITICAL |
| C4 | Frontmatter does NOT contain `tools:` as a field name (wrong for commands) | CRITICAL |
| C5 | If the command spawns subagents, `Task` is in the allowed-tools list | WARNING |
| C6 | If the command uses AskUserQuestion, it's in the allowed-tools list | WARNING |

## Category 5: Skill Frontmatter

For EACH skill's SKILL.md file, check ALL of these:

| Check ID | Check | Severity |
|----------|-------|----------|
| K1 | File starts with `---` YAML frontmatter delimiter | CRITICAL |
| K2 | Frontmatter contains `name:` field | CRITICAL |
| K3 | Frontmatter contains `description:` field | CRITICAL |
| K4 | Identity skill has `user-invocable: false` | CRITICAL |
| K5 | Skill name in frontmatter is `plugin-name:directory-name` (e.g., `coding-foo:identity` for `skills/identity/`). The portion after `:` must match the directory name. | WARNING |

## Category 6: Hooks Correctness

| Check ID | Check | Severity |
|----------|-------|----------|
| H1 | hooks.json top-level structure is `{"hooks": {...}}` | CRITICAL |
| H2 | Every hook group object has a `"matcher"` field (string, can be empty `""`) | CRITICAL |
| H3 | Every hook entry has a `"type"` field with value `"command"`, `"prompt"`, or `"agent"` | CRITICAL |
| H4 | At least one `PreToolUse` hook exists | WARNING |
| H5 | At least one `PostToolUse` hook exists | WARNING |
| H6 | At least one `Stop` hook exists | WARNING |
| H7 | At least one `command`-type hook is used somewhere | WARNING |
| H8 | At least one `prompt`-type hook is used somewhere | WARNING |
| H9 | At least one `agent`-type hook is used somewhere | SUGGESTION |
| H10 | All `command`-type hooks reference scripts that exist (map `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` to `scripts/<name>` in build dir) | CRITICAL |
| H11 | All `prompt`-type hooks end with verdict format instruction (prompt text contains `"ok"` somewhere) | WARNING |
| H12 | All `agent`-type hooks have a `"timeout"` field | WARNING |
| H13 | All script files referenced by hooks have a shebang line (`#!/bin/bash` or `#!/usr/bin/env bash`) | WARNING |
| H14 | PreToolUse command hooks use `exit 2` for blocking (grep the script source) | WARNING |

## Category 7: Cross-Reference Integrity

| Check ID | Check | Severity |
|----------|-------|----------|
| X1 | Every skill name in every agent's `skills:` list has a corresponding `skills/<name>/SKILL.md` | CRITICAL |
| X2 | Every `subagent_type` value referenced in command files has a corresponding `agents/<name>.md` | CRITICAL |
| X3 | Every script path in hooks.json maps to an existing file in `scripts/` | CRITICAL |
| X4 | Agent names in frontmatter match their filenames (e.g., `name: foo` is in `agents/foo.md`) | WARNING |
| X5 | Command descriptions don't reference nonexistent subagent types | WARNING |

## Category 8: Content Quality

| Check ID | Check | Severity |
|----------|-------|----------|
| Q1 | Identity SKILL.md is >80 lines (has real substance) | CRITICAL |
| Q2 | Identity SKILL.md contains a non-negotiables section (search for "non-negotiable" or numbered hard rules) | CRITICAL |
| Q3 | Identity SKILL.md contains a methodology or workflow section | WARNING |
| Q4 | Identity SKILL.md references coding-standards.md and workflow-patterns.md | WARNING |
| Q5 | coding-standards.md is >40 lines with domain-specific content (not generic boilerplate) | WARNING |
| Q6 | workflow-patterns.md is >40 lines with concrete step-by-step workflows | WARNING |
| Q7 | Each non-identity skill SKILL.md is >30 lines | WARNING |
| Q8 | Each non-identity skill has at least one supplementary file (reference.md, examples.md, etc.) | WARNING |
| Q9 | Each agent file is 40-300 lines (not too thin, not bloated) | WARNING |
| Q10 | Each agent file has a `<role>` or role description section | WARNING |
| Q11 | Each agent file has an `<input>` or input description section | WARNING |
| Q12 | Each agent file has a process, steps, or workflow section | WARNING |
| Q13 | Each command file has a clear workflow with steps | WARNING |
| Q14 | No file contains only headers with no content (skeleton files with <20 lines of actual content) | CRITICAL |
| Q15 | No file has excessive TODO/FIXME/PLACEHOLDER markers (>3 per file) | WARNING |
| Q16 | For coding-type plugins: at least one skill covers design patterns or architecture principles | WARNING |
| Q17 | For coding-type plugins: design patterns skill includes patterns-reference.md and anti-patterns.md | SUGGESTION |

## Category 9: Anti-Pattern Detection

| Check ID | Check | Severity |
|----------|-------|----------|
| P1 | No `CLAUDE.md` exists anywhere | CRITICAL |
| P2 | No agent file uses `allowed-tools:` (should be `tools:`) | CRITICAL |
| P3 | No command file uses `tools:` as a standalone field (should be `allowed-tools:`) | CRITICAL |
| P4 | No agent is missing `identity` in its skills list | CRITICAL |
| P5 | No hook group is missing the `matcher` field | CRITICAL |
| P6 | No `plan`-mode agent has Write or Edit in its tools list | WARNING |
| P7 | No skill SKILL.md exceeds 500 lines | WARNING |
| P8 | No file contains hardcoded `/tmp/` build paths that should use `${CLAUDE_PLUGIN_ROOT}` | WARNING |
| P9 | No hooks.json uses old-style flat array format instead of event-based keys | CRITICAL |
| P10 | plugin.json `name` field matches the AGENT_NAME | WARNING |

## Category 10: Knowledge Plugin Checks

Only run these checks when the plugin's ctl.json has `"role": "knowledge"`.

| Check ID | Check | Severity |
|----------|-------|----------|
| KN1 | No `agents/` directory exists. Knowledge plugins must not contain agent definitions. | CRITICAL |
| KN2 | No `commands/` directory exists. Knowledge plugins must not contain command files. | CRITICAL |
| KN3 | Identity SKILL.md is under 60 lines. Knowledge plugin identities should be minimal domain overviews. | WARNING |
| KN4 | No persona, non-negotiables, or methodology sections in identity. These belong in role plugins. | WARNING |
| KN5 | ctl.json has no `companions` field. Knowledge plugins should not reference companions. | INFO |

## Category 11: Companion Checks

Only run these checks when the plugin's ctl.json has a `companions` array.

| Check ID | Check | Severity |
|----------|-------|----------|
| CO1 | Every plugin listed in `companions` exists in the installed plugins directory (`$CLAUDE_KIT_OUTPUT_DIR/`). | CRITICAL |
| CO2 | Agent frontmatter `skills:` lists reference skills that exist either in this plugin's `skills/` directory OR in a companion plugin's `skills/` directory. Flag any skill reference that cannot be found in either location. | WARNING |
| CO3 | No domain reference skills are duplicated between this plugin and its companions. If a skill directory exists in both, flag as duplication. | WARNING |
| CO4 | ctl.json has a `role` field. Plugins with companions should declare their role in ctl.json. | INFO |
| CO5 | plugin.json contains ONLY `name`, `description`, and `version`. Any other fields (`role`, `keywords`, `companions`, `author`, `license`) cause Claude Code to silently fail to load the plugin. If extra fields are found, flag as CRITICAL. | CRITICAL |

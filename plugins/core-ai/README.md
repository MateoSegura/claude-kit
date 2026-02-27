# core-ai

> **Role:** System · **Version:** 0.0.1

Repository instrumentation for AI-assisted development — analyzes repos, generates `.claude/` rules, commands, and hooks that encode conventions into enforceable context.

```bash
claude-kit --kit core-ai
```

---

## Agents

| Agent | Description |
|-------|-------------|
| `repo-analyzer` | Read-only repository scanner — analyzes file system, configs, git history, and existing .claude/ setup to build a structured detection model JSON for instrumentation. |
| `rule-generator` | Generates .claude/rules/*.md files from the detection model and user answers. Each rule file includes a provenance header and is scoped to a single convention category. |
| `command-generator` | Generates .claude/commands/*.md files from the detection model and user workflow descriptions. Each command orchestrates a repeatable multi-step workflow with correct frontmatter. |
| `hook-generator` | Generates .claude/hooks.json and supporting scripts for automated convention enforcement. Only generates hooks when the user explicitly opts into enforcement. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/core-ai:instrument` | Analyze a repository and generate tailored .claude/ rules, commands, and hooks. Walks through a 4-phase process: detect, confirm, generate, manifest. |

---

## Skills

| Skill | Description |
|-------|-------------|
| `identity` | Core identity, philosophy, and non-negotiable rules for the core-ai plugin. |
| `instrumentation` | Instrumentation theory, 4-phase process overview, detection patterns, and output templates. |

---

## How It Works

1. **Detect** — The repo-analyzer scans your repository: file system, configs, git history, existing `.claude/` setup
2. **Confirm** — Presents findings and asks 3-5 clarifying questions (workflows, boundaries, enforcement level)
3. **Generate** — Spawns rule/command/hook generators in parallel to create `.claude/` files
4. **Manifest** — Creates `.claude/.instrumentation.json` for idempotent re-runs and drift detection

### Instrumentation Modes

- **Greenfield** — No existing `.claude/` config. Full detection + guided generation.
- **Partial** — Some rules/commands exist. Gap analysis + augmentation without overwriting.
- **Re-instrumentation** — Previously instrumented. Drift detection + targeted updates.

### What Gets Generated

- **Rules** (`.claude/rules/*.md`) — Convention documentation loaded every session
- **Commands** (`.claude/commands/*.md`) — Repeatable workflow orchestration
- **Hooks** (`.claude/hooks.json`) — Automated enforcement (opt-in only)
- **Manifest** (`.claude/.instrumentation.json`) — State tracking for re-runs

# system-updater

> **Role:** System · **Version:** 0.0.4

Agent Updater — guides users through enhancing existing Claude Code plugins via a structured 7-phase workflow with fitness checking, surgical change planning, and staging-based safe implementation.

```bash
claude-kit --kit system-updater
```

**Companion auto-loaded:** `core-spec` (spec-driven development and progress tracking)

---

## Agents

| Agent | Description |
|-------|-------------|
| `plugin-analyzer` | Deep-analyzes an existing Claude Code plugin: reads every file, catalogs the structure, understands the domain identity, and produces a structured inventory. Use in Phase 2 of the update workflow. |
| `change-planner` | Analyzes a user's update request against an existing plugin's structure, determines if the change belongs in this plugin or needs a new one, and produces a surgical change plan. Use in Phase 3 of the update workflow. |
| `change-writer` | Implements a specific file change from the approved change plan — creates new files or modifies existing ones following the plugin's established patterns. Launched once per independent change or group of related changes. |
| `plugin-reviewer` | Exhaustive quality auditor for staged plugins. Performs a 9-category deep review covering structure, frontmatter, cross-references, content quality, hooks, JSON validity, and anti-patterns. Returns a graded report with categorized findings and specific fix instructions. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/system-updater:update-agent` | Plugin enhancement orchestrator. Guides through a 7-phase workflow (plugin selection → analysis → fitness check → approval → implementation → deep review → finalization) with timestamped backups and staging-based safety. |

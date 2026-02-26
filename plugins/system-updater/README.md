# system-updater

> **Role:** System · **Version:** 0.3.0

Team Updater — guides users through enhancing existing Claude Code plugins via structured workflows with fitness checking, surgical change planning, and staging-based safe implementation. Supports batched team-wide updates and comprehensive plugin review.

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
| `plugin-reviewer` | Exhaustive quality auditor for newly built plugins. Performs a 9-category deep review covering structure, frontmatter, cross-references, content quality, hooks, JSON validity, and anti-patterns. Returns a graded report with categorized findings and specific fix instructions. Use during Phase 10 after all plugin files are assembled. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/system-updater:update-team` | Team update orchestrator. Updates all members of a domain team (or a subset) in one session with shared intent, parallel analysis, per-plugin fitness checking, batched implementation, and sequential review. |
| `/system-updater:review-all` | Read-only parallel review of all plugins (or a filtered subset). Spawns batched plugin-reviewer agents (5 per batch) via team-lead pattern, aggregates per-plugin grades into a health summary. |
| `/system-updater:review-and-fix-all` | Full review-and-fix cycle for all plugins. Reviews in parallel batches, applies mechanical fixes directly, dispatches change-writer teams for content/structural fixes, re-reviews fixed plugins, and presents before/after grade comparison with user approval gate before finalizing. |

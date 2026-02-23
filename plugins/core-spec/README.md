# core-spec

> **Role:** System · **Version:** 0.0.0

Spec-driven development for long-running Claude Code sessions — write the spec first, derive implementation phases from it, track progress via file-based state, and recover context after compaction through hooks and agents.

```bash
claude-kit --kit core-spec
```

---

## Agents

| Agent | Description |
|-------|-------------|
| `plan-verifier` | Checks plan consistency at session end — verifies no in-progress tasks are left hanging and status.log matches TaskList state. |
| `context-recovery` | Reads plan files after context compaction and outputs a structured summary to restore Claude's orientation. Uses state.json fast path when available; falls back to status.log parsing. Read-only agent — no edits. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/core-spec:new` | Start a new spec-driven development session. Creates or loads a specification document, derives implementation phases, and initializes file-based state tracking. |
| `/core-spec:status` | Check implementation progress against the specification. Reads current state files and displays which phases are complete, in progress, or pending. |

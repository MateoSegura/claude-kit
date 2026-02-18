# Plan File Formatting Standards and Conventions

This document defines the canonical format for plan files, naming conventions, and formatting rules enforced by the spec plugin.

## overview.md Required Sections

The overview.md file MUST contain these sections in order:

### Title (H1)
- First line of the file
- Format: `# [Project Title]`
- Concise description of the project or task

### Context (H2)
- Immediately after the title
- Captures the original request and conversation state at plan creation
- Two required subsections:
  - `**Original request:**` — The user prompt or request that initiated this plan
  - `**Conversation state:**` — Brief summary of relevant context: key files discussed, decisions made, constraints mentioned
- Purpose: Aids context recovery after compaction by preserving the starting conditions

### Goal (H2)
- One-paragraph description of what we're building, fixing, or changing
- Should be specific and measurable

### Architecture Decisions (H2)
- Bulleted list of key decisions with rationale
- Format: `- **[Decision]**: [Rationale]`
- Captures WHY choices were made, not just WHAT was chosen

### Constraints (H2)
- Bulleted list of limitations, requirements, or boundaries
- Technical constraints (platform versions, API limits)
- Process constraints (must not break existing features)
- Resource constraints (time, budget, dependencies)

### Phase Summary (H2)
- Markdown table with columns: Phase | Title | Status | Description
- Status values: `pending`, `in_progress`, `completed`
- One-line description per phase
- Must match the phase files in `phases/` directory

### Key Files (H2)
- Bulleted list of critical files in the project
- Format: `` `path/to/file.ext` — [role in the project] ``
- Helps recovery agent orient to the codebase structure

All sections are mandatory. Omitting any section breaks the context-recovery workflow.

## Phase File Naming Convention

Phase files use zero-padded two-digit numbering:

- `phase-01.md`
- `phase-02.md`
- `phase-03.md`
- ...
- `phase-99.md`

### Rationale

Zero-padding ensures lexicographic sorting matches numeric sorting:
- Correct lexicographic order: `phase-01.md`, `phase-02.md`, `phase-10.md`, `phase-11.md`
- Broken without padding: `phase-1.md`, `phase-10.md`, `phase-11.md`, `phase-2.md`

This matters for:
- Shell globs that list phases in order: `ls phases/phase-*.md`
- Context recovery scripts that read phases sequentially
- Human readability when browsing the phases directory

## status.log Conventions

The status.log is an append-only audit trail. Format rules:

### Timestamp Format
- UTC ISO 8601: `[YYYY-MM-DDTHH:MM:SSZ]`
- Always in square brackets at start of line
- Example: `[2026-02-16T14:23:00Z]`

### COMPLETED Entry Format
```
[YYYY-MM-DDTHH:MM:SSZ] COMPLETED (task #N): Phase NN: [Title]
```
- Includes TaskList task ID for cross-referencing
- Phase number is zero-padded to match phase file names
- Example: `[2026-02-16T10:30:00Z] COMPLETED (task #1): Phase 01: Project Setup`

### COMPACTION_SNAPSHOT Format
```
--- COMPACTION_SNAPSHOT [YYYY-MM-DDTHH:MM:SSZ] ---
Context compaction triggered. State above this line was in context before compaction.
The context-recovery agent will read this file to restore orientation.
---
```
- Three-line block with timestamp in header
- Acts as a bookmark separating context windows
- Recovery agent reads from most recent snapshot forward

### Write Restrictions
- **Never hand-edited by Claude** — only hook scripts write to status.log
- `update-status.sh` writes COMPLETED entries (triggered by TaskCompleted hook)
- `pre-compact-snapshot.sh` writes COMPACTION_SNAPSHOT markers (triggered by PreCompact hook)
- Append-only — never delete or modify existing entries
- This ensures status.log is a reliable, untampered audit trail

## state.json Format

state.json is a structured compaction snapshot written by `pre-compact-snapshot.sh` during PreCompact events. It provides a fast, machine-readable recovery path that the context-recovery agent reads before falling back to status.log parsing.

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `active_spec` | string | Relative path to the plan directory, e.g., `"docs/specs/auth-refactor-2026-02-16"` |
| `current_phase` | integer | The phase currently in progress |
| `current_task_id` | string | TaskList ID of the current or next task |
| `last_completed_task_id` | string | TaskList ID of the most recently completed task |
| `last_completed_phase` | integer | The last fully completed phase number |
| `timestamp` | string | UTC ISO 8601 timestamp of when the snapshot was taken |

### Example

```json
{
  "active_spec": "docs/specs/auth-refactor-2026-02-16",
  "current_phase": 3,
  "current_task_id": "task-4",
  "last_completed_task_id": "task-3",
  "last_completed_phase": 2,
  "timestamp": "2026-02-16T14:23:00Z"
}
```

### Write Restrictions

- Written by `pre-compact-snapshot.sh` during PreCompact events ONLY. Never written by Claude directly.
- This is the authoritative snapshot for recovery — the recovery agent reads this first.
- If state.json is missing or malformed, the recovery agent falls back to status.log parsing.

## .current-phase Format

`.current-phase` is a single-line file containing an integer representing the current or next phase number (e.g., `3`).

### Purpose

- Written by `update-status.sh` when a task completes
- The value represents the next phase to work on: completed phase + 1, validated against existing phase files
- Provides a fast, reliable phase indicator without requiring status.log parsing

### Format

```
3
```

Single integer on a single line, no trailing whitespace or extra newlines.

### Write Restrictions

- Never written by Claude directly — only `update-status.sh` manages this file
- Updated atomically each time a phase task completes
- The recovery agent uses this as a fallback if state.json is unavailable

## TaskList Naming Conventions

TaskList items representing plan phases follow strict naming:

### Subject Format
- MUST start with `Phase NN:` where NN is zero-padded
- Matches the phase file number exactly
- Examples:
  - `Phase 01: Project Setup`
  - `Phase 02: Core Implementation`
  - `Phase 10: Final Testing`
  - `Phase 15: Deployment`

### activeForm Field
- MUST use present continuous tense
- Examples:
  - "Setting up project structure"
  - "Implementing core functionality"
  - "Testing integration points"
  - "Deploying to production"

This consistency enables the context-recovery agent to cross-reference TaskList items with phase files and status.log entries.

## Named Plan Directory Conventions

Plans are stored in `docs/specs/<name>-<YYYY-MM-DD>/` where:

### Name Component
- 2-4 words in kebab-case
- Descriptive of the plan's purpose
- Examples: `api-refactor`, `user-auth-flow`, `perf-optimization`, `db-migration-prep`
- No underscores, no camelCase, no spaces

### Date Component
- Format: `YYYY-MM-DD`
- Represents the plan creation date
- Uses ISO 8601 date format (no time component)
- Examples: `2026-02-16`, `2026-03-01`, `2025-12-15`

### Full Examples
- `docs/specs/api-refactor-2026-02-16/`
- `docs/specs/user-auth-flow-2026-02-15/`
- `docs/specs/perf-optimization-2026-02-10/`

### Active Plan Tracking
- File: `docs/specs/.active`
- Content: Single line containing just the directory name (not full path)
- Example content: `api-refactor-2026-02-16`
- Updated when switching between plans or creating a new plan

This convention:
- Keeps all plans organized under a single `docs/specs/` directory
- Makes plan age immediately visible from directory name
- Allows multiple plans to coexist (only one active at a time)
- Enables historical tracking and archival

## Markdown Formatting Rules

All plan markdown files follow these formatting conventions:

### Headings
- Use ATX-style headings (`#`, `##`, `###`) — NOT underline style
- One blank line before each heading (except document-initial H1)
- Example:
  ```markdown
  ## Section Title

  Content here.

  ## Next Section
  ```

### Tables
- MUST include header separator row with dashes
- Align columns with pipes for readability
- Example:
  ```markdown
  | Phase | Title | Status |
  |-------|-------|--------|
  | 1     | Setup | pending |
  ```

### Code Fences
- Always include language hint for syntax highlighting
- Example:
  ```markdown
  ```bash
  npm install
  ```
  ```

### Checklists
- Use `- [ ]` for unchecked items
- Use `- [x]` for checked items
- One space after the checkbox
- Example:
  ```markdown
  - [ ] Implement feature X
  - [x] Write tests for feature X
  ```

### Line Breaks
- Use one blank line between paragraphs
- Use one blank line before headings
- No trailing whitespace at end of lines

These rules ensure consistency across all plan files and make diffs more meaningful during recovery and updates.

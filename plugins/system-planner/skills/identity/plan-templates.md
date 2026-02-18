# Plan File Templates

Reference templates for the files created by `/system-planner:plan`. These define the canonical format that the context-recovery agent expects.

Named plan directories follow the convention `docs/plans/<name>-<YYYY-MM-DD>/` where:
- `<name>` must be 2-4 kebab-case words
- `<YYYY-MM-DD>` is the creation date

## overview.md template

```markdown
# [Project Title]

## Context

**Original request:** [the user prompt or request that initiated this plan]

**Conversation state:** [brief summary of relevant context at plan creation time — key files discussed, decisions made, constraints mentioned]

## Goal
[One-paragraph description of what we're building/fixing/changing]

## Architecture Decisions
- **[Decision 1]**: [Rationale]
- **[Decision 2]**: [Rationale]

## Constraints
- [Constraint 1]
- [Constraint 2]

## Phase Summary

| Phase | Title | Status | Description |
|-------|-------|--------|-------------|
| 1 | [Title] | pending | [One-line summary] |
| 2 | [Title] | pending | [One-line summary] |
| N | [Title] | pending | [One-line summary] |

## Key Files
- `path/to/file.ext` — [role in the project]
```

## phase-NN.md template

Phase files use zero-padded naming: `phase-01.md`, `phase-02.md`, etc.

```markdown
# Phase NN: [Title]

## Objective
[One sentence: what this phase achieves]

## Steps
1. [ ] [Step description] — `path/to/file`
2. [ ] [Step description] — `path/to/file`
3. [ ] [Step description]

## Files to Create/Modify
- `path/to/new-file.ext` — [what it contains]
- `path/to/existing-file.ext` — [what changes]

## Acceptance Criteria
- [ ] [Verifiable condition 1]
- [ ] [Verifiable condition 2]

## Dependencies
- Requires: Phase [NN-1] (if applicable)
- Blocks: Phase [NN+1] (if applicable)
```

## status.log format

The status.log is append-only and written exclusively by hook scripts. Located at `docs/plans/<name>-<YYYY-MM-DD>/status.log`.

Format:

```
[2026-02-16T10:30:00Z] COMPLETED (task #1): Phase 01: Project setup
[2026-02-16T11:45:00Z] COMPLETED (task #2): Phase 02: Core implementation
--- COMPACTION_SNAPSHOT [2026-02-16T12:00:00Z] ---
Context compaction triggered. State above this line was in context before compaction.
The context-recovery agent will read this file to restore orientation.
---
[2026-02-16T12:15:00Z] COMPLETED (task #3): Phase 03: Testing
```

### Conventions

- Timestamps are UTC ISO 8601
- COMPLETED entries include the TaskList task ID for cross-reference
- Phase numbers are zero-padded to match phase file names (Phase 01, Phase 02, etc.)
- COMPACTION_SNAPSHOT markers are bookends — everything between two markers represents one context window's work
- The most recent marker is the relevant recovery point

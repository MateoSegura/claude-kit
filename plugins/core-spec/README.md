# core-spec

> **Role:** System · **Version:** 0.2.0

Tiered planning system for long-running Claude Code sessions. Assesses task
complexity, creates the right level of plan (vanilla → structured → phased
specification), and ensures plans survive context compaction through file-based
state and a rules-driven boot sequence.

```bash
claude-kit --kit core-spec
```

---

## How It Works

### The Problem

Claude's built-in planning works for short tasks. For long tasks requiring
multiple context compactions, plan adherence degrades because compaction
preserves facts but loses behavioral momentum.

### The Solution: Tiered Planning

| Tier | Name | When | What |
|------|------|------|------|
| 0 | Vanilla | Simple, <20 turns | Claude's built-in plan mode |
| 1 | Structured Plan | Medium, 20-50 turns | Single plan file at `~/.claude-kit/plans/` |
| 2 | Phased Specification | Complex, 50+ turns | Full spec with phases, team-reviewed |

Plans automatically upgrade when a task outgrows its tier:
- First compaction + incomplete → Tier 1
- Second compaction + incomplete → Tier 2

### Key Mechanisms

- **PLAN-ACTIVE TaskList anchor**: Links the conversation to plan files. Survives compaction.
- **plan-protocol.md rules file**: Installed to `~/.claude/rules/`, enforces boot sequence after compaction.
- **Phase-as-session model**: Each compaction is a clean handoff between phases.
- **Team agents** (Tier 2): Writer + reviewer agents produce high-quality phase files.
- **Mode-aware planning**: Adapts plans to the active behavioral profile (autonomous/pair/assistant).

---

## Mode Awareness

Plans adapt to the user's behavioral profile, detected from the `claude-kit setup`
profile:

| Mode | Acceptance Criteria | Environment Doc | Test Plan |
|------|-------------------|-----------------|-----------|
| Autonomous | Machine-verifiable only (`[command] → [output]`) | Fully populated, no gaps | Automated only, explicit coverage targets |
| Pair | Mostly automated, up to 20% `[HUMAN-REVIEW]` | Brief notes acceptable | Automation default, few manual review points |
| Assistant | Any mix of automated and subjective | Can reference external docs | Flexible, serves as discussion guide |

Mode is detected from:
1. Section 4 heading in `~/.claude/rules/claude-kit.md`
2. Fallback: `profile` key in `~/.claude-kit/manifest.json`
3. Default: `pair`

---

## Commands

| Command | What it does |
|---------|-------------|
| `/spec:new` | Create a plan or specification. Detects mode, asks mode-adapted questions, generates the right tier. |
| `/spec:status` | Show plan progress — tier, mode, phases, environment/test readiness. |

---

## Plan File Locations

Plans are stored at `~/.claude-kit/plans/<plan-id>/`:

- **Tier 1**: `plan.md` (single file)
- **Tier 2**: `overview.md` + `status.md` + `phases/phase-NN.md` + `environment.md` + `test-plan.md`

### Tier 2 Artifacts

| File | Purpose |
|------|---------|
| `overview.md` | Requirements, constraints, architecture decisions |
| `status.md` | Current phase, progress, decisions log, detected mode |
| `phases/phase-NN.md` | Self-contained phase specifications |
| `environment.md` | Development setup, dependencies, secrets, verification |
| `test-plan.md` | Test strategy, frameworks, per-phase pass/fail criteria |

---

## Enforcement

The `rules/plan-protocol.md` file is designed to be installed to
`~/.claude/rules/` by the `claude-kit setup` command. It provides:

- Boot sequence after context compaction (includes mode recovery)
- Plan adherence rules (ONLY modify planned files)
- Adaptive upgrade triggers
- Complexity assessment heuristics

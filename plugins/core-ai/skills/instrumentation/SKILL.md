---
name: core-ai:instrumentation
description: "Instrumentation theory and 4-phase process overview. Covers detection tiers, output taxonomy, progressive instrumentation modes, and the manifest system for idempotent re-runs."
user-invocable: false
---

# Instrumentation — Theory and Process

Repository instrumentation is the process of analyzing a codebase and generating `.claude/` configuration files that encode its conventions into machine-readable, enforceable context.

## The 4-Phase Process

### Phase 1: Detect (Silent, No User Interaction)

The repo-analyzer agent scans the repository and builds a structured detection model:

- **File system signals** — package.json, Cargo.toml, tsconfig, linter configs, CI workflows, Docker, monorepo configs, existing `.claude/`
- **Git history signals** — commit patterns, branch naming, merge strategy, tags, contributor count
- **Code structure signals** — directory layout, test co-location, import patterns, entry points

Output: a JSON detection model covering Tier 1 (auto-detectable) and Tier 2 (partially detectable, needs confirmation) signals.

### Phase 2: Confirm (Guided Interaction)

Present detection findings and ask clarifying questions:

1. **Verify detection** — "I detected X, Y, Z. Is this accurate?"
2. **Workflows** — "How do releases work? What should happen on PR creation?"
3. **Boundaries** — "Are there things I should never do in this repo?"
4. **Enforcement level** — Strict (block), Moderate (warn), Relaxed (document only)

Target: 3-5 focused questions with sensible defaults.

### Phase 3: Generate (Transparent Output)

Spawn generator agents in parallel to create `.claude/` files:

- **rule-generator** → `.claude/rules/*.md` files
- **command-generator** → `.claude/commands/*.md` files
- **hook-generator** → `.claude/hooks.json` + scripts (only if user opted for enforcement)

Before writing, show the user exactly what will be generated and why. Each file traces back to its detection signals and user input.

### Phase 4: Manifest (State Tracking)

Create or update `.claude/.instrumentation.json` — the manifest that tracks:
- What was generated, when, from what signals
- File hashes for drift detection
- User answers for re-instrumentation context
- Detection model for comparison on re-runs

## Detection Tiers

### Tier 1 — Essential (auto-detectable, high impact)

Build commands, test commands, language/framework, package manager, project structure, linting/formatting, CI/CD system.

### Tier 2 — Important (partially detectable, needs confirmation)

Git workflow, testing conventions, documentation requirements, dependency management, monorepo tooling.

### Tier 3 — Advanced (human-only knowledge)

Architecture decisions, release workflow details, security policies, boundary rules, team conventions, development philosophy.

## Output Taxonomy

### Rules (`.claude/rules/*.md`)

Loaded every Claude session. Define behavioral expectations — conventions, standards, patterns.

| Rule category | Content source |
|---------------|---------------|
| Git conventions | Git history + user input |
| Code style | Linter configs + user input |
| Testing standards | Test configs + CI + user input |
| Release workflow | CI workflows + user input |
| Project structure | File system scan |
| Architecture | User input (Tier 3) |
| Security | User input (Tier 3) |
| Dependencies | Lockfiles + user input |

### Commands (`.claude/commands/*.md`)

User-invocable workflows. Generated when the user describes a repeatable process.

### Hooks (`.claude/hooks.json`)

Automated enforcement. Generated conservatively — only when the user explicitly wants enforcement, not just guidance.

## Progressive Instrumentation Modes

### Greenfield (nothing exists)

Full detection + guided generation. Scan everything, ask 3-5 questions, generate complete `.claude/` setup.

### Partial (some rules/commands exist)

Audit + gap analysis + augment. Parse existing files, build coverage map, report gaps, offer to fill them without modifying existing files.

### Re-instrumentation (update existing)

Drift detection + evolution. Re-scan repo, compare against manifest, detect drift and staleness, suggest targeted updates.

See [detection-patterns.md](detection-patterns.md) for comprehensive signal reference.
See [output-templates.md](output-templates.md) for template patterns.

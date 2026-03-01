# Repository Instrumentation for AI-Assisted Development

> A design research document exploring how claude-kit can analyze a repository
> and generate tailored `.claude/` configurations — commands, skills, rules,
> and hooks — that encode the repo's conventions, workflows, and enforcement
> needs into machine-readable context.

**Date:** 2026-02-28

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [The Instrumentation Metaphor](#2-the-instrumentation-metaphor)
3. [Industry Landscape](#3-industry-landscape)
4. [What Makes a Repo AI-Ready](#4-what-makes-a-repo-ai-ready)
5. [Architecture: Where This Lives in claude-kit](#5-architecture-where-this-lives-in-claude-kit)
6. [The Instrumentation Process](#6-the-instrumentation-process)
7. [Output Taxonomy: What Gets Generated](#7-output-taxonomy-what-gets-generated)
8. [Progressive Instrumentation](#8-progressive-instrumentation)
9. [UX Design](#9-ux-design)
10. [Implementation Sketch](#10-implementation-sketch)
11. [Open Questions](#11-open-questions)
12. [Sources](#sources)

---

## 1. The Problem

Developers who use claude-kit (or Claude Code directly) today face a recurring
pattern: they discover enforcement gaps *after* something goes wrong.

**Example — the Release command problem:**

A `/release` command starts simple: bump version, tag, push. Over time it
accumulates ad-hoc requirements:

- "Enforce that docs get updated"
- "Enforce that `claude-kit update` still works"
- "Enforce that tests exist for new features"
- "Enforce that all plugins validate"

Each of these was added reactively after something broke. The command grows
into a sprawling checklist that is:

- **Incomplete** — there are always enforcement gaps you haven't hit yet
- **Non-uniform** — each rule was written at a different time with different
  rigor
- **Non-transferable** — these lessons live in one command, not available to
  other workflows (feature development, PR review, debugging)

This problem is not specific to releases. It applies to every workflow:
development, testing, code review, dependency management, documentation. The
conventions exist in the developer's head but are not encoded anywhere an AI
agent can discover and enforce them.

**The core insight:** Every repository has implicit conventions that determine
"how we work here." Today, these are transferred to AI agents via ad-hoc
instructions, repeated prompting, and trial-and-error. Instrumentation makes
them explicit, discoverable, and enforceable.

---

## 2. The Instrumentation Metaphor

In observability (OpenTelemetry, Prometheus), **instrumentation** means
embedding hooks, probes, and metadata into a system so its runtime behavior
becomes visible, measurable, and actionable. The metaphor maps precisely to
repository configuration for AI agents:

| Observability | Repository Instrumentation |
|---------------|---------------------------|
| **Traces** — follow a request through the system | **Workflow rules** — follow a change through branch, commit, PR, release |
| **Metrics** — measure quantitative properties | **Quality gates** — linting, test coverage, validation checks |
| **Spans** — delimit operations within a trace | **Scoped rules** — directory-specific conventions for certain file types |
| **Semantic conventions** — standardized field names | **Convention files** — standardized naming, formatting, structure |
| **Auto-instrumentation** — zero-code observability | **Auto-detection** — infer stack, tools, patterns from existing files |
| **Manual instrumentation** — custom spans/metrics | **Custom rules** — developer-authored instructions for project specifics |
| **Exporters** — send telemetry to backends | **Cross-tool output** — AGENTS.md, CLAUDE.md, .cursorrules |

### Why "instrumentation" is the right word

1. **Additive, not invasive.** Like OpenTelemetry, it adds observability
   without changing business logic. Rules live alongside code, not inside it.
2. **Layered.** Auto-instrumentation (detect package.json) vs manual
   instrumentation (write custom release rules) — same spectrum as OTel.
3. **Convention-driven.** OTel has semantic conventions (`http.method`,
   `db.system`). Repo instrumentation standardizes what agents expect to find.
4. **Enables enforcement.** Metrics trigger alerts; rules trigger hooks and
   validation. The hooks are the enforcement mechanism.
5. **Degrades gracefully.** An uninstrumented repo still works with AI agents.
   But output quality is dramatically better with instrumentation.

---

## 3. Industry Landscape

Every major AI coding tool has converged on the same need: a machine-readable
description of "how to work in this repository." They differ in file names and
minor format details, but the content categories are identical.

### Configuration file landscape (as of early 2026)

| Tool | Config location | Format |
|------|----------------|--------|
| Claude Code | `CLAUDE.md`, `.claude/rules/*.md` | Markdown |
| Cursor | `.cursor/rules/*.mdc` | Markdown + YAML frontmatter |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/*.md` | Markdown |
| Copilot Agent | Above + `copilot-setup-steps.yml` + `AGENTS.md` | Markdown + YAML |
| Windsurf | `.windsurf/rules/*.md` | Markdown |
| Amazon Q | `.amazonq/rules/*.md` | Markdown |
| Gemini CLI | `GEMINI.md`, `AGENTS.md` | Markdown |
| Kiro (AWS) | `requirements.md`, `design.md`, `tasks.md` | Markdown (spec-driven) |

### The emerging standard: AGENTS.md

Initiated by Sourcegraph and backed by OpenAI, Google, and GitHub, AGENTS.md
is a lightweight, Markdown-based open format. Key properties:

- No proprietary syntax — standard Markdown
- Hierarchical discovery — closest file to the edited file wins (monorepo-aware)
- 60,000+ repos already use it
- Supported by Codex, Copilot, Cursor, Aider, Zed, and others

### The "README for Machines" convergence

Every tool converges on the same insight: AI agents need a document analogous
to README.md, but optimized for *operational context* rather than human
onboarding. Where README says "what this project is," the agent instruction
file says "how to work in this project."

### What no tool does well today

No existing tool **generates** these configuration files from repository
analysis. They all require manual authoring. This is the gap that
instrumentation fills: **auto-detect what can be inferred, ask for what
cannot, and generate a complete, well-structured configuration.**

---

## 4. What Makes a Repo AI-Ready

Based on analysis of 2,500+ repositories (GitHub's AGENTS.md study) and the
broader ecosystem, the following tiers emerge:

### Tier 1 — Essential (auto-detectable, high impact)

| Category | Example | Detection source |
|----------|---------|-----------------|
| Build commands | `npm run build`, `cargo build` | package.json, Cargo.toml, Makefile |
| Test commands | `pytest -v`, `nx affected -t test` | config files, CI workflows |
| Language + framework | TypeScript 5.3, React 18, Zephyr 3.6 | dependencies, file extensions |
| Package manager | pnpm, cargo, pip | lockfiles |
| Project structure | `src/`, `apps/`, `libs/`, entry points | directory scan |
| Linting/formatting | ESLint, Prettier, clang-format | config files |
| CI/CD system | GitHub Actions, GitLab CI | workflow files |

### Tier 2 — Important (partially detectable, needs confirmation)

| Category | Example | Detection method |
|----------|---------|-----------------|
| Git workflow | Conventional Commits, trunk-based | commit history analysis, branch patterns |
| Testing conventions | Jest + co-located tests, 80% coverage | test config, CI thresholds |
| Documentation requirements | JSDoc required, README per package | existing patterns |
| Dependency management | "Use pnpm, justify new deps" | lockfile type, CI checks |
| Monorepo tooling | Nx, Turborepo, pnpm workspaces | config files |

### Tier 3 — Advanced (human-only knowledge)

| Category | Example | Must be asked |
|----------|---------|--------------|
| Architecture decisions | "We use hexagonal architecture" | Yes |
| Release workflow | "Squash merge, semver from changelog" | Yes |
| Security policies | "Never commit .env, validate all input" | Yes |
| Boundary rules | "Never delete migrations, ask before refactoring" | Yes |
| Team conventions | "PR descriptions must reference issue" | Yes |
| Target audience | "Internal tooling for embedded engineers" | Yes |
| Development philosophy | "Ship fast, tests for critical paths only" | Yes |

### The maturity spectrum

| Level | Name | Description |
|-------|------|-------------|
| 0 | **AI-Unaware** | No agent configuration. Agent guesses everything from code. |
| 1 | **AI-Ready** | Has instruction file(s) with build commands, style, structure. |
| 2 | **AI-Enabled** | Has scoped rules, boundaries, testing conventions, workflow defs. |
| 3 | **AI-First** | Designed with AI collaboration as first-class concern. Specs drive development. Hooks enforce conventions. The repo teaches any agent how to work in it. |

Instrumentation moves a repository from level 0 toward level 3.

---

## 5. Architecture: Where This Lives in claude-kit

### Current core-kit anatomy

```
plugins/core-kit/
  .claude-plugin/
    plugin.json           # name, description, version
    ctl.json              # role: "knowledge", domain: "universal"
  skills/
    identity/SKILL.md     # What core-kit is and why
    routing/
      SKILL.md            # Intent matching theory
      intent-map.md       # Natural language → skill mapping
```

core-kit is a **knowledge-only plugin** (no agents, no commands) with
`domain: "universal"`, meaning it auto-loads with every team. It provides
the routing intelligence that lets Claude match natural language to skills.

### Where instrumentation fits

Instrumentation is a natural extension of core-kit's role. core-kit already
teaches Claude *how to route intents to skills*. Instrumentation teaches
Claude *how to generate the rules, commands, and hooks that a specific
repository needs*.

**Proposed additions to core-kit:**

```
plugins/core-kit/
  skills/
    identity/SKILL.md
    routing/...
    instrumentation/              # NEW
      SKILL.md                    # Instrumentation theory + process overview
      detection-patterns.md       # What to auto-detect and how
      output-templates.md         # Templates for generated rules/commands/hooks
  agents/                         # NEW (core-kit gains agents)
    repo-analyzer.md              # Scans repo, builds detection model
    rule-generator.md             # Generates .claude/rules/ files
    command-generator.md          # Generates .claude/commands/ files
    hook-generator.md             # Generates .claude/hooks/ files
  commands/                       # NEW
    instrument.md                 # /core-kit:instrument — main entry point
```

**Key design decision:** core-kit transitions from knowledge-only to
knowledge + agents + commands. This is justified because instrumentation is
a *universal* capability — every repository benefits from it regardless of
domain. It stays in core-kit (not a separate plugin) because:

1. It needs `domain: "universal"` to be available with any team
2. It's a natural extension of the "teach Claude about this project" role
3. It shares context with the routing skill (generated rules feed into routing)

**Alternative: separate `core-instrumentation` plugin.** This keeps core-kit
pure as knowledge-only. However, it adds complexity (another plugin to
maintain, companion declarations, etc.) for a feature that conceptually
belongs in the "core intelligence" layer. This is a valid alternative if
core-kit's scope becomes too large.

### How the user triggers it

```bash
# User runs core plugins only (no team needed)
claude-kit -k core

# In the Claude session, says:
> "I want to instrument this repo for AI development"

# Auto-routing matches intent → /core-kit:instrument
# The command walks them through the process
```

Or explicitly:

```bash
claude-kit -k core-kit
> /core-kit:instrument
```

### What it generates (output targets)

All output goes into the project's `.claude/` directory:

```
.claude/
  rules/                # Convention enforcement (loaded every session)
    git-conventions.md
    testing-standards.md
    release-workflow.md
    code-style.md
    architecture.md
    security.md
  commands/             # Workflow orchestration (user-invocable)
    release.md
    review.md
    test.md
  hooks.json            # Automated enforcement
  settings.local.json   # Tool permissions (optional)
```

Instrumentation does **not** generate plugins. It generates project-level
`.claude/` configuration that works with or without claude-kit plugins loaded.

---

## 6. The Instrumentation Process

### Phase 1: Silent Detection (no user interaction)

The repo-analyzer agent scans the repository and builds a detection model:

**File system signals:**
- `package.json` → language, dependencies, scripts, package manager
- `Cargo.toml`, `go.mod`, `pyproject.toml` → language + ecosystem
- `tsconfig.json`, `jsconfig.json` → TypeScript/JS configuration
- `.eslintrc*`, `.prettierrc*`, `rustfmt.toml` → formatting tools
- `jest.config.*`, `vitest.config.*`, `pytest.ini` → test framework
- `.github/workflows/` → CI/CD system and workflow patterns
- `Dockerfile`, `.devcontainer/` → containerization
- `nx.json`, `turbo.json` → monorepo tooling
- `.claude/`, `.cursor/`, `AGENTS.md` → existing AI configuration

**Git history signals:**
- Commit message patterns → conventional commits? Freeform?
- Branch naming patterns → feature/, fix/, release/?
- Merge patterns → squash, merge commit, rebase?
- Tag patterns → semver? Calendar versioning?
- Active contributors → team size signal

**Code structure signals:**
- Directory layout → `src/`, `apps/`, `libs/`, `packages/`
- Test co-location → `*.test.ts` next to source? Separate `tests/` dir?
- Import patterns → relative? Aliases? Barrel files?

### Phase 2: Confirm and Customize (guided interaction)

Present findings and ask for what cannot be inferred. The interaction is
conversational, not a form. Questions are ordered by impact:

**Category 1: Verify detection**
> "I detected a TypeScript/React project using pnpm, Vitest, ESLint, and
> GitHub Actions. You have a devcontainer and appear to use Conventional
> Commits. Is this accurate?"

**Category 2: Workflows (highest value)**
> "How do releases work in this project? What needs to happen before a
> release is considered ready?"

> "What should happen when someone creates a PR? What checks must pass?"

**Category 3: Boundaries and philosophy**
> "Are there things an AI should never do in this repo? Files it shouldn't
> touch, commands it shouldn't run, patterns it shouldn't use?"

> "How strict should enforcement be? Should the AI block violations or just
> warn about them?"

**Category 4: Advanced (optional, offered not required)**
> "Want to define architecture constraints?"
> "Want to add security policies?"
> "Want to configure environment setup for new contributors?"

The total interaction should be **5-10 questions**, each with sensible
defaults that can be accepted with Enter.

### Phase 3: Generate (transparent output)

The generator agents create `.claude/` files, showing the user exactly what
is being generated and why:

```
Creating .claude/rules/git-conventions.md
  ← detected: Conventional Commits from commit history
  ← user confirmed: squash merge to main
  ← user added: "always reference issue in PR description"

Creating .claude/rules/testing-standards.md
  ← detected: Vitest, co-located test files
  ← user confirmed: 80% coverage target
  ← user added: "integration tests required for API routes"

Creating .claude/commands/release.md
  ← user described: version bump from changelog, tag, push, monitor CI
  ← detected: GitHub Actions release workflow exists
  ← auto-included: validation step from existing CI checks
```

### Phase 4: Verify (optional)

After generation, offer to validate:

> "Want me to do a dry run? I'll simulate a release / feature development /
> PR review using the generated rules to check if anything is missing."

This catches gaps before they matter.

---

## 7. Output Taxonomy: What Gets Generated

### Rules (`.claude/rules/*.md`)

Rules are the foundation. They're loaded into every Claude session in this
project and define behavioral expectations.

| Rule file | Content | Detection source |
|-----------|---------|-----------------|
| `git-conventions.md` | Commit format, branch naming, merge strategy, push policies | Git history + user input |
| `code-style.md` | Language idioms, formatting, naming conventions, import order | Linter configs + user input |
| `testing-standards.md` | Framework, patterns, coverage, when tests are required | Test configs + CI + user input |
| `release-workflow.md` | Steps, checks, version strategy, changelog, CI requirements | CI workflows + user input |
| `project-structure.md` | Directory map, where things go, naming patterns | File system scan |
| `architecture.md` | Patterns, boundaries, technology decisions | User input (Tier 3) |
| `security.md` | Sensitive files, auth patterns, input validation | User input (Tier 3) |
| `dependencies.md` | Package manager, update policy, justification requirements | Lockfiles + user input |

### Commands (`.claude/commands/*.md`)

Commands orchestrate multi-step workflows. Generated when the user describes
a repeatable process.

| Command | Purpose | Generated when |
|---------|---------|---------------|
| `release.md` | Orchestrate the full release process | User describes release workflow |
| `review.md` | Structured code review checklist | User describes review conventions |
| `test.md` | Run tests with project-specific flags | Test framework detected |
| `setup.md` | Onboard new contributor or environment | Devcontainer or setup scripts detected |
| `deploy.md` | Deployment workflow | Deployment config detected |

### Hooks (`.claude/hooks.json`)

Hooks enforce rules automatically. Generated conservatively — only when the
user explicitly wants enforcement (not just guidance).

| Hook | Event | Purpose |
|------|-------|---------|
| Commit message format | `PreToolUse` on `Bash` matching `git commit` | Block malformed commits |
| Test presence check | `PostToolUse` on `Write` matching source files | Warn if new code lacks tests |
| Sensitive file guard | `PreToolUse` on `Write\|Edit` matching `.env*` | Block writing secrets |
| Build verification | `Stop` | Run build before session ends |

### What is NOT generated

- **Plugin files** — instrumentation targets `.claude/`, not `plugins/`
- **CLAUDE.md** — that's the user's domain; instrumentation writes to
  `rules/` which is modular and doesn't conflict
- **Global config** — only touches the current project's `.claude/`
- **Code changes** — never modifies source code, tests, or configs

---

## 8. Progressive Instrumentation

The system must handle three scenarios gracefully:

### Greenfield (nothing exists)

**Strategy:** Full detection + guided generation.

- Scan everything, ask 5-10 questions, generate complete `.claude/` setup
- Start with Tier 1 + Tier 2 content
- Offer Tier 3 as optional extensions
- Generate a manifest file (`.claude/.instrumentation.json`) tracking what
  was generated, when, and from what detection signals

### Partial (some rules/commands exist)

**Strategy:** Audit + gap analysis + augment.

1. Parse existing `.claude/rules/`, `.claude/commands/`, `CLAUDE.md`
2. Build a coverage map: what's already addressed, what's missing
3. Report: "You have git conventions and testing rules, but no release
   workflow, dependency policy, or architecture constraints"
4. Offer to fill gaps without modifying existing files
5. If existing rules conflict with detected patterns, surface the conflict
   and let the user resolve it

**Critical principle:** Never overwrite or modify existing user-authored
files. Treat them as ground truth. Instrumentation augments, never replaces.

### Re-instrumentation (update existing)

**Strategy:** Drift detection + evolution.

Over time, instrumentation drifts from reality just like documentation.
Re-running instrumentation should:

1. Re-scan the repo (tech stack may have changed)
2. Compare current state against the manifest
3. Detect drift: rules mention Jest but the repo now uses Vitest
4. Detect staleness: rules reference files/dirs that no longer exist
5. Suggest updates: "Your testing rules reference Jest but I see Vitest
   config now. Want me to update?"
6. Track changes in the manifest for auditability

**The manifest file (`.claude/.instrumentation.json`):**

```json
{
  "version": "1",
  "created": "2026-02-27",
  "updated": "2026-02-27",
  "generator": "core-kit:instrument",
  "detection": {
    "language": "typescript",
    "framework": "react",
    "package_manager": "pnpm",
    "test_framework": "vitest",
    "ci_system": "github-actions",
    "monorepo": null
  },
  "files": {
    ".claude/rules/git-conventions.md": {
      "generated": "2026-02-27",
      "sources": ["git-history", "user-input"],
      "hash": "abc123"
    },
    ".claude/rules/testing-standards.md": {
      "generated": "2026-02-27",
      "sources": ["vitest.config.ts", "user-input"],
      "hash": "def456"
    }
  },
  "user_answers": {
    "release_workflow": "semver from changelog, squash merge",
    "test_coverage": "80% minimum",
    "strict_enforcement": false
  }
}
```

The manifest enables:
- **Idempotency**: Running instrumentation again doesn't duplicate files
- **Drift detection**: Compare file hashes to detect manual edits
- **Re-detection**: Re-scan and compare against stored detection results
- **Auditability**: Track what was auto-generated vs user-authored

---

## 9. UX Design

### Design principles

1. **Transparency over magic.** Always show what was detected and what will
   be generated. Never silently write files.
2. **Sensible defaults over blank slates.** Pre-fill everything possible.
   Let the user edit rather than create from scratch.
3. **Progressive disclosure.** Start with essentials (build, test, style).
   Advanced sections (security, release, architecture) are opt-in.
4. **Non-invasive.** Never modify existing code or existing `.claude/` files.
   Only create new files or update previously-generated ones.
5. **Idempotent.** Running again on an instrumented repo detects existing
   state and offers updates, not duplicates.
6. **Time to value < 60 seconds.** Detection should finish in seconds,
   first useful output within a minute.

### The interaction flow

```
User: "I want to instrument this repo for AI development"

Claude: [Scans repo silently — 5-10 seconds]

Claude: "Here's what I found:
  Language:    TypeScript (React 18, Node 20)
  Package mgr: pnpm
  Tests:       Vitest, co-located (*.test.ts)
  Linting:     ESLint + Prettier
  CI:          GitHub Actions (3 workflows)
  Container:   .devcontainer present
  Git:         Conventional Commits, squash merge to main

  Does this look right? Anything to correct?"

User: "Yeah that's right"

Claude: "Great. A few things I can't detect from the code:

  1. How do releases work? What needs to happen before a version
     ships? (or skip if you don't have a release process yet)

  2. Are there things I should never do in this repo?
     (e.g., files to never touch, commands to never run)

  3. How strict should enforcement be?
     ○ Strict — block violations before they happen
     ○ Moderate — warn but allow (recommended)
     ○ Relaxed — just document conventions, no enforcement"

User: [Answers naturally in conversation]

Claude: "Based on your answers, here's what I'll generate:

  .claude/rules/git-conventions.md      ← commit format, branch naming
  .claude/rules/testing-standards.md    ← vitest patterns, coverage
  .claude/rules/code-style.md          ← TS/React conventions from ESLint
  .claude/rules/release-workflow.md    ← your release process
  .claude/commands/release.md          ← orchestrates the release
  .claude/hooks.json                   ← commit format enforcement

  Want me to proceed? You can also add/remove items."

User: "Go for it"

Claude: [Generates files, shows each one briefly]
        [Creates .instrumentation.json manifest]

Claude: "Done. Your repo is now instrumented. These rules will be
  active in every Claude session in this project.

  To update later: just say 'update instrumentation' or
  run /core-kit:instrument again."
```

### What "transparent" means in practice

Every generated file includes a header comment:

```markdown
<!-- Generated by claude-kit instrumentation (2026-02-27)
     Sources: git history analysis, vitest.config.ts, user input
     Re-generate: /core-kit:instrument -->

# Git Conventions

...
```

This makes it clear to any developer (or future AI session) that the file
was generated, when, from what signals, and how to update it.

---

## 10. Implementation Sketch

### Agents

**repo-analyzer** (read-only, fast)
- Tools: Read, Glob, Grep, Bash (read-only commands)
- Model: haiku (speed over depth for detection)
- Output: JSON detection model
- Behavior: Scan file system, parse configs, analyze git history,
  identify existing `.claude/` configuration

**rule-generator** (write)
- Tools: Read, Write, Glob
- Model: sonnet (needs good prose for rule content)
- Input: Detection model + user answers
- Output: `.claude/rules/*.md` files
- Skills: instrumentation (templates, patterns)

**command-generator** (write)
- Tools: Read, Write, Glob
- Model: sonnet
- Input: Detection model + user workflow descriptions
- Output: `.claude/commands/*.md` files
- Skills: instrumentation, plugin-structure (correct frontmatter)

**hook-generator** (write)
- Tools: Read, Write, Bash
- Model: sonnet
- Input: Detection model + enforcement preferences
- Output: `.claude/hooks.json` + scripts
- Skills: instrumentation, plugin-structure (hook schema)

### Command

**instrument.md** (`/core-kit:instrument`)
- Orchestrates the 4-phase process
- Spawns repo-analyzer first, then presents findings
- Conducts conversational Q&A (not a rigid form)
- Spawns generator agents in parallel for the output phase
- Creates/updates the manifest

### Skills

**instrumentation/SKILL.md** — Theory and process overview
**instrumentation/detection-patterns.md** — Comprehensive detection
  reference (which files signal what, how to parse each ecosystem)
**instrumentation/output-templates.md** — Template patterns for each
  output file type (rules, commands, hooks)

### Routing

Add to the intent map:

| Intent | Skill/Command |
|--------|--------------|
| "instrument this repo", "set up AI rules", "configure claude for this project" | `core-kit:instrument` |
| "update instrumentation", "refresh rules" | `core-kit:instrument` (re-run mode) |
| "audit AI configuration", "check instrumentation" | `core-kit:instrument` (audit mode) |

---

## 11. Open Questions

### Scope boundaries

1. **Should instrumentation generate CLAUDE.md or only `.claude/rules/`?**
   CLAUDE.md is the "main" instruction file and users may already have one.
   Rules are modular and lower-conflict. Recommendation: rules only, with an
   option to generate CLAUDE.md if none exists.

2. **Should it generate AGENTS.md for cross-tool compatibility?**
   This would make the instrumentation useful beyond Claude Code. Could be
   an opt-in flag. Low cost, high value for teams using multiple tools.

3. **Should it generate `.github/copilot-instructions.md` too?**
   Same reasoning as AGENTS.md. If the goal is "instrument this repo for AI
   development" broadly, multi-format output makes sense.

### core-kit evolution

4. **Does core-kit stay knowledge-only or gain agents/commands?**
   Adding agents and commands to core-kit is a breaking change to its
   architecture (currently pure knowledge). Alternative: create a separate
   `core-instrumentation` plugin. Trade-off: simplicity vs purity.

5. **Version implications:** If core-kit gains agents/commands, that's a
   MINOR version bump (new capability). If the skill API changes, MAJOR.

### Detection depth

6. **How deep should git history analysis go?** Analyzing 50 commits is fast
   and catches patterns. Analyzing 1000 gives better accuracy but takes
   longer. Should be configurable.

7. **Should detection run AI inference (expensive) or be purely heuristic
   (fast)?** The repo-analyzer could use a haiku model to understand code
   patterns, or it could be pure file/regex matching. Recommendation: start
   heuristic, add inference later for ambiguous cases.

### Update mechanics

8. **How to handle user edits to generated files?** If the user modifies a
   generated rule, re-instrumentation should detect the modification (via
   hash comparison) and not overwrite it. But it should surface that the
   file has drifted from the template.

9. **Should there be a `claude-kit instrument` CLI command in addition to
   the in-session `/core-kit:instrument` skill?** A CLI command could run
   headlessly for CI integration. The in-session command is better for
   guided setup.

### Output quality

10. **How to ensure generated commands are actually useful?** The risk is
    generating boilerplate commands that don't capture the repo's real
    workflow. Mitigation: generate from specific user descriptions, not
    generic templates. Show drafts before writing.

11. **How to test instrumentation quality?** Could have a "dry run" mode
    that simulates using the generated rules on a real task and surfaces
    gaps. This is essentially what the grader plugins do — grade the
    instrumentation output.

---

---

## Sources

- [AGENTS.md Specification](https://agents.md/) — The emerging cross-tool standard for AI agent configuration
- [How to Write a Great agents.md (GitHub Blog)](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) — Analysis of 2,500+ repositories
- [Trail of Bits claude-code-config](https://github.com/trailofbits/claude-code-config) — Production-grade Claude Code configuration reference
- [Claude Code Settings (Anthropic Docs)](https://code.claude.com/docs/en/settings) — Official .claude/ directory documentation
- [Using CLAUDE.MD Files (Anthropic)](https://claude.com/blog/using-claude-md-files) — Best practices for project instruction files
- [GitHub Copilot Custom Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot) — Copilot's approach to project configuration
- [Cursor Rules Documentation](https://docs.cursor.com/context/rules-for-ai) — Cursor's rule system and glob-based scoping
- [Amazon Q Developer Project Rules](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/context-project-rules.html) — AWS's approach to project rules
- [Kiro: Spec-Driven AI Development](https://kiro.dev/) — AWS's spec-driven approach with agent hooks
- [OpenTelemetry Instrumentation Concepts](https://opentelemetry.io/docs/concepts/instrumentation/) — The observability instrumentation model
- [Spec-Driven Development (Thoughtworks)](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices) — Spec-driven development patterns
- [awesome-cursorrules (GitHub)](https://github.com/PatrickJS/awesome-cursorrules) — Community cursor rules collection
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md) — Community guide for CLAUDE.md authoring

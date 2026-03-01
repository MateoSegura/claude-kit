# claude-kit Research Overview

> **Living document.** Extended as new research is added to this directory.
> Last updated: 2026-02-27

**Date:** 2026-02-28

---

## Table of Contents

1. [The North Star](#1-the-north-star)
2. [The Problems We Are Solving](#2-the-problems-we-are-solving)
3. [Three Operating Modes](#3-three-operating-modes)
4. [The Macro Shift: AI-Native Engineering](#4-the-macro-shift-ai-native-engineering)
5. [Research Index](#5-research-index)
6. [Cross-Cutting Insights](#6-cross-cutting-insights)
7. [Roadmap Signals](#7-roadmap-signals)
8. [How to Extend This Document](#8-how-to-extend-this-document)

---

## 1. The North Star

**claude-kit is the infrastructure layer that turns Claude from a capable assistant
into a reliable engineering system.**

Today, most developers using AI coding tools spend a disproportionate amount of
time managing the AI rather than directing it. They re-explain context that should
already be known. They catch errors that should have been blocked. They manually
coordinate agent sessions that should hand off cleanly. They wonder whether an
agent's output is correct rather than having confidence it was validated.

claude-kit's answer to this is not a faster model or a smarter prompt. It is
**architecture** — a layered system of domain knowledge injection, role-based agent
specialization, enforcement hooks, and workflow primitives that handles the
systemic failure modes of agentic coding so the developer can operate at the level
of intent and architecture rather than prompt management.

The aspiration is a tool that works across three modes, described in Section 3,
from fully autonomous long-running pipelines down to tightly supervised step-by-step
assistance. The same underlying infrastructure — plugins, skills, hooks, teams —
serves all three.

### One-sentence formulation

> claude-kit makes agentic coding reliable by encoding domain expertise, enforcing
> constraints, and managing the complexity of multi-agent workflows — so developers
> can think at the level of what to build, not how to keep the agent on track.

---

## 2. The Problems We Are Solving

The research across this directory maps to ten distinct failure modes in current
agentic coding. These are not hypothetical — they are documented in empirical
studies, benchmark results, and practitioner experience.

| # | Problem | Real-World Evidence | What claude-kit Does |
|---|---------|--------------------|-----------------------|
| 1 | **Non-determinism** | At temperature=0, 1,000 identical runs produced 80 unique completions due to GPU floating-point non-associativity and dynamic batching | Skill injection narrows the output distribution *before* sampling; PostToolUse hooks validate outputs after |
| 2 | **Context drift** | Knowledge in skills becomes stale; LLMs actively prefer in-context content over parametric memory, so outdated skills override correct model knowledge | Versioned skills with `valid_until` / `drift_indicators` frontmatter; `system-updater` drift detection |
| 3 | **Intent ambiguity** | Natural language commands are underspecified; agents optimize for the literal request, not the underlying intent | Typed command interfaces with `input:`, `preconditions:`, `postconditions:`; formal routing via `intent-map.md` |
| 4 | **Error compounding** | A 1% per-step error rate produces a 63% cumulative failure rate at 100 steps; agents double down on initial misunderstandings | Agent-friendly codebase patterns; test coverage as behavioral contracts; early validation hooks |
| 5 | **Lack of runtime governance** | Agents can take irreversible actions (push to remote, delete files, spend money) without human awareness | Hook-based reversibility gates; AgentSpec-style trigger/predicate/enforcement rules; semantic reversibility classification |
| 6 | **Constraint unreliability** | P(follow all N rules) ≈ P(follow one rule)^N — every constraint added to a skill multiplies the failure probability | Hard invariants separated from soft preferences; ≤10 invariants in identity skill; grader as the verification layer |
| 7 | **Multi-agent coordination failure** | Agents sharing context produce conformity bias; sequential pipelines degrade (documented 39% performance drop in multi-turn LLMs) | 5-role team architecture; knowledge plugin as shared context substrate; companion declarations for coherence |
| 8 | **Context switching cost** | Each agent context switch costs up to 40% productivity; full recovery from interruption takes 23 minutes | Session state capture; `claude-kit status`; CHECKPOINT protocol; structured resume handoffs |
| 9 | **Spaghetti code attractor** | GitClear's 211M-line study: code churn doubled, refactoring declined from 25% to 10% under AI assistance | Spec-driven development via `core-spec`; agent-friendly codebase auditing; `core-kit:audit` command |
| 10 | **Skill gap for AI-native engineering** | Entry-level job postings dropped 67% (2023–2024); AI slowed experienced developers 19% on complex tasks without proper scaffolding | Structured workflow templates; onboarding experience; feedback loops that build engineering taste |

---

## 3. Three Operating Modes

claude-kit is designed to serve the same developer across a spectrum of autonomy.
The underlying infrastructure is identical — what changes is the level of human
involvement at each decision point.

### Mode 1 — Full Autonomy (Black Box)

The developer defines the intent (a spec, a workflow, a set of objectives) and
delegates execution entirely to a configured pipeline of agents. The system runs
unsupervised, enforcing its own constraints, validating its own outputs, and
recovering from failures within defined blast-radius limits.

**Requirements:** Agent-friendly codebase (high test coverage, consistent patterns,
typed interfaces). Well-authored skills with hard invariants. Hook-enforced
reversibility gates that block irreversible actions without explicit approval.
A grader agent that validates outputs at each significant step.

**What this looks like today:** `claude-kit --kit embedded-zephyr --yolo` with a
well-instrumented repo and a Stop hook that spawns the grader before the session ends.

**What it needs to become:** Workflow plugin type with DAG task definitions,
checkpoint semantics, automated grader integration, and session state persistence
across runs.

### Mode 2 — Collaborative (Powerful Assistant)

The developer works alongside a specialized agent that has deep domain knowledge,
understands the project's conventions, and produces output that's already been
validated. The developer makes decisions; the agent executes and validates.

**Requirements:** Domain knowledge plugin with authoritative skill content.
Identity skill with clear role boundaries. Grader agent available for
on-demand validation. Hooks that enforce conventions without blocking flow.

**What this looks like today:** The full claude-kit team experience — engineer
writes, grader validates, tester covers, debugger diagnoses.

**What it needs to become:** Richer intent interfaces (typed command schemas),
better context health indicators, inline feedback loops that build the developer's
taste over time.

### Mode 3 — Controlled (High-Oversight Assistant)

The developer retains fine-grained control, reviewing and approving each
significant action. The agent is powerful but operates within explicit checkpoints.
Used for high-stakes operations, unfamiliar codebases, or early stages of a project
where trust hasn't been established.

**Requirements:** Explicit CHECKPOINT markers in workflow definitions. Human-in-the-loop
approval hooks for irreversible actions. Detailed audit trails. Structured handoff
formats that give the developer full context at each review point.

**What this looks like today:** Plan mode (`--permission-mode plan`) with the engineer
plugin and manual review of each proposed action.

**What it needs to become:** Formal CHECKPOINT protocol in command and workflow
definitions; structured session summaries; reversibility classification per tool type.

---

## 4. The Macro Shift: AI-Native Engineering

Two trends define the environment this tool is being built into.

### The AI-native engineer is a new role

The emerging practitioner is not a developer who "uses AI tools." They are a
**director, reviewer, and integrator** of AI output — what some call a "manager of
agents." Their primary skill is not writing code; it is decomposing intent into
agent-sized isolated tasks, validating outputs against architectural judgment, and
coordinating multiple concurrent workstreams without losing context.

This role is demanding. Managing multiple agents without a supporting tool is
cognitively equivalent to managing a team of developers with no project management
infrastructure — possible for exceptional individuals, but systematically unreliable.

### The market is being defined right now

- Claude Code hit $1B ARR in 6 months (fastest ever) and is now at $2.5B annualized
- Entry-level developer hiring dropped 67% in 2023–2024 — the AI-native engineer
  is the new junior hire profile
- The closest public analog to claude-kit (Trail of Bits `claude-code-config`) is
  single-domain, single-org, no hooks, no team model — the gap is wide open
- The ESLint path is the strategic trajectory: composable configs, `extends` pattern,
  community plugin registry, CI integration, org governance

**claude-kit's positioning:** The standard context layer for Claude Code — the tool
that makes Claude reliably domain-expert-level for any team, any stack, any level
of autonomy. Not a model wrapper. Not a prompt marketplace. Infrastructure.

---

## 5. Research Index

Each document covers one research area in depth (~1,000–1,500 lines) with a
concrete "Implications for claude-kit" section. Summaries below are deliberately
brief — read the source for depth.

---

### [theory-context-cache.md](./theory-context-cache.md)
**Topic:** Why claude-kit's skill injection approach works theoretically

**Core finding:** Skill injection is not "prompt engineering." It is soft fine-tuning
via the transformer attention mechanism — each skill reprograms the model's
computation for the domain. LLMs actively prefer contextual knowledge over
parametric memory (training weights), so well-authored skills override incorrect
model defaults. Posterior variance vanishes *exponentially* with each well-chosen
skill added.

**Key implication:** The L0–L5 level framework defines measurable capability tiers.
claude-kit's value prop is moving teams from L0 (raw Claude) to L5 (hooks +
grader + domain knowledge = near-minimum output entropy) for their specific domain.

---

### [llm-non-determinism.md](./llm-non-determinism.md)
**Topic:** Root causes of LLM non-determinism; measurement; mitigation techniques

**Core finding:** Temperature = 0 is not deterministic. GPU floating-point
non-associativity and dynamic batching mean identical requests produce different
outputs based on hardware state and co-occurring requests. True determinism at the
sampling layer is not achievable. The only reliable control is **upstream** — context
engineering is the correct intervention point, not sampling parameters.

**Key implication:** claude-kit's context-first approach is architecturally correct.
Additional levers: temperature declarations in agent frontmatter (grader: 0.1–0.2,
architect: 0.5–0.7), PostToolUse output validation hooks, structured grader output
schemas enforced via JSON Schema, grader auto-spawn on Stop.

---

### [memory-architecture.md](./memory-architecture.md)
**Topic:** Memory types for LLM agents; context window governance; policy-driven forgetting; RAG vs. in-context

**Core finding:** Five memory types exist (in-context, episodic, semantic, procedural,
external). claude-kit's skills are **procedural memory** — how-to patterns and domain
knowledge. The 500-line skill cap is correct in principle but token budget (~3,000
tokens) is the right metric. Skills need `valid_until`, `source_version`, and
`drift_indicators` frontmatter to self-describe when they're stale.

**Key implication:** Three-tier hybrid architecture for large domains: always-loaded
core skills → RAG-selected extended knowledge → on-demand reference files. Currently
claude-kit only has tiers 1 and 3. Tier 2 (dynamic RAG selection) is the next
architectural evolution for knowledge-heavy domains.

---

### [intent-formalization.md](./intent-formalization.md)
**Topic:** Spectrum from natural language to formal specification; DSLs; typed intent interfaces; routing systems

**Core finding:** The intent gap — the distance between what a user means and what an
agent can reliably execute — is the primary source of misaligned agent behavior. The
right architecture is three-layered: **natural language for discovery, schemas for
dispatch, contracts for enforcement**. Tools like DSPy, TypeChat, and Guidance show
that typed interfaces produce 25–65% performance improvements over untyped prompts.

**Key implication:** Commands should have typed `input:` schemas and `postconditions:`
contracts. Skills should have structured `provides:` and `query_when:` declarations.
A `core-intent` plugin could formalize the routing layer. LMQL-style constrained
generation is achievable via PostToolUse schema validation today without changing
the model layer.

---

### [runtime-governance.md](./runtime-governance.md)
**Topic:** Hook design; constitutional AI; semantic reversibility; tool use safety; formal runtime verification

**Core finding:** AgentSpec (ICSE 2026) provides a formal trigger/predicate/enforcement
rule structure that maps directly to claude-kit's hook event system. The key
insight: **deterministic scripts belong in the hot path (PreToolUse/PostToolUse);
LLM reasoning belongs in the slow path (Stop hooks)**. Reversibility must be
classified per tool type — not all bash commands are equal.

**Key implication:** Four-layer reversibility architecture: (A) trivially reversible
— allow silently, (B) compensatable — allow with logging, (C) irreversible but
bounded — require confirmation, (D) permanently unbounded — block. Constitutional
skill content (invariants Claude must never violate) is the complement to hook
enforcement for behaviors that can't be caught at the tool-call level.

---

### [symbolic-scaffolding.md](./symbolic-scaffolding.md)
**Topic:** How symbolic constraints behave in neural systems; constraint reliability; invariant specification; verifiability

**Core finding:** The **Curse of Instructions** — P(follow all N rules) ≈ P(follow
one rule)^N. Every constraint added to a skill multiplies the failure probability.
This is not a prompt quality problem; it is a fundamental property of how attention
distributes across long constraint lists. The mitigation is structural: separate
hard invariants (max 10, machine-readable) from soft preferences, load invariants
at primacy position, and use the grader as the behavioral verification layer.

**Key implication:** Skills need an `invariants:` YAML frontmatter field for
machine-readable hard constraints, separate from prose guidance. The identity skill
should contain ≤10 invariants, stated positively, with concrete specificity. The
grader agent is not just a code reviewer — it is the **verification layer for
symbolic constraints**.

---

### [multi-agent-architecture.md](./multi-agent-architecture.md)
**Topic:** Architecture taxonomies; specialization vs. generalization; coordination patterns; context coherence; failure modes

**Core finding:** Empirical research (MetaGPT, AgentCoder, MapCoder) validates
**4–6 specialized roles as the optimal team size** — directly confirming claude-kit's
5-role model. The MAST taxonomy documents 14 failure modes in multi-agent systems;
the most dangerous is **cascading failure through context pollution**. Claude-kit's
companion plugin architecture (shared knowledge substrate) addresses static coherence
but not dynamic coherence (shared understanding of current task state).

**Key implication:** A formal grader↔engineer handoff protocol with context
partitioning is needed. A workflow plugin type with loop/condition semantics would
enable structured multi-agent pipelines. A minimal session trace format (8 fields)
would give the debugger role the structured input it needs to diagnose cross-agent
failures.

---

### [agent-friendly-codebases.md](./agent-friendly-codebases.md)
**Topic:** Tests as contracts; documentation consistency; design pattern consistency; error compounding; measuring agent-friendliness

**Core finding:** A codebase's agent-friendliness is measurable. A proposed 12-metric
composite score (test coverage, type coverage, linting pass rate, pattern consistency,
file length distribution, documentation currency) produces an "agent safety rating."
Below 40: high risk for autonomous operation. Above 80: safe for black-box runs.
**AI agents use the TypeScript `any` keyword 9x more than humans** — type systems
actively degrade under autonomous coding without enforcement hooks.

**Key implication:** `core-kit:instrument` (the repo instrumentation command from
`ai-instrumentation.md`) should be extended to detect agent-hostile patterns, not
just encode conventions. A `core-kit:audit` command should score a codebase before
autonomous operation. Hooks that enforce `no-any` and similar type-preservation rules
are essential for long-running autonomous sessions.

---

### [ai-native-engineer.md](./ai-native-engineer.md)
**Topic:** The new class of AI-native engineer; manager-of-agents mental model; skills gap; learning by taste

**Core finding:** The AI-native engineer's defining characteristic is mental model,
not tool preference: they treat AI as the primary producer and themselves as
**director, reviewer, and integrator**. McKinsey identifies two archetypes: the
M-shaped orchestrator (generalist coordinator) and the T-shaped domain specialist
(who encodes expertise into pipelines). "Vibe coding" failure is documented —
GitClear found 4x code duplication increase, and the 2025 METR RCT found AI *slowed*
experienced developers 19% on complex tasks without proper scaffolding.

**Key implication:** claude-kit must evolve from "domain knowledge manager" to
**"agent operating system"** — the orchestration layer that makes the developer a
more effective director of agents. A `claude-kit learn` onboarding experience and
session analytics that build engineering taste over time are the differentiated
features for this audience.

---

### [human-agent-orchestration.md](./human-agent-orchestration.md)
**Topic:** Cognitive science of context switching; HITL design patterns; UX for multi-agent workflows; task decomposition; error recovery

**Core finding:** Context switching costs up to **40% of productive time**, and full
recovery from an interruption takes 23 minutes. The bottleneck in multi-agent
orchestration is entirely on the human side — the agent's state is fully recoverable,
but the developer's mental model of each session must be reconstructed from scratch.
Rich session state emission (8-field schema) makes resumption take seconds rather
than minutes.

**Key implication:** `claude-kit status` command showing all running sessions with
current task, files changed, and blocker status. Structured CHECKPOINT protocol in
commands and workflows. Session state auto-capture on switch. Resume context injection
that restores the developer's mental model, not just the agent's working memory.

---

### [developer-tools-landscape.md](./developer-tools-landscape.md)
**Topic:** Competitive map of AI dev tools; plugin ecosystem opportunity; strategic positioning

**Core finding:** Claude Code hit $1B ARR in 6 months. The closest public analog to
claude-kit (Trail of Bits `claude-code-config`) is single-domain, single-org, no
enforcement hooks, no team role model. No existing tool provides versioned +
composable + enforced + role-specialized domain injection. This gap is defensible.

**Key implication:** The ESLint path is the strategic trajectory — shareable configs,
`extends` pattern, community plugin registry, CI integration, org governance. Primary
beachhead: AI-native startups (5–50 person engineering teams) where the pain is
highest and willingness to pay is established. Secondary: enterprise DevEx teams.
Anthropic absorption risk is real but mitigated by community network effects.

---

### [ai-instrumentation.md](./ai-instrumentation.md)
**Topic:** Generating `.claude/` configuration from repository analysis

**Core finding:** Every major AI coding tool has converged on the same need: a
machine-readable description of "how to work in this repository." No existing tool
generates these files from repository analysis — they all require manual authoring.

**Key implication:** `core-kit:instrument` — a command that analyzes a repo (stack
detection, git history patterns, existing conventions) and generates `.claude/rules/`,
`.claude/commands/`, and `hooks.json` — fills this gap. Phase 1: silent detection.
Phase 2: guided Q&A. Phase 3: transparent generation with manifest tracking.
Extended by `agent-friendly-codebases.md` research: instrumentation should also
score and report agent-hostile patterns.

---

## 6. Cross-Cutting Insights

Findings that appear independently across multiple research documents deserve
special weight — they represent convergent evidence, not single-study conclusions.

### 1. Context engineering is the right level of abstraction

`llm-non-determinism.md`, `theory-context-cache.md`, and `symbolic-scaffolding.md`
all converge on the same conclusion from different directions: the most effective
control point for LLM behavior is not the sampling layer, not fine-tuning, and not
post-hoc filtering. It is the **context window** — what the model sees before it
generates a single token. claude-kit's entire architecture is built on this insight.

### 2. The grader is more important than the engineer

`symbolic-scaffolding.md` identifies the grader as the verification layer for
symbolic constraints. `multi-agent-architecture.md` finds that critic agents
produce the largest quality jumps in multi-agent systems. `llm-non-determinism.md`
recommends auto-spawning the grader on Stop as a self-consistency mechanism.
`agent-friendly-codebases.md` proposes grader-driven contracts audits.
**The grader role is underutilized relative to its architectural importance.**

### 3. Hooks and skills are complementary, not redundant

`runtime-governance.md` and `symbolic-scaffolding.md` both arrive at the same
two-layer model independently: **probabilistic enforcement** (skills that make
correct behavior likely) sits below **deterministic enforcement** (hooks that make
incorrect behavior impossible). Skills handle the middle of the distribution; hooks
handle the tails. Neither is sufficient alone.

### 4. The 5-role team is empirically validated

`multi-agent-architecture.md` finds that 4–6 specialized roles is the empirical
sweet spot from AgentCoder, MetaGPT, and MapCoder research. claude-kit's 5-role
model (engineer, grader, tester, debugger, knowledge) predates this research and
matches its conclusions. The architecture is correct — the gap is in **coordination
primitives** (handoff protocols, workflow definitions, context bridges).

### 5. The human bottleneck is real and must be designed for

`human-agent-orchestration.md` and `ai-native-engineer.md` both converge on the
finding that multi-agent orchestration bottlenecks on the human, not the agents.
Context switching costs, prospective memory failures, and cognitive load are the
primary limiting factors. Tools that minimize these (session state, status dashboards,
structured handoffs) are not UX polish — they are **core infrastructure** for the
autonomy modes the tool needs to support.

### 6. Trust requires an audit trail

`runtime-governance.md`, `symbolic-scaffolding.md`, and `multi-agent-architecture.md`
all identify auditability as essential for trust in autonomous systems. Without a
structured record of what each agent decided and why, developers cannot validate
agent behavior, diagnose failures, or build confidence in autonomous operation.
**A minimal session trace format is a prerequisite for autonomous mode, not a
nice-to-have feature.**

---

## 7. Roadmap Signals

The research collectively suggests the following evolution for claude-kit, loosely
ordered by leverage (impact × feasibility):

### Near-term (high leverage, low disruption to existing architecture)

| Feature | Research Basis | What It Enables |
|---------|---------------|-----------------|
| `invariants:` YAML frontmatter in skills | `symbolic-scaffolding.md` | Machine-readable hard constraints; grader can audit constraint compliance |
| Temperature declarations in agent frontmatter | `llm-non-determinism.md` | Role-appropriate sampling; grader at 0.1, architect at 0.5–0.7 |
| Reversibility classification per tool type | `runtime-governance.md` | Four-layer hook architecture: allow/log/confirm/block |
| Typed `input:` / `postconditions:` in command frontmatter | `intent-formalization.md` | Formal intent contracts; better routing; grader can verify postconditions |
| `valid_until` / `drift_indicators` in skill frontmatter | `memory-architecture.md` | Self-describing knowledge staleness; `system-updater` drift detection |
| Grader auto-spawn on Stop hook | `llm-non-determinism.md`, `symbolic-scaffolding.md` | Self-consistency enforcement at session boundary |

### Medium-term (new capabilities, significant but scoped)

| Feature | Research Basis | What It Enables |
|---------|---------------|-----------------|
| `core-kit:audit` command | `agent-friendly-codebases.md` | Agent-friendliness score before autonomous operation |
| CHECKPOINT protocol in commands | `human-agent-orchestration.md` | Structured human-in-the-loop review points |
| `claude-kit status` | `human-agent-orchestration.md`, `developer-tools-landscape.md` | Multi-session visibility; the "manager of agents" dashboard |
| Session state schema + resume injection | `human-agent-orchestration.md` | Context switching without 23-minute recovery cost |
| `core-kit:instrument` anti-pattern detection | `agent-friendly-codebases.md`, `ai-instrumentation.md` | Repo readiness assessment before agent deployment |

### Longer-term (architectural evolution)

| Feature | Research Basis | What It Enables |
|---------|---------------|-----------------|
| Workflow plugin type (DAG task definitions) | `multi-agent-architecture.md`, `human-agent-orchestration.md` | Structured multi-agent pipelines with checkpoints and dependencies |
| Three-tier knowledge architecture (static + RAG + on-demand) | `memory-architecture.md` | Scale knowledge plugins beyond static injection for large domains |
| Session trace format (8-field schema) | `multi-agent-architecture.md`, `runtime-governance.md` | Debugger-ready structured audit trail for cross-agent failures |
| Community plugin registry | `developer-tools-landscape.md` | ESLint-path network effects; composable, versioned, shareable plugins |
| `claude-kit learn` onboarding experience | `ai-native-engineer.md` | Entry point for AI-native engineers building taste through structured feedback |

---

## 8. How to Extend This Document

When new research is added to `docs/research/`:

1. Add a new entry to **Section 5 (Research Index)** following the established format:
   - Document link
   - Topic (one line)
   - Core finding (2–3 sentences, the most important thing it established)
   - Key implication (1–2 sentences, what claude-kit should do differently)

2. Update **Section 6 (Cross-Cutting Insights)** if the new research confirms,
   challenges, or extends an existing cross-cutting finding.

3. Update **Section 7 (Roadmap Signals)** if the research reveals new feature
   priorities or changes the sequencing of existing ones.

4. Update the "Last updated" date at the top.

Do not rewrite the North Star (Section 1) or Operating Modes (Section 3) unless
there is a fundamental strategic shift — these should be stable anchors that new
research is interpreted against, not updated with every document.

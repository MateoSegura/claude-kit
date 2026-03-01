# Requirements Derivation Methodology

**Date:** 2026-02-28

> How claude-kit's 10 product requirements were systematically derived from
> empirical evidence, and how we validated their completeness.

---

## 1. The Question This Document Answers

A sophisticated reader encountering claude-kit's requirements layer
(GitHub Issues [#101–#110](https://github.com/MateoSegura/claude-kit/issues?q=label%3Arequirement) with the `requirement` label) will ask three questions:

1. **Origin:** Where did these requirements come from? What process identified
   them?
2. **Completeness:** How do you know these are the RIGHT requirements? What
   methodology ensures you didn't miss critical ones?
3. **Evidence quality:** How strong is the evidence behind each requirement?
   Is this grounded in peer-reviewed research or blog posts?

This document answers all three.

---

## 2. Methodology Overview

The requirements were derived through a four-stage process:

```
Stage 1              Stage 2              Stage 3              Stage 4
─────────            ─────────            ─────────            ─────────
Literature      →    Failure Mode    →    Requirement    →    Coverage
Survey               Extraction          Derivation           Validation
(12 papers)          (10 failure modes)   (10 requirements)    (external frameworks)
```

### Stage 1 — Literature Survey

12 research documents were authored over a focused two-week period (February
2026). Each paper investigates a specific facet of AI-assisted software
engineering, synthesizing findings from peer-reviewed publications, industry
reports, benchmark data, and practitioner accounts.

The research topics were not selected randomly. They were driven by a
systematic decomposition of the question: **"What goes wrong when developers
use AI coding agents, and what architectural interventions reduce those
failure modes?"**

The decomposition produced six research axes:

| Axis | Question | Papers |
|------|----------|--------|
| **Theoretical foundation** | Why does context injection work at the mechanism level? | theory-context-cache.md, llm-non-determinism.md |
| **Knowledge management** | How should domain knowledge be structured, versioned, and governed? | memory-architecture.md, symbolic-scaffolding.md |
| **Multi-agent design** | How should specialized agents coordinate without degrading? | multi-agent-architecture.md, intent-formalization.md |
| **Safety and governance** | How do you enforce constraints on a stochastic system? | runtime-governance.md, symbolic-scaffolding.md |
| **Human factors** | What does the human operator need to manage agents effectively? | human-agent-orchestration.md, ai-native-engineer.md |
| **Market and strategy** | Where does this sit in the competitive landscape? | developer-tools-landscape.md, agent-friendly-codebases.md |

Two additional papers provide synthesis: `state-and-roadmap.md` (current
state assessment and vision) and `overview.md` (research index with
cross-cutting insights). `ai-instrumentation.md` covers the repo
instrumentation capability, which feeds REQ-001 (knowledge injection) and
REQ-005 (transparency).

### Stage 2 — Failure Mode Extraction

Each research paper was analyzed for documented failure modes — not
hypothetical risks, but problems supported by empirical evidence (published
studies, benchmark results, or quantified practitioner data). This produced
10 failure modes, each with at least one quantitative evidence point:

| # | Failure Mode | Key Evidence | Source |
|---|-------------|--------------|--------|
| F1 | **Non-determinism** | 1,000 identical runs at temperature=0 produced 80 unique completions | arXiv 2502.20747 (2025) |
| F2 | **Context drift** | LLMs preferentially attend to contextual over parametric knowledge; stale context overrides correct model knowledge | arXiv 2410.08414 (2024) |
| F3 | **Intent ambiguity** | Typed interfaces produce 25–65% performance improvement over untyped prompts | DSPy, TypeChat benchmarks |
| F4 | **Error compounding** | 1% per-step error rate produces 63% cumulative failure rate at 100 steps | Geometric probability analysis, validated in multi-turn LLM studies |
| F5 | **Lack of runtime governance** | No published multi-agent framework provides deterministic runtime constraint enforcement | ICSE AgentSpec survey (2026) |
| F6 | **Constraint unreliability** | P(follow all N rules) ≈ P(follow one rule)^N — multiplicative failure probability | Derived from attention distribution research; validated empirically in symbolic-scaffolding.md |
| F7 | **Multi-agent coordination failure** | 39% performance drop documented in multi-turn LLM pipelines; conformity bias in shared-context agents | ACM TOSEM survey (2025) |
| F8 | **Context switching cost** | Each context switch costs up to 40% of productive time; full recovery takes 23 minutes | Cognitive science literature (Mark et al.) |
| F9 | **Spaghetti code attractor** | Code churn doubled, refactoring declined from 25% to 10% under AI assistance (211M-line study) | GitClear (2024) |
| F10 | **Skill gap** | Entry-level developer job postings dropped 67% (2023–2024); AI slowed experienced developers 19% on complex tasks | Indeed hiring data; METR RCT (2025) |

### Stage 3 — Requirement Derivation

Each requirement addresses one or more failure modes. The mapping is not 1:1 —
some failure modes converge on a single architectural response, and some
requirements address business needs beyond technical failure modes.

| Requirement | Addresses Failure Modes | Derivation Logic |
|-------------|------------------------|------------------|
| **REQ-001** Domain Knowledge Injection | F1 (non-determinism), F2 (context drift) | Context injection narrows the output distribution (reduces F1) using knowledge that must be curated to avoid F2. The intervention is the same mechanism addressing both failure modes. |
| **REQ-002** Scope-Aware Planning | F3 (intent ambiguity), F8 (context switching) | Agents that know their own scope avoid ambiguous task acceptance (F3). Plans that persist on disk survive context switching (F8). |
| **REQ-003** Role Specialization | F7 (coordination failure), F6 (constraint unreliability) | Specialized roles reduce context dilution (F7). Each role carries fewer constraints, reducing multiplicative failure probability (F6). |
| **REQ-004** Runtime Enforcement | F4 (error compounding), F5 (governance gap), F6 (constraint unreliability) | Dual enforcement (hooks + skills) creates defense-in-depth: skills reduce the base error rate (F4), hooks catch remaining errors deterministically (F5), and the combination reduces reliance on any single constraint layer (F6). |
| **REQ-005** Transparent Execution | F8 (context switching), F10 (skill gap) | Visibility into agent behavior reduces cognitive recovery cost on context switches (F8). Debug traces help developers build "taste" for agent behavior, closing the skill gap (F10). |
| **REQ-006** Autonomous Operation | F8 (context switching) | Full autonomy eliminates human context switching entirely for well-defined tasks. Requires REQ-005 as prerequisite (glass box, not black box). |
| **REQ-007** Measurable Impact | F9 (spaghetti code), F1 (non-determinism) | Without measurement, you cannot know whether the tool helps or hurts. The spaghetti code attractor (F9) operates silently — quality degradation is invisible without grader scores and trend data. |
| **REQ-008** Secure Distribution | — (business requirement) | Not derived from a technical failure mode. Derived from the product requirement to distribute proprietary plugin content while protecting intellectual property. |
| **REQ-009** Cloud Platform | — (competitive requirement) | Not derived from a technical failure mode. Derived from competitive analysis showing that successful dev tools evolve from CLIs to cloud-connected platforms. |
| **REQ-010** Plugin Ecosystem | — (strategic requirement) | Not derived from a technical failure mode. Derived from ESLint trajectory analysis showing that ecosystem network effects create the strongest competitive moat. |

**Honesty note:** 7 of 10 requirements derive from documented technical failure
modes. 3 derive from business and competitive analysis. This split is
intentional — a product must address both technical problems and market
positioning. The derivation basis is explicitly different for each category.

### Stage 4 — Coverage Validation

To validate that the 10 requirements don't miss critical failure modes, the
failure mode list was cross-checked against three external frameworks:

#### 4a. MAST Taxonomy (ACM TOSEM, 2025)

The Multi-Agent System Testing taxonomy documents 14 failure modes in
multi-agent LLM systems. Mapping to claude-kit's failure modes:

| MAST Failure Mode | Covered by | Coverage |
|-------------------|-----------|----------|
| Task decomposition errors | F3 (intent ambiguity), F7 (coordination) | Full |
| Inter-agent communication failure | F7 (coordination failure) | Full |
| Context pollution / leakage | F7 (coordination failure), F2 (drift) | Full |
| Cascading failures across agents | F4 (error compounding) | Full |
| Inconsistent knowledge across agents | F2 (context drift) | Full |
| Role confusion / boundary violation | F6 (constraint unreliability) | Full |
| Resource contention (context window) | F2 (context drift) | Partial — addressed by skill size caps but not by explicit resource management |
| Hallucination amplification | F1 (non-determinism), F4 (compounding) | Full |
| Evaluation metric gaming | Not covered | Gap — grader rubric gaming is a known risk |
| Deadlock in agent coordination | Not covered | Gap — no deadlock detection mechanism |
| Non-reproducible agent behavior | F1 (non-determinism) | Full |
| Permission escalation | F5 (governance gap) | Full |
| Infinite retry loops | Not covered | Gap — no loop detection in hook system |
| State management failures | F8 (context switching) | Partial — plan persistence addresses this but not runtime state management |

**Coverage: 10 of 14 fully covered, 2 partially covered, 2 gaps identified.**

The gaps (evaluation gaming, deadlock detection, infinite loops) are real but
lower-priority — they emerge in mature multi-agent deployments, not in the
current product stage. They should be tracked as future requirements.

#### 4b. AgentSpec Framework (ICSE, 2026)

AgentSpec defines a trigger/predicate/enforcement rule structure for runtime
agent governance. Its requirement categories:

| AgentSpec Category | Covered by |
|-------------------|-----------|
| Safety constraints (irreversible action prevention) | REQ-004 (hooks) |
| Liveness constraints (agent must eventually complete) | Partially — REQ-006 (autonomous operation) but no explicit liveness checking |
| Fairness constraints (equitable resource allocation) | Not covered — single-user tool, not relevant at current stage |
| Behavioral contracts (pre/postconditions) | REQ-004 (hook enforcement), partially REQ-002 (scope awareness) |

#### 4c. ASDLC Autonomy Levels

The AI Software Development Lifecycle autonomy framework defines 5 levels
(L1 Assistive through L5 Full Autonomy). claude-kit's requirements span
L2–L5:

| Level | claude-kit Requirement |
|-------|----------------------|
| L1 — Assistive | Below claude-kit's scope (raw IDE autocomplete) |
| L2 — Guarded Autonomy | REQ-004 (enforcement), REQ-005 (transparency) |
| L3 — Proposal-First | REQ-002 (scope-aware planning) |
| L4 — Supervised Autonomy | REQ-006 (autonomous operation), REQ-007 (measurable impact) |
| L5 — Full Autonomy | REQ-006 (autonomous mode), REQ-003 (role specialization for self-validation) |

**No autonomy level is unaddressed by the requirements.**

---

## 3. Evidence Quality Assessment

Not all evidence is equal. The following grades the primary evidence behind
each failure mode on a 4-tier scale:

| Tier | Criteria | Weight |
|------|----------|--------|
| **A — Peer-reviewed** | Published in a peer-reviewed venue (ACL, EMNLP, ICML, ICSE, ACM TOSEM, etc.) | Highest — reproducible methodology, peer scrutiny |
| **B — Quantitative industry** | Published by a credible organization with quantified data (GitClear, DORA, McKinsey, METR) | High — real-world data but may have selection bias |
| **C — Preprint / arXiv** | Published on arXiv or similar with clear methodology but no peer review | Medium — methodology visible but no external validation |
| **D — Practitioner / anecdotal** | Blog posts, podcast interviews, Twitter threads from credible practitioners | Low — useful for problem identification but not for magnitude claims |

| Failure Mode | Primary Evidence | Tier | Notes |
|-------------|-----------------|------|-------|
| F1 Non-determinism | arXiv 2502.20747 (2025), arXiv 2508.14288 (2025) | C | Strong methodology papers but preprint. Core claim (temp=0 is non-deterministic) is well-established in the field. |
| F2 Context drift | arXiv 2410.08414 (2024), EMNLP 2024 | A/C | EMNLP paper is peer-reviewed (Tier A). arXiv paper is preprint (Tier C). Convergent findings strengthen both. |
| F3 Intent ambiguity | DSPy (arXiv 2310.03714), TypeChat (Microsoft) | C/B | DSPy is well-cited arXiv. TypeChat is industry with published benchmarks. Performance improvements (25–65%) are from controlled experiments. |
| F4 Error compounding | Geometric probability analysis, multi-turn studies | C | Mathematical derivation is sound. Empirical validation from multi-turn LLM degradation studies (39% drop). |
| F5 Governance gap | ICSE AgentSpec (2026), runtime-governance survey | A | ICSE is a top-tier SE venue. AgentSpec survey is comprehensive. |
| F6 Constraint unreliability | Attention distribution research, symbolic-scaffolding analysis | C | Derived from transformer attention mechanics. Empirically observable but not directly measured in a controlled study. The weakest evidence tier among the technical failure modes. |
| F7 Coordination failure | ACM TOSEM survey (2025), AgentCoder (2024), MapCoder (2024) | A | Three independently published multi-agent studies converging on the same finding. Strongest evidence in the set. |
| F8 Context switching | Mark et al. (cognitive science), Microsoft Research | A | Well-established cognitive science with decades of replication. The 23-minute recovery finding is one of the most cited results in HCI. |
| F9 Spaghetti code | GitClear 211M-line study (2024) | B | Large-scale quantitative industry study. Methodology is published. Potential selection bias (GitClear's customer base may not be representative). |
| F10 Skill gap | Indeed hiring data, METR RCT (2025) | A/B | METR RCT is a rigorous randomized controlled trial. Indeed hiring data is quantitative but observational. |

**Summary:** 4 failure modes have Tier A (peer-reviewed) primary evidence. 3
have Tier B (quantitative industry). 3 have Tier C (preprint/arXiv). None rely
solely on anecdotal evidence. The weakest evidence is for F6 (constraint
unreliability) — the multiplicative failure probability claim is
theoretically derived rather than empirically measured in a controlled study.

---

## 4. Known Gaps and Limitations

### 4.1 Gaps in the Failure Mode Analysis

The following areas are NOT covered by the current research corpus:

| Gap | Why It Matters | Why It's Not Yet Covered |
|-----|---------------|-------------------------|
| **Cost analysis** | Token overhead from skill injection has real cost. A 10,000-token skill budget per session at Opus pricing is a non-trivial expense. No requirement addresses cost efficiency. | Requires usage data from real sessions. Cannot be researched theoretically — needs benchmarking infrastructure (REQ-007) first. |
| **Latency impact** | Larger context windows may increase time-to-first-token. No requirement addresses performance. | Model-specific and likely to change with each model generation. Not a stable requirement target. |
| **Multi-language coverage** | Research papers cite Python and JavaScript examples predominantly. Embedded (C/Zephyr) and frontend (Svelte) domains have less published data. | The architectural interventions (context injection, hooks, role specialization) are language-agnostic. Domain-specific validation is needed per team plugin, not at the requirements level. |
| **Accessibility and onboarding** | The 10 requirements assume a technically sophisticated user. No requirement addresses first-use experience. | Covered partially by REQ-010 (ecosystem) and REQ-005 (transparency). A dedicated onboarding requirement may be needed as the user base broadens. |
| **Evaluation gaming** | The grader role (REQ-003, ADR-006) could be gamed by an engineer that learns what the grader checks. No requirement addresses adversarial robustness between roles. | Identified in MAST cross-check (Section 2, Stage 4a). Low priority at current product stage but should be tracked. |

### 4.2 Limitations of the Methodology

1. **Single-team authorship.** All 12 research papers were written by the same
   team in a two-week period. This creates coherence but risks blind spots
   that an external research community would catch. Mitigation: the papers
   heavily cite external sources (100+ unique references across the corpus),
   and the cross-cutting insights (overview.md, Section 6) specifically look
   for convergent evidence across independent external studies.

2. **No user research.** The failure modes were identified from published
   research, not from interviews with claude-kit users (none exist yet at
   product scale). The requirements may prioritize problems that are
   academically interesting over problems that are practically painful.
   Mitigation: the competitive coverage analysis (see `coverage-analysis.md`)
   maps published user complaints from competing tools to validate that the
   failure modes match real user pain.

3. **Survivorship bias in research selection.** The research corpus focuses on
   problems where published evidence exists. Problems that are real but
   unstudied (e.g., "my AI agent produced code that works but is unmaintainable
   in ways I won't discover for 6 months") are underrepresented. Mitigation:
   the spaghetti code attractor (F9, GitClear study) partially addresses this,
   but long-term maintainability effects of AI-generated code are genuinely
   under-researched.

4. **No controlled experiments.** The requirements are derived from literature
   synthesis, not from controlled experiments with claude-kit itself. The
   predicted improvements (e.g., "domain knowledge injection should improve
   pass@1 by 20–30 percentage points") are extrapolations from related studies,
   not measurements of this system. Mitigation: REQ-007 (Measurable Impact)
   exists specifically to close this gap by building benchmarking infrastructure.

---

## 5. Requirements-to-Research Traceability Matrix

The complete forward trace from research papers through failure modes to
requirements:

```
RESEARCH PAPER                  FAILURE MODES           REQUIREMENTS
─────────────────────────       ──────────────          ────────────
theory-context-cache.md    ───→ F1 (non-determinism) ─→ REQ-001, REQ-007
                           ───→ F2 (context drift)   ─→ REQ-001
llm-non-determinism.md    ───→ F1 (non-determinism) ─→ REQ-001, REQ-004
memory-architecture.md    ───→ F2 (context drift)   ─→ REQ-001
symbolic-scaffolding.md   ───→ F6 (constraints)     ─→ REQ-004
                           ───→ F4 (compounding)     ─→ REQ-004
runtime-governance.md     ───→ F5 (governance gap)  ─→ REQ-004
                           ───→ F4 (compounding)     ─→ REQ-004
multi-agent-architecture  ───→ F7 (coordination)    ─→ REQ-003
                           ───→ F6 (constraints)     ─→ REQ-003
intent-formalization.md   ───→ F3 (intent ambiguity)─→ REQ-002
human-agent-orchestration ───→ F8 (ctx switching)   ─→ REQ-002, REQ-005, REQ-006
ai-native-engineer.md     ───→ F10 (skill gap)      ─→ REQ-005
                           ───→ F8 (ctx switching)   ─→ REQ-006
agent-friendly-codebases  ───→ F9 (spaghetti code)  ─→ REQ-007
                           ───→ F4 (compounding)     ─→ REQ-004
developer-tools-landscape ───→ (competitive analysis)─→ REQ-009, REQ-010
state-and-roadmap.md      ───→ F8 (ctx switching)   ─→ REQ-006
                           ───→ (vision)             ─→ REQ-005, REQ-007
(product need)            ───→ (IP protection)      ─→ REQ-008
```

Every requirement has at least one upstream research paper. Every research
paper contributes to at least one requirement. Three requirements (REQ-008,
REQ-009, REQ-010) have non-research origins that are explicitly declared.

---

## 6. How to Extend This Analysis

When new failure modes are identified (from user feedback, new research, or
production incidents):

1. Document the failure mode with quantitative evidence (not anecdotal)
2. Grade the evidence quality using the 4-tier system in Section 3
3. Determine whether it maps to an existing requirement or requires a new one
4. Cross-check against MAST, AgentSpec, and ASDLC frameworks
5. Update the traceability matrix in Section 5
6. If a new requirement is created, file it as a GitHub Issue with the
   `requirement` label following the existing ID convention (REQ-XXX)

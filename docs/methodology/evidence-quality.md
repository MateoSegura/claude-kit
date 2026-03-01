# Evidence Quality Assessment

**Date:** 2026-02-28

> Grading the evidence behind claude-kit's requirements — what is peer-reviewed,
> what is industry-quantified, and what is anecdotal.

---

## 1. Purpose

claude-kit's requirements derive from a 12-paper research corpus authored in
February 2026. This document grades the evidence quality behind each claim
using a 4-tier system, so a reader can assess which claims rest on strong
foundations and which require further validation.

## 2. Tier Definitions

| Tier | Label | Criteria | Example |
|------|-------|----------|---------|
| **A** | Peer-reviewed | Published in a peer-reviewed venue (ACL, EMNLP, ICML, ICSE, ACM TOSEM, NeurIPS) | AgentCoder (arXiv 2312.13010, ACL-cited) |
| **B** | Quantitative industry | Published by a credible organization with quantified data and disclosed methodology | GitClear 211M-line study, METR RCT, DORA 2025, JetBrains survey |
| **C** | Preprint / arXiv | Published with clear methodology but not yet peer-reviewed | arXiv 2502.20747 (LLM determinism measurement) |
| **D** | Practitioner / anecdotal | Blog posts, podcast interviews, or conference talks from credible practitioners | Karpathy "LLM as CPU" analogy, Anthropic engineering blog |

**Tier B is not inferior to Tier A for industry claims.** A GitClear study
analyzing 211M lines of production code is more relevant to code quality
claims than any controlled lab experiment. The tiers measure *type* of
evidence, not inherent superiority.

## 3. Evidence Inventory by Failure Mode

### F1: Non-Determinism

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| Temperature=0 is non-deterministic | arXiv 2502.20747: 1,000 runs → 80 unique completions | C | Strong methodology, preprint. Core claim widely accepted in the field. |
| Structural entropy measures output variance | arXiv 2508.14288 (SCE on ASTs) | C | Novel measurement framework, not yet replicated. |
| Self-consistency improves with specific prompts | Wang et al. 2023 (self-consistency) | A | Peer-reviewed, highly cited. |
| LLM code review varies across runs | arXiv 2502.20747 | C | Same study as above. |
| AI models show quality regressions over time | IEEE Spectrum 2025 (silent failures) | B | Industry report with named sources. |
| Anthropic infrastructure bugs degraded quality | Anthropic postmortem (2025) | B | First-party disclosure. |

**Aggregate tier: C+ (strong preprint evidence, partially peer-reviewed)**

### F2: Context Drift

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| LLMs prefer contextual over parametric knowledge | arXiv 2410.08414 | C | Well-cited preprint, consistent with peer-reviewed RAG literature. |
| RAG outperforms fine-tuning for knowledge injection | EMNLP 2024 | A | Peer-reviewed, top venue. |
| Stale context overrides correct model knowledge | Derived from above | — | Logical implication, not independently measured. |
| Cursor context compressor loses session state | Cursor Forum bug reports | D | User reports, reproducible. |

**Aggregate tier: B+ (one Tier A, strong Tier C, supported by user reports)**

### F3: Intent Ambiguity

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| Typed interfaces improve performance 25–65% | DSPy (arXiv 2310.03714) | C | Well-cited, large user base, multiple evaluations. |
| TypeChat reduces output errors | Microsoft TypeChat | B | Industry tool with published benchmarks. |
| Copilot produces 30% speculative content | GitHub community report | D | Single documented case, but detailed and reproducible. |
| Aider misinterprets markdown prompts | Practitioner blog posts | D | Anecdotal but consistent pattern. |

**Aggregate tier: C (good preprint + industry evidence, weak empirical measurement)**

### F4: Error Compounding

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| 1% per-step error → 63% cumulative at 100 steps | Geometric probability (mathematical derivation) | — | Mathematical fact, not empirical. |
| Multi-agent configs degrade 39–70% vs single-agent | CooperBench (arXiv 2601.13295) | C | Recent, detailed methodology. |
| 39% performance drop in multi-turn LLM pipelines | ACM TOSEM survey 2025 | A | Peer-reviewed survey of literature. |
| AI code has 1.75x more logic/correctness errors | The Register (2025), citing controlled study | B | Quantified industry report. |
| Replit agent escalated errors over multiple days | Fortune (2025) | B | Detailed documented incident. |

**Aggregate tier: B+ (mathematical + Tier A survey + documented incidents)**

### F5: Governance Gap

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| No framework provides deterministic runtime enforcement | AgentSpec ICSE 2026 survey | A | Top-tier SE venue, comprehensive survey. |
| 69 vulnerabilities across 5 AI coding tools | Tenzai study (December 2025) | B | Systematic security audit with reproducible methodology. |
| OWASP Top 10 in 45% of AI-generated code | GenAI Code Security Report 2025 | B | 80 tasks, 100+ LLMs, 4 languages. |
| CVE-2025-59536 (Claude Code RCE) | CVE database | A | Verified vulnerability with assigned CVE. |
| All tools introduced SSRF; zero implemented CSRF protection | Tenzai study | B | Consistent finding across all 5 tools. |

**Aggregate tier: A- (Tier A survey + strong Tier B security audits)**

### F6: Constraint Unreliability

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| P(all N rules) ≈ P(one)^N multiplicative failure | Derived from attention distribution mechanics | — | Theoretical derivation, not directly measured. |
| Constraint reliability degrades with instruction count | Implied by lost-in-the-middle (Liu et al. 2023) | A | Peer-reviewed, highly cited. |
| Codex ignores approval_policy="never" | GitHub issue reports | D | Reproducible bug, multiple reporters. |
| Cursor modifies files user didn't request | Cursor Forum | D | Multiple user reports. |

**Aggregate tier: C- (theoretical derivation, indirectly supported by Tier A attention research, weak direct measurement — the weakest failure mode in the set)**

### F7: Multi-Agent Coordination Failure

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| 4–6 roles is the empirical sweet spot | AgentCoder, MapCoder, MetaGPT | A | Multiple peer-reviewed studies converging. |
| AgentCoder: 91.5% vs 86.8% pass@1 | AgentCoder (2024) | A | Controlled experiment. |
| MAST taxonomy: 14 failure modes | ACM TOSEM 2025 | A | Peer-reviewed, comprehensive. |
| "Curse of coordination" in CooperBench | arXiv 2601.13295 | C | Recent, detailed, not yet peer-reviewed. |
| Failed agentic PRs show broader, more invasive changes | arXiv 2601.15195 | C | Empirical study of GitHub PRs. |

**Aggregate tier: A (strongest evidence in the entire set — multiple Tier A studies converging independently)**

### F8: Context Switching Cost

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| Context switching costs up to 40% productivity | Mark et al. (cognitive science) | A | Decades of replication, highly cited. |
| Full recovery takes 23 minutes | Mark et al. | A | Same research lineage. |
| METR: AI slowed experienced devs 19% | METR RCT (2025) | A | Randomized controlled trial. |
| Developers forecasted 24% improvement, got 19% slowdown | METR RCT | A | Rigorous pre-registration. |

**Aggregate tier: A (peer-reviewed cognitive science + gold-standard RCT)**

### F9: Spaghetti Code Attractor

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| Code churn doubled (2020–2024) | GitClear 211M-line study | B | Largest code quality dataset published. |
| Refactoring declined from 25% to 10% | GitClear | B | Same study, longitudinal. |
| Code duplication increased 8x in 2024 | GitClear 2025 update | B | Updated data. |
| Enrichlead: 15K lines of unauditable AI code → shutdown | Practitioner account (2025) | D | Single case study. |

**Aggregate tier: B (strong quantitative industry data, weak on controlled causation)**

### F10: Skill Gap

| Claim | Evidence | Tier | Notes |
|-------|----------|------|-------|
| Entry-level job postings dropped 67% | Indeed hiring data (2023–2024) | B | Quantitative observational data. |
| AI slowed experienced devs 19% on complex tasks | METR RCT (2025) | A | Randomized controlled trial. |
| 85% of developers use AI regularly | JetBrains survey (24,534 devs, 2025) | B | Large-scale survey with disclosed methodology. |
| Trust in AI accuracy fell from 40% to 29% | Stack Overflow survey (49,000 devs, 2025) | B | Annual benchmark survey. |
| 66% cite "almost right but not quite" as biggest frustration | Stack Overflow 2025 | B | Same survey. |

**Aggregate tier: A- (RCT + two large-scale industry surveys)**

## 4. Summary

| Failure Mode | Aggregate Evidence Tier | Confidence |
|-------------|------------------------|------------|
| F1 Non-determinism | C+ | Moderate — well-accepted but pre-print primary evidence |
| F2 Context drift | B+ | High — peer-reviewed RAG research + consistent user reports |
| F3 Intent ambiguity | C | Moderate — good tooling evidence, weak on magnitude |
| F4 Error compounding | B+ | High — mathematical + peer-reviewed + documented incidents |
| F5 Governance gap | A- | Very high — ICSE survey + systematic security audits |
| F6 Constraint unreliability | C- | Low-moderate — theoretical, weakest direct evidence |
| F7 Coordination failure | A | Very high — multiple convergent peer-reviewed studies |
| F8 Context switching | A | Very high — decades of cognitive science + RCT |
| F9 Spaghetti code | B | High — largest published code quality dataset |
| F10 Skill gap | A- | Very high — RCT + two large-scale surveys |

**Overall assessment:** 4 of 10 failure modes have Tier A primary evidence.
3 have Tier B. 3 have Tier C. None rely solely on anecdotal evidence.

The weakest link is **F6 (constraint unreliability)** — the multiplicative
failure probability claim is derived from attention mechanics rather than
directly measured. This should be flagged as a hypothesis requiring empirical
validation via claude-kit's benchmarking infrastructure (REQ-007).

## 5. External Validation Sources

Beyond the internal research corpus, the requirements are validated against
three independent large-scale data sources:

| Source | Sample Size | Key Finding Relevant to claude-kit |
|--------|------------|-----------------------------------|
| **JetBrains Developer Ecosystem 2025** | 24,534 devs | Top concern: code quality (23%), lack of context awareness (10%). Enterprise buyers prioritize governance and transparency. |
| **Stack Overflow Developer Survey 2025** | ~49,000 devs | Trust in AI accuracy fell from 40% to 29%. 66% say "almost right but not quite" is the biggest frustration. 76% won't use AI for deployment. |
| **DORA 2025** | ~5,000 respondents + 100h qualitative | AI is an amplifier, not a fixer. AI adoption has negative relationship with delivery stability. |

These three surveys collectively represent ~78,000 developers and
independently confirm the failure modes identified in claude-kit's research
corpus — particularly F1 (non-determinism/quality), F5 (governance), and
F10 (skill gap / trust erosion).

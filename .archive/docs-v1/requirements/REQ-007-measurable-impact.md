# REQ-007: Measurable Impact

**Status:** active
**Priority:** should
**Created:** 2026-02-28

## Context

The fundamental business question for any AI development tool is: "Is this
actually producing better output than the base model alone?" Without
quantitative measurement, the value proposition rests on subjective impressions.
The agent-friendly-codebases research emphasizes that agents operating on
well-structured projects with explicit contracts outperform agents on poorly-
structured projects — but this claim requires measurement infrastructure to
verify.

The state-and-roadmap research designs a level ablation study (L0 through L5)
that isolates the contribution of each architectural layer: raw model, tools,
identity, domain knowledge, multi-agent specialization, and deterministic
enforcement. The theory-context-cache research predicts that the largest
improvement comes from L2→L3 (adding domain knowledge), consistent with the
exponential posterior variance reduction from in-context examples. These
predictions must be testable.

The user needs a "feel" signal — not a dashboard with charts, but simple
trend data that answers "is having claude-kit loaded making my output better
this week versus last week?" This requires lightweight session instrumentation,
not heavyweight benchmarking infrastructure.

## Requirement

The system shall provide mechanisms to measure and compare output quality:

1. **Session scoring** — Every session produces a quality score via the grader
   role, capturing correctness, style conformance, and domain idiomaticity.
2. **Comparative baselines** — Sessions can be run with and without plugins
   loaded, producing comparable output that answers whether the tool helps.
3. **Trend reporting** — Aggregated session data surfaces quality trends over
   time so the user can calibrate trust.
4. **Level attribution** — The system can attribute quality improvements to
   specific architectural layers (knowledge injection, role specialization,
   hook enforcement) through configuration variants.

## Acceptance Criteria

- [ ] Grader scores are recorded in session logs with consistent format
- [ ] The same prompt can be run with different plugin configurations
- [ ] A reporting command shows quality trends across recent sessions
- [ ] Reports compare plugged vs. unplugged sessions when both exist
- [ ] Session data includes token count, duration, and tool call count
      alongside quality scores
- [ ] The scoring methodology is documented and reproducible

## Traces

- **From:** agent-friendly-codebases.md (measurable agent performance on
  structured vs. unstructured projects), state-and-roadmap.md (level ablation
  study, benchmarking design), theory-context-cache.md (predicted improvement
  at each cache level)
- **To:** ADR-006 (grader as verifier — the scoring mechanism)

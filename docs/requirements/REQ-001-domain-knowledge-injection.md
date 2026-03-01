# REQ-001: Domain Knowledge Injection

**Status:** active
**Priority:** must-have
**Created:** 2026-02-28
**Governing Process:** PROC-LC-002 (Requirements Engineering)

## Context

AI coding agents operating on general parametric memory produce code that is
statistically plausible but domain-incorrect. Research on LLM knowledge
injection demonstrates that contextual knowledge overrides parametric memory
(arXiv 2410.08414) and that posterior variance from task uncertainty vanishes
exponentially with well-chosen in-context examples (Arora et al., 2025). A 2024
ACM TOSEM study measured a 51% CodeBLEU degradation when domain-specific code
generation operates without domain context.

The theory-context-cache research formalizes this as a hierarchical cache:
identity skills (L1), domain skills (L2), reference files (L3), and external
knowledge (L4/disk). Each layer reduces output entropy — the model's uncertainty
about what constitutes correct domain code. The memory-architecture research
adds that LLMs preferentially attend to contextual over parametric knowledge,
making curated skill injection functionally equivalent to fine-tuning but
cheaper, more flexible, and fully transparent.

claude-kit must provide a mechanism for injecting curated, authoritative domain
knowledge into agent context windows so that outputs converge on domain-correct
code rather than statistically-likely guesses.

## Requirement

The system shall support hierarchical injection of curated domain knowledge into
LLM context windows, where:

1. Knowledge is organized as discrete, composable skill units scoped to specific
   domain subsystems (e.g., a single RTOS kernel, a specific cloud framework).
2. Each skill unit is human-authored, version-controlled, and reviewable —
   not auto-generated from scraped documentation.
3. Skills are loaded selectively per agent role, so that each agent receives
   only the knowledge relevant to its task (locality exploitation).
4. The injection hierarchy preserves attention priority: identity knowledge
   loads first (primacy), domain skills load next, reference material loads
   on demand.
5. Individual skills are capped in size to prevent the "lost in the middle"
   attention degradation identified by Liu et al. (2023).

## Acceptance Criteria

- [ ] Skills are discrete markdown files loadable independently
- [ ] Agent frontmatter declares which skills to load (selective injection)
- [ ] Skill load order is deterministic and controlled by the agent author
- [ ] No single skill exceeds 500 lines (attention degradation threshold)
- [ ] Domain knowledge overrides model parametric memory for domain-specific
      facts (verifiable via targeted benchmark questions)
- [ ] Skills are human-readable, auditable, and diffable via standard VCS

## Traces

- **Upstream:** theory-context-cache.md (hierarchical context cache framework),
  memory-architecture.md (contextual vs parametric knowledge preference)
- **Downstream:** ADR-001 (context engineering as primary intervention),
  ADR-004 (companion system for cross-role knowledge sharing)
- **Quality Attributes:** None identified

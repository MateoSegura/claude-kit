# ADR-001: Context Window Engineering as Primary Intervention

**Status:** accepted
**Date:** 2026-02-28
**Governing Process:** PROC-LC-003 (Architecture Design)

## Context

Three approaches exist for customizing LLM behavior on domain-specific tasks:

1. **Fine-tuning** — Modify model weights through additional training on
   domain data. Produces permanent behavioral changes. Requires GPU
   infrastructure, training data curation, and re-training on each model
   update. Changes are opaque (embedded in weights) and irreversible without
   re-training.

2. **Retrieval-Augmented Generation (RAG)** — Dynamically retrieve relevant
   documents at inference time and inject them into context. Requires vector
   database infrastructure, embedding pipelines, and chunking strategies.
   Retrieved content may be noisy or irrelevant depending on query quality.

3. **Context engineering** — Architect the content, structure, and hierarchy
   of the context window to narrow the model's output distribution toward
   domain-correct responses. No infrastructure beyond file management.
   Changes are transparent (readable markdown), instantly updatable, and
   composable.

The theory-context-cache research demonstrates that context injection
reconfigures the model's computation during inference — prompts function as
configuration parameters for a virtual neural network (arXiv 2503.20561).
The model preferentially attends to contextual over parametric knowledge
(arXiv 2410.08414), and posterior variance vanishes exponentially with
well-chosen in-context examples (Arora et al., 2025).

The llm-non-determinism research adds that even at temperature zero, LLM
outputs vary across runs due to floating-point non-associativity and
multi-GPU parallelism. Context specificity is the primary lever for reducing
this variance — more specific context produces higher self-consistency
(Wang et al., 2023).

The symbolic-scaffolding research frames context injection as embedding
symbolic constraints (Bayesian priors) into a neural system — a neuro-symbolic
architecture where explicit structures guide probabilistic computation.

## Decision

Context window engineering is claude-kit's primary intervention mechanism. The
system does not fine-tune models, does not operate vector databases, and does
not require infrastructure beyond the filesystem. All domain customization is
achieved through structured injection of curated content into the context
window.

This means:
- Skills are markdown files, not embeddings or weight deltas
- Changes take effect on the next session, not after a training run
- Users can read, audit, and diff exactly what the model "knows"
- The system works with any model that accepts a context window
- No external services are required for core functionality

## Consequences

### Positive

- Zero infrastructure cost — no GPUs, no vector DBs, no embedding pipelines
- Instant iteration — edit a skill file, restart the session, see the effect
- Full transparency — every piece of injected knowledge is human-readable
- Model-agnostic — works with any model that accepts long context
- Composable — skills are independent units that can be mixed per task

### Negative

- Context window is finite — cannot inject unlimited domain knowledge
- Skill quality is critical — bad context actively overrides correct parametric
  knowledge, producing worse results than no context at all
- Manual curation required — skills must be authored and maintained by domain
  experts, not auto-generated
- No persistent learning — the model does not retain session-to-session
  improvements; every session starts from the same skill baseline

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

## Traces

- **Upstream:** REQ-001 (Domain Knowledge Injection)
- **Downstream:** (future SPEC documents implementing the skill system)
- **Quality Attributes:** modifiability, transparency, composability

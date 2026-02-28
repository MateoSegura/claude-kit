# ADR-003: Dual Enforcement — Probabilistic Skills and Deterministic Hooks

**Status:** accepted
**Date:** 2026-02-28

## Context

Runtime governance for AI agents must address a fundamental challenge: LLM
behavior is stochastic. The same instruction produces different tool-call
sequences on different runs. Traditional enforcement mechanisms (type systems,
assertions) assume deterministic execution and are insufficient.

The runtime-governance research maps the enforcement spectrum from weakest
to strongest:

1. **Prompting** — Tell the model what to do. No guarantee of compliance.
2. **Structured output** — Constrain the output format. Compliance is format-
   level, not semantic-level.
3. **Tool filtering** — Restrict which tools the agent can call. Coarse-grained.
4. **Pre/post validation** — Inspect inputs and outputs of tool calls with
   scripts that can block execution. Deterministic for pattern-matchable
   violations.
5. **Formal verification** — Prove properties about the agent's behavior.
   Theoretically ideal, practically infeasible for stochastic systems.

No single mechanism provides both coverage and certainty. The symbolic-
scaffolding research proposes a neuro-symbolic architecture that combines
probabilistic guidance (constraints embedded in context as Bayesian priors)
with deterministic enforcement (symbolic checks that fire on every action).

This mirrors defense-in-depth in security: each layer catches what the
previous layer missed.

## Decision

claude-kit implements two complementary enforcement layers that operate
simultaneously:

**Layer 1 — Probabilistic (Skills):**
Skills injected into the agent's context establish behavioral norms: which
APIs to use, which patterns to follow, which anti-patterns to avoid. These
function as Bayesian priors that shift the model's output distribution toward
correct behavior. They reduce the base error rate but cannot eliminate errors
because the model is free to deviate from instructions.

**Layer 2 — Deterministic (Hooks):**
Shell scripts bound to tool-use lifecycle events (PreToolUse, PostToolUse,
Stop) inspect every action and can block execution with certainty. A PreToolUse
hook that pattern-matches `rm -rf /` blocks it regardless of how persuasively
the LLM argues for it. PostToolUse hooks validate output quality (linting,
syntax checking) after every write. Hook verdicts are binary — allow or block
— with no probabilistic interpretation.

The layers are complementary:
- Skills reduce the probability of errors from high to low
- Hooks catch the remaining errors with certainty
- Without skills, hooks would fire constantly (high false-positive-like noise)
- Without hooks, skills leave residual risk from model non-compliance

## Consequences

**Positive:**
- Defense-in-depth — no single layer failure compromises the system
- Skills handle the long tail of domain-specific guidance that would be
  impractical to encode as hook patterns
- Hooks provide hard guarantees for safety-critical operations
- The combination is measurably more effective than either layer alone
  (testable via ablation)
- Hooks are auditable shell scripts — no ML interpretation required

**Negative:**
- Two layers to maintain — skill updates and hook updates must stay consistent
- Hook pattern matching is limited to textual patterns — semantic violations
  that don't match a regex escape the deterministic layer
- Skills add context window pressure — every enforcement skill consumes tokens
  that could hold domain knowledge
- The interaction between layers can be complex — a skill might instruct
  behavior that a hook then blocks, creating confusing user experiences

## Traces

- **From:** REQ-004 (Runtime Enforcement)
- **To:** (future SPEC documents implementing hook and skill enforcement)

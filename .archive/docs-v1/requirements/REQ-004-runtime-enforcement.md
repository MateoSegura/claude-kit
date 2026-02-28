# REQ-004: Runtime Enforcement

**Status:** active
**Priority:** must
**Created:** 2026-02-28

## Context

Traditional software enforces contracts at compile time (types, static analysis)
and deployment time (CI gates). AI agents break these assumptions because their
behavior is stochastic — the same goal produces different tool-call sequences on
different runs. The runtime-governance research identifies a "governance gap"
where autonomous agents can take irreversible actions (deleting files, pushing
code, dropping tables) without any runtime check equivalent to a type system.

The symbolic-scaffolding research proposes a neuro-symbolic solution: embed
constraints as explicit, verifiable symbolic structures that function as
Bayesian priors guiding the neural system. These constraints operate at two
complementary layers:

- **Deterministic enforcement (hooks):** Shell scripts that fire on tool-use
  events and can block dangerous operations with certainty. A PreToolUse hook
  that rejects `rm -rf /` always works, regardless of what the LLM intended.
- **Probabilistic enforcement (skills):** Knowledge injected into context that
  guides the model toward correct behavior but cannot guarantee it. A skill
  that says "never use deprecated API X" reduces the probability of X appearing
  but cannot eliminate it.

Neither layer alone is sufficient. Skills without hooks produce well-intentioned
but unverified output. Hooks without skills produce correct-but-brittle
enforcement that catches errors too late. The combination creates a defense-in-
depth architecture where skills reduce the error rate and hooks catch the errors
that remain.

## Requirement

The system shall enforce behavioral constraints on agent actions through two
complementary layers:

1. **Deterministic hooks** — Shell scripts bound to tool-use events
   (PreToolUse, PostToolUse, Stop) that can inspect, allow, modify, or block
   agent actions with certainty. Hook verdicts are binary (allow/block) and
   override the LLM's intent.
2. **Probabilistic skills** — Knowledge injected into agent context that
   establishes behavioral norms, coding standards, and domain constraints.
   Skills guide the model's output distribution but do not guarantee compliance.
3. **Layered defense** — Both layers must be active simultaneously. Skills
   reduce the base error rate; hooks catch remaining violations. The system
   must not rely on either layer alone.

## Acceptance Criteria

- [ ] Hooks fire on every tool-use event (PreToolUse, PostToolUse) without
      exception
- [ ] A hook returning exit code 2 blocks the tool action regardless of the
      LLM's intent
- [ ] Hook scripts are deterministic — same input always produces same verdict
- [ ] Skills are loaded into agent context before the first tool use
- [ ] Dangerous operations (force-push, recursive delete, schema drops) are
      blocked by hooks even when the LLM explicitly requests them
- [ ] PostToolUse hooks validate output quality (linting, syntax checking)
      after every write operation
- [ ] The combination of hooks and skills produces a measurably lower error
      rate than either layer alone (verifiable via ablation benchmark)

## Traces

- **From:** runtime-governance.md (governance gap, enforcement spectrum),
  symbolic-scaffolding.md (neuro-symbolic constraint embedding, Bayesian priors)
- **To:** ADR-003 (dual enforcement architecture)

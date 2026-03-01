# ADR-006: Grader as Independent Verifier

**Status:** accepted
**Date:** 2026-02-28

## Context

The multi-agent-architecture research identifies a counterintuitive finding:
in multi-agent code generation systems, the verification role is
architecturally more important than the generation role. AgentCoder (2024)
demonstrated that adding a test-generating agent that validates the coder
agent's output improved pass@1 more than improving the coder agent itself.

The llm-non-determinism research explains why: LLMs exhibit irreducible
variance even at temperature zero. The same prompt produces structurally
different code across runs. A code-generating agent that evaluates its own
output is subject to the same biases that produced the output — self-
evaluation converges on confirming the original approach rather than
identifying its flaws. Independent verification breaks this confirmation bias.

The symbolic-scaffolding research frames verification as a formal property:
constraints embedded as symbolic structures (grading rubrics, coding standards,
test suites) provide an objective reference that the verifier evaluates against.
The grader is not expressing an opinion — it is checking observable properties
against a defined standard.

This has direct implications for system architecture: if verification is more
valuable than generation, the grader role deserves equal or greater investment
in skill quality, rubric design, and behavioral constraints compared to the
engineer role.

## Decision

The grader role in claude-kit is an independent verifier with the following
architectural properties:

1. **Read-only tool access** — The grader cannot modify production code. It
   reads code, reads test results, reads lint output, and produces an
   evaluation. This separation ensures the grader cannot "fix" issues it
   finds, which would compromise its independence.

2. **Rubric-driven evaluation** — The grader evaluates against explicit
   rubrics defined in its skills, not against its own judgment. Rubric items
   are concrete and checkable: "Does the code use the correct API version?"
   not "Is the code good?"

3. **Structured output** — Grader output follows a defined format: numerical
   score, issue list with severity, and specific file/line references. This
   enables automated tracking and trend analysis.

4. **Mandatory on session end** — In autonomous mode, the grader auto-spawns
   at session end (Stop hook) to evaluate the engineer's output. The session
   log includes the grader score as a standard field.

5. **Cannot be influenced by the engineer** — The grader loads its own
   skills and operates in its own context. It does not see the engineer's
   reasoning, only the engineer's output. This prevents the engineer from
   "explaining away" issues.

## Consequences

### Positive

- Independent verification catches errors that self-evaluation misses
- Rubric-driven evaluation is reproducible — the same code scores the same
  across grader runs (modulo LLM variance)
- Structured output enables quantitative tracking of code quality over time
- Automatic grading on session end ensures no session goes unevaluated in
  autonomous mode
- The grader's evaluation is the primary signal for "is this tool helping?"

### Negative

- Grader quality is a bottleneck — a poorly designed rubric produces
  misleading scores that erode trust
- Read-only restriction means the grader cannot fix trivial issues it finds,
  requiring a separate fix cycle
- Grader context window budget competes with rubric detail — comprehensive
  rubrics consume tokens
- LLM variance affects the grader too — the same code may receive different
  scores across runs, requiring aggregation strategies

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

---
name: core-testing:coverage-strategy
description: "Line vs branch vs path coverage, mutation testing, coverage as a tool not a target, and risk-based coverage allocation"
user-invocable: false
---

# Coverage Strategy Quick Reference

## Coverage Metrics Explained

### Line Coverage (Statement Coverage)

**What it measures**: Percentage of executable lines that were executed during tests.

```
function divide(a, b):
    if b == 0:              // line 1
        return "error"      // line 2
    return a / b            // line 3

// Test: divide(10, 2) -> exercises lines 1, 3
// Line coverage: 2/3 = 67%
// Missing: line 2 (the error path)
```

**Limitation**: A line can be "covered" without checking the result. Executing code is not the same as testing it.

### Branch Coverage (Decision Coverage)

**What it measures**: Percentage of branches (true/false outcomes of conditionals) that were taken.

```
function classify(age):
    if age < 0:             // branch 1: true/false
        return "invalid"
    if age < 18:            // branch 2: true/false
        return "minor"
    return "adult"

// Test 1: classify(25) -> branch 1 false, branch 2 false
// Test 2: classify(10) -> branch 1 false, branch 2 true
// Branch coverage: 3/4 = 75%
// Missing: branch 1 true (negative age)
```

**Stronger than line coverage**: 100% line coverage does not guarantee 100% branch coverage. Always prefer branch coverage if your tooling supports it.

### Path Coverage

**What it measures**: Percentage of unique execution paths through a function.

For `N` independent branches, there are up to `2^N` paths. Path coverage explodes combinatorially and is rarely achievable at 100%. Useful conceptually but impractical as a target.

### Condition Coverage

**What it measures**: Whether each boolean sub-expression has been true and false.

```
if (isAdmin OR isOwner):
    allow()

// Condition coverage requires:
// isAdmin=true, isAdmin=false, isOwner=true, isOwner=false
// (4 conditions, not just 2 branches)
```

**MC/DC (Modified Condition/Decision Coverage)**: Each condition independently affects the decision. Required in safety-critical domains (DO-178C, IEC 62304).

## What 100% Coverage Means (and Does Not Mean)

**100% coverage means**: Every line/branch was executed at least once during testing.

**100% coverage does NOT mean**:
- The code is bug-free
- All edge cases are tested
- Return values are checked
- Error conditions are handled correctly
- Concurrent behavior is tested
- Performance is adequate

```
// 100% line coverage, 0% useful testing:
function add(a, b):
    return a + b

test:
    add(1, 2)    // Covers the line. Never checks the result.
```

## Mutation Testing

**Concept**: Modify the source code (introduce "mutants") and check whether tests fail. If a mutant survives (tests still pass), the tests are weak at that point.

**Common mutations**:

| Mutation | Example |
|----------|---------|
| Negate conditional | `if a > b` becomes `if a <= b` |
| Change operator | `a + b` becomes `a - b` |
| Remove statement | Delete a method call |
| Change constant | `return 0` becomes `return 1` |
| Change return value | `return true` becomes `return false` |

**Mutation score** = killed mutants / total mutants

A high mutation score means tests are sensitive to code changes — they actually verify behavior, not just execute code.

**When to use mutation testing**:
- Critical business logic
- Code with high coverage but low confidence
- Security-sensitive paths
- Periodic audit of test quality

**When NOT to use**: On trivial code, generated code, or entire codebases (too expensive). Target it at high-risk modules.

## Coverage as a Tool, Not a Target

**Coverage is a diagnostic tool** that reveals untested code. It should inform decisions, not drive them.

**Anti-patterns**:
- Mandating 100% coverage on all code (leads to low-value tests)
- Gaming coverage with assertion-free tests
- Treating coverage as a quality metric instead of a testing completeness metric
- Blocking PRs on arbitrary coverage thresholds without context

**Healthy coverage practices**:
- Track coverage trends (declining coverage on active code = red flag)
- Use coverage diff on PRs: new/changed code should be tested
- Set minimum thresholds only on critical paths, not globally
- Investigate uncovered lines — some are intentionally untested, others are bugs waiting to happen

## Risk-Based Coverage Allocation

Not all code deserves equal test investment. Allocate based on risk:

| Code category | Coverage priority | Rationale |
|---------------|-------------------|-----------|
| Payment/billing logic | Very high (branch + mutation) | Bugs cost money directly |
| Auth/authz | Very high | Security impact |
| Core business rules | High | Defines product value |
| Data transformations | High | Silent corruption is hard to detect |
| API contracts | Medium-high | Breaking changes affect consumers |
| Configuration/wiring | Medium | Integration tests cover this |
| UI presentation | Low-medium | Visual review + E2E tests |
| Logging/telemetry | Low | Not user-facing, observable in production |
| One-time scripts/migrations | Low | Run once, verify manually |

## Decision Guide

1. **Measure branch coverage**, not just line coverage
2. **Set contextual thresholds**: 90%+ for core business logic, relaxed for UI/glue
3. **Use coverage diffs on PRs**: ensure new code is tested
4. **Run mutation testing periodically** on high-risk modules
5. **Never chase a number**: ask "what confidence do these tests give me?" instead

## Additional Resources

- [coverage-reference.md](coverage-reference.md) — Extended discussion of coverage tool categories, mutation testing workflows, coverage ratcheting strategies, and organizational coverage policies

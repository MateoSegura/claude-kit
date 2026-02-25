---
name: core-testing:test-philosophy
description: "Test pyramid, testing trophy, cost-benefit analysis, property-based testing, and principles for deciding what to test"
user-invocable: false
---

# Test Philosophy Quick Reference

## The Test Pyramid

```
        /\
       /  \    E2E Tests
      /----\   (few, slow, expensive, high confidence)
     /      \
    /--------\  Integration Tests
   /          \ (moderate count, medium speed)
  /------------\
 /______________\ Unit Tests
                  (many, fast, cheap, focused)
```

**Rationale**: Tests at the bottom are fast, cheap to write, and cheap to maintain. Tests at the top give high confidence but are slow, brittle, and expensive. A healthy suite is bottom-heavy.

**Typical ratios** (guideline, not law):
- Unit: 70%
- Integration: 20%
- E2E: 10%

## When to Bend the Pyramid

The pyramid is a heuristic, not a rule. Bend it when:

- **CRUD-heavy apps**: Integration tests covering request-to-database round trips often catch more bugs per test than unit tests on thin service layers
- **UI-driven products**: A broader middle layer (component/integration) may be more cost-effective than deep unit tests on presentation logic
- **Data pipelines**: End-to-end pipeline tests with snapshot comparisons may outweigh unit tests on individual transforms
- **Glue code**: If a module is mostly wiring dependencies together, integration tests that exercise the wiring are more valuable than unit tests mocking everything

## The Testing Trophy

An alternative model emphasizing integration tests:

```
        /\       E2E
       /--\
      /    \     Integration (widest)
     /------\
    /        \   Unit
   /----------\
  / Static     \
 /--------------\
```

Key insight: **Integration tests give the best return on investment** for many web applications because they test realistic behavior without the brittleness of E2E tests or the over-isolation of unit tests.

## Cost-Benefit Analysis

**Cost of a test:**
- Time to write and understand
- Time to maintain when code changes
- CI wall-clock time
- False-positive investigation time

**Value of a test:**
- Bug prevention (catches regressions)
- Design feedback (hard-to-test code signals design problems)
- Documentation (shows intended behavior)
- Refactoring safety net

**High-value tests** have low maintenance cost and catch real bugs. **Low-value tests** are brittle, test implementation details, and break on every refactor without catching bugs.

## What NOT to Test

- **Language/framework guarantees**: Do not test that your ORM saves data or that the HTTP framework routes correctly — trust the framework's own tests
- **Trivial getters/setters**: No logic, no value in testing
- **Implementation details**: Private methods, internal state, call ordering — test observable behavior instead
- **Third-party library internals**: Test YOUR code's interaction with the library, not the library itself
- **Generated code**: If a code generator is well-tested, do not re-test its output

## Property-Based Testing

Instead of writing specific input-output examples, define **properties** that must hold for any valid input:

```
// Example property: reversing a list twice yields the original list
for any list L:
    reverse(reverse(L)) == L

// Example property: sorting is idempotent
for any list L:
    sort(sort(L)) == sort(L)

// Example property: serialization round-trip
for any object O:
    deserialize(serialize(O)) == O
```

**When property-based testing shines:**
- Serialization/deserialization round trips
- Mathematical properties (commutativity, associativity)
- Encoding/decoding
- Data structure invariants
- Parsers (parse then pretty-print then parse again)

## Testing in Production

Some properties can only be verified in production:

- **Canary deployments**: Route a percentage of traffic to the new version, monitor error rates
- **Feature flags**: Toggle features for specific users, observe behavior
- **Observability**: Structured logs, metrics, and traces that enable fast diagnosis
- **Chaos engineering**: Deliberately inject failures to verify resilience

These complement, not replace, pre-deployment testing.

## Decision Guide

When deciding whether and how to test something, ask:

1. **What is the cost if this breaks?** High cost = more testing
2. **How likely is it to break?** Complex logic = more testing
3. **How fast will I know it broke?** Slow feedback = more pre-deployment tests
4. **Can I test this at a lower level?** Prefer the cheapest test that gives confidence

## Additional Resources

- [philosophy-reference.md](philosophy-reference.md) — Extended discussion of test economics, testing maturity models, organizational testing patterns, and anti-patterns in test strategy

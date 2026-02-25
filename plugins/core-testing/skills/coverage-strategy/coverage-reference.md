# Coverage Strategy — Extended Reference

Detailed reference material covering coverage tool categories, mutation testing workflows, coverage ratcheting, and organizational coverage policies.

## Coverage Tool Categories

### Source-Instrumentation Tools

Insert tracking code at compile/transpile time. Accurate but adds overhead.

```
// Original code
function add(a, b):
    return a + b

// Instrumented code (conceptual)
function add(a, b):
    __coverage__["add:line1"] = true
    return a + b
```

**Characteristics:**
- Precise line/branch/function tracking
- Language-specific (one tool per language)
- Build-time overhead
- Examples: Istanbul/NYC (JavaScript), coverage.py (Python), JaCoCo (Java), gcov (C/C++), llvm-cov (Rust/C++)

### Runtime-Sampling Tools

Sample the program counter at intervals. Low overhead, statistical accuracy.

**Characteristics:**
- Language-agnostic (works at binary level)
- Minimal performance impact
- Statistical, not exact
- Better for production profiling than test coverage

### Binary-Instrumentation Tools

Rewrite the compiled binary to insert tracking.

**Characteristics:**
- No source code changes needed
- Works with any compiled language
- Higher runtime overhead than sampling
- Examples: Valgrind's callgrind, DynamoRIO

## Coverage Metrics Comparison

| Metric | Strength | Weakness | Recommendation |
|--------|----------|----------|----------------|
| Line coverage | Easy to understand, widely supported | A line can execute without being tested | Minimum viable metric |
| Branch coverage | Catches missed conditional paths | Does not cover compound conditions | Preferred default |
| Function coverage | Quick overview of untested functions | Says nothing about internal coverage | Good for triage |
| Path coverage | Most thorough | Combinatorial explosion | Impractical as target |
| MC/DC | Verifies condition independence | Expensive to achieve | Safety-critical only |
| Mutation score | Measures test sensitivity | Slow, expensive | Periodic audits |

## Mutation Testing in Depth

### Workflow

```
1. Run test suite → all pass (baseline)
2. Generate mutants (automated tool modifies source)
3. For each mutant:
   a. Apply mutation to source
   b. Run test suite
   c. If any test FAILS → mutant is KILLED (good)
   d. If all tests PASS → mutant SURVIVED (test gap)
4. Calculate mutation score = killed / total
5. Review surviving mutants → improve tests or mark as equivalent
```

### Mutation Operators

**Arithmetic operators:**
```
a + b  →  a - b
a * b  →  a / b
a % b  →  a * b
```

**Relational operators:**
```
a > b   →  a >= b
a == b  →  a != b
a < b   →  a <= b
```

**Logical operators:**
```
a && b  →  a || b
!a      →  a
a && b  →  true
```

**Statement mutations:**
```
return x    →  return 0
return x    →  return null
doSomething()  →  (removed)
if (cond)   →  if (true)
if (cond)   →  if (false)
```

**Constant mutations:**
```
0  →  1
1  →  0
""  →  "mutant"
true  →  false
```

### Equivalent Mutants

Some mutants produce code that is functionally identical to the original. These cannot be killed and should be excluded from the score.

```
// Original
function max(a, b):
    if a >= b:
        return a
    return b

// Mutant: a > b instead of a >= b
// When a == b, both return a — same result
// This is an equivalent mutant
```

Equivalent mutants are the biggest practical challenge in mutation testing. Most tools flag surviving mutants for human review rather than automatically classifying them.

### Targeting Mutation Testing

Running mutation testing on an entire codebase is prohibitively expensive. Target it strategically:

```
1. Identify high-risk modules (payment, auth, core business rules)
2. Run mutation testing only on those modules
3. Review surviving mutants
4. Add tests for genuine gaps
5. Mark equivalent mutants
6. Repeat periodically (monthly or per release)
```

**Cost estimate**: For a module with 500 lines and 50 mutants, each mutant runs the full test suite. If the suite takes 10 seconds, mutation testing takes ~8 minutes. Scale accordingly.

## Coverage Ratcheting

### Concept

A coverage ratchet prevents coverage from declining. It does not demand a specific target — it only demands that new code does not lower the overall coverage.

```
// CI check pseudocode
previousCoverage = readFromArtifact("coverage-baseline.json")
currentCoverage = runTestsWithCoverage()

if currentCoverage.overall < previousCoverage.overall:
    fail("Coverage decreased from {previous}% to {current}%")

if currentCoverage.overall > previousCoverage.overall:
    updateArtifact("coverage-baseline.json", currentCoverage)
    log("Coverage ratchet increased to {current}%")
```

### Diff Coverage (Preferred)

Instead of ratcheting overall coverage, measure coverage on **changed lines only**:

```
// CI check: new/modified lines must be X% covered
changedLines = git diff --numstat main...HEAD
coveredChangedLines = intersect(changedLines, coveredLines)
diffCoverage = coveredChangedLines / changedLines

if diffCoverage < threshold:
    fail("New/changed code is only {diffCoverage}% covered (minimum: {threshold}%)")
```

**Advantages:**
- Does not penalize old untested code
- Focuses testing effort on new code
- Gradually improves coverage over time
- Avoids "coverage debt" arguments

**Recommended threshold**: 80% diff coverage for new code. Lower (60%) for test infrastructure and configuration files.

### Coverage in Pull Request Reviews

Display coverage information in PRs:

```
PR #123: Add discount calculation
──────────────────────────────────
Overall coverage: 78.3% (+0.2%)
Diff coverage:    92.1% (37/40 new lines covered)

Uncovered new lines:
  src/pricing/discount.py:45-47  (error handling path)
  src/pricing/discount.py:62     (edge case: zero quantity)
```

This gives reviewers actionable information without blocking on arbitrary thresholds.

## Organizational Coverage Policies

### Tiered Coverage Requirements

Different code categories have different coverage expectations:

```
Tier 1 — Critical (90%+ branch coverage required)
├── Payment processing
├── Authentication / authorization
├── Data encryption / decryption
├── Core business rules
└── API contracts (request/response validation)

Tier 2 — Important (75%+ branch coverage)
├── Data access layer
├── Service orchestration
├── Input validation
├── Error handling paths
└── Background job processing

Tier 3 — Standard (60%+ branch coverage)
├── Configuration loading
├── Logging and telemetry
├── Admin/internal tools
└── CLI argument parsing

Tier 4 — Relaxed (no hard requirement)
├── UI layout/styling
├── One-time migration scripts
├── Generated code
├── Development tooling
└── Documentation generators
```

### Coverage Exemptions

Some code should be explicitly excluded from coverage requirements:

```
// Platform-specific code (only runs on specific OS)
// Panic/fatal error handlers (hard to trigger safely)
// Debug-only code (compiled out in release)
// Generated protocol buffer / API client code
// Vendor / third-party code copied into the repo
```

Document exemptions in a `.coveragerc`, `jest.config`, or equivalent file so they are visible and auditable.

### Coverage Trending

Track coverage over time to identify trends:

```
Month    Coverage    Trend    Action
─────    ────────    ─────    ──────
Jan      72.1%       —       Baseline
Feb      71.8%       ↓       Warning: new code untested
Mar      73.2%       ↑       Diff coverage enforced
Apr      74.5%       ↑       Mutation testing started
May      74.3%       →       Stable
Jun      76.1%       ↑       Legacy module retrofit
```

A steady upward trend without heroic effort indicates a healthy testing culture.

## What Coverage Cannot Tell You

### False Sense of Security

```
// 100% line coverage, but the test is worthless:
test "process order":
    order = Order(items: [Item(100)])
    service.processOrder(order)
    // No assertion — just exercises the code
    // Coverage tool says: "line covered!"
```

### Missing Assertions

Coverage tools measure execution, not verification. A line that runs but whose result is never checked provides false confidence.

### Concurrency Issues

Coverage is measured on single-threaded execution paths. Race conditions, deadlocks, and timing bugs are invisible to coverage analysis.

### Configuration and Environment

Code may behave differently with different configurations, feature flags, or environment variables. 100% coverage on one configuration says nothing about other configurations.

### Error Handling Quality

A covered error handler is not necessarily a correct error handler. Coverage confirms the handler runs; it does not confirm it does the right thing.

## Coverage Anti-Patterns

### The Coverage Game

Developers write assertion-free tests to hit the coverage target:

```
// BAD: covers the code, tests nothing
test "covers all branches":
    try:
        service.process(null)
    catch:
        pass  // Swallow exception, line "covered"

    try:
        service.process(validInput)
    catch:
        pass  // Swallow exception, line "covered"
```

**Fix**: Require meaningful assertions. Code review should flag tests without assertions.

### Coverage Theater

Team celebrates hitting 90% coverage while production has frequent bugs. Coverage is high, but tests are low quality.

**Fix**: Supplement coverage with mutation testing scores on critical paths.

### Coverage Guilt

Developers avoid refactoring because it would temporarily drop coverage. Old, poorly-tested code stays untouched.

**Fix**: Use diff coverage (only measure new/changed lines). Allow temporary overall drops during large refactors with a plan to recover.

### One-Size-Fits-All Threshold

Same coverage requirement for all code regardless of risk. Payment logic and logging configuration have the same bar.

**Fix**: Tiered requirements based on risk (see Tiered Coverage Requirements above).

# testing/ — Test Documentation

**Governing Process:** PROC-LC-005 (Integration & Testing)

Test documentation captures evidence of verification and regression analysis.
Test evidence validates that specs were implemented correctly. Regression
documents capture root causes and fixes for issues discovered in production.

## Subdirectories

| Directory | Contents |
|-----------|----------|
| `evidence/` | Test evidence records (TEST-XXX) |
| `regression/` | Regression analysis records (REG-XXX) |

## Test Evidence Convention

- Prefix: `TEST-XXX` (zero-padded three digits)
- Filename: `TEST-XXX-<short-description>.md`
- Example: `TEST-001-v0.11-release.md`

### Test Evidence Template

```markdown
# TEST-XXX: <Title>

**Status:** pass | fail | partial
**Date:** YYYY-MM-DD
**Version:** vX.Y.Z

## Scope

What was tested and what was explicitly excluded.

## Results

Summary of test outcomes.

## Evidence

Relevant logs, screenshots, or command output demonstrating results.

## Traces

- **From:** SPEC-XXX (the spec this testing validates)
- **To:** REG-XXX (any regressions discovered during this test cycle)
```

## Regression Convention

- Prefix: `REG-XXX` (zero-padded three digits)
- Filename: `REG-XXX-<short-description>.md`
- Example: `REG-001-install-credential-fix.md`

### Regression Template

```markdown
# REG-XXX: <Title>

**Status:** open | fixed | wont-fix
**Severity:** critical | high | medium | low
**Date:** YYYY-MM-DD

## Symptom

What was observed.

## Root Cause

Why it happened.

## Fix

What was done to resolve it.

## Prevention

How to prevent recurrence.

## Traces

- **From:** TEST-XXX (test cycle that discovered this)
- **To:** REQ-XXX or SPEC-XXX (if a new requirement or spec was created)
```

## Valid Status Values

| Document Type | Valid Statuses |
|---------------|---------------|
| TEST-XXX | `pass`, `fail`, `partial` |
| REG-XXX | `open`, `fixed`, `wont-fix` |

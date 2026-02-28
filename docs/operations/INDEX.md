# operations/ — Operational Documentation

**Governing Process:** PROC-LC-007 (Deployment & Operations)

Operations documentation covers incidents, runbooks, and migration guides.
These are cross-cutting — they can reference any other documentation layer.

## Subdirectories

| Directory | Contents |
|-----------|----------|
| `incidents/` | Post-incident reports (INC-XXX) |
| `runbooks/` | Operational procedures (RB-XXX) |
| `migration/` | Version migration guides (MIG-XXX) |

## Incident Convention

- Prefix: `INC-XXX` (zero-padded three digits)
- Filename: `INC-XXX-<short-description>.md`
- Example: `INC-001-encryption-key-rotation.md`

### Incident Template

```markdown
# INC-XXX: <Title>

**Status:** investigating | resolved | post-mortem-complete
**Severity:** critical | high | medium | low
**Date:** YYYY-MM-DD

## Timeline

Chronological sequence of events.

## Impact

What was affected and for how long.

## Root Cause

Why it happened.

## Resolution

What was done to resolve it.

## Action Items

- [ ] Preventive measure 1
- [ ] Preventive measure 2

## Traces

- **From:** (what triggered the investigation)
- **To:** REG-XXX, RB-XXX (regressions filed, runbooks created/updated)
```

## Runbook Convention

- Prefix: `RB-XXX` (zero-padded three digits)
- Filename: `RB-XXX-<short-description>.md`
- Example: `RB-001-release-process.md`

### Runbook Template

```markdown
# RB-XXX: <Title>

**Status:** active | deprecated | superseded-by RB-YYY
**Last Verified:** YYYY-MM-DD

## Purpose

When to use this runbook.

## Prerequisites

What must be true before starting.

## Steps

1. Step one
2. Step two
3. ...

## Rollback

How to undo if something goes wrong.

## Traces

- **From:** INC-XXX (incident that motivated this runbook)
- **To:** (related documents)
```

## Migration Convention

- Prefix: `MIG-XXX` (zero-padded three digits)
- Filename: `MIG-XXX-<short-description>.md`
- Example: `MIG-001-v010-to-v011.md`

### Migration Template

```markdown
# MIG-XXX: <Title>

**Status:** draft | active | completed
**From Version:** vX.Y.Z
**To Version:** vA.B.C

## Breaking Changes

What changed that requires migration.

## Migration Steps

1. Step one
2. Step two
3. ...

## Verification

How to confirm migration was successful.

## Rollback

How to revert if the migration fails.

## Traces

- **From:** ADR-XXX (decision that introduced the breaking change)
- **To:** TEST-XXX (test evidence for the migration)
```

## Valid Status Values

| Document Type | Valid Statuses |
|---------------|---------------|
| INC-XXX | `investigating`, `resolved`, `post-mortem-complete` |
| RB-XXX | `active`, `deprecated`, `superseded-by RB-YYY` |
| MIG-XXX | `draft`, `active`, `completed` |

# plans/ — Implementation Plans

Plans describe **how** and **when** a set of requirements and architecture
decisions will be implemented. Each plan is version-scoped and tracks its own
status through completion.

## ID Convention

- Prefix: `PLAN-XXX` (zero-padded three digits)
- Filename: `PLAN-XXX-<short-description>.md`
- Example: `PLAN-001-session-logging.md`

## Document Template

```markdown
# PLAN-XXX: <Title>

**Status:** draft | active | completed | abandoned
**Target Version:** vX.Y.Z
**Created:** YYYY-MM-DD

## Objective

What this plan delivers and why it matters.

## Scope

What is included and explicitly excluded.

## Implementation Steps

1. Step one — description
2. Step two — description
3. ...

## Verification

How to confirm the plan was successfully implemented.

## Traces

- **From:** REQ-XXX, ADR-XXX (requirements and decisions this plan implements)
- **To:** TEST-XXX (test evidence validating the implementation)
```

## Valid Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Under development, not yet committed to |
| `active` | Approved and in progress |
| `completed` | Fully implemented and verified |
| `abandoned` | Cancelled before completion |

# specs/ — Implementation Specs

Specs describe **how** and **when** a set of requirements and architecture
decisions will be implemented. Each spec is version-scoped and tracks its own
status through completion.

This directory also contains spec-driven development workspaces (created by
`/spec:new`) which use a directory-based structure with `overview.md`, phase
files, and status tracking.

## ID Convention

- Prefix: `SPEC-XXX` (zero-padded three digits)
- Filename: `SPEC-XXX-<short-description>.md`
- Example: `SPEC-001-session-logging.md`

## Document Template

```markdown
# SPEC-XXX: <Title>

**Status:** draft | active | completed | abandoned
**Target Version:** vX.Y.Z
**Created:** YYYY-MM-DD

## Objective

What this spec delivers and why it matters.

## Scope

What is included and explicitly excluded.

## Implementation Steps

1. Step one — description
2. Step two — description
3. ...

## Verification

How to confirm the spec was successfully implemented.

## Traces

- **From:** REQ-XXX, ADR-XXX (requirements and decisions this spec implements)
- **To:** TEST-XXX (test evidence validating the implementation)
```

## Valid Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Under development, not yet committed to |
| `active` | Approved and in progress |
| `completed` | Fully implemented and verified |
| `abandoned` | Cancelled before completion |

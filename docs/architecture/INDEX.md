# architecture/ — Architecture Documentation

**Governing Process:** PROC-LC-003 (Architecture Design)

Architecture documentation captures **decisions** (ADRs) and **component
descriptions**. Decisions are immutable once accepted — if circumstances change,
supersede with a new ADR rather than editing the original.

## Subdirectories

| Directory | Contents |
|-----------|----------|
| `decisions/` | Architecture Decision Records (ADR-XXX) |
| `components/` | Component documentation (free-form, no ID prefix) |

## ADR Convention

- Prefix: `ADR-XXX` (zero-padded three digits)
- Filename: `ADR-XXX-<short-description>.md`
- Example: `ADR-001-single-file-cli.md`

### ADR Template

```markdown
# ADR-XXX: <Title>

**Status:** proposed | accepted | superseded-by ADR-YYY | rejected
**Date:** YYYY-MM-DD

## Context

What situation or requirement prompted this decision?

## Decision

What was decided and why.

## Consequences

What follows from this decision — both positive and negative.

## Traces

- **From:** REQ-XXX (the requirement this decision addresses)
- **To:** SPEC-XXX, component docs (downstream implementations)
```

### Immutability Rule

**Never edit an accepted ADR.** If a decision needs to change:

1. Create a new ADR (next sequential ID)
2. Set the new ADR's context to explain why the original is being revisited
3. Update the original ADR's status to `superseded-by ADR-YYY`
4. The status update is the **only** permitted edit to an accepted ADR

## Component Documentation

Component docs in `components/` describe subsystems in detail (internal
structure, APIs, data flows). They are free-form and do not use ID prefixes.
Name them descriptively: `cli-architecture.md`, `plugin-loader.md`, etc.

## Valid Status Values

| Status | Meaning |
|--------|---------|
| `proposed` | Under discussion |
| `accepted` | Decided and in effect |
| `superseded-by ADR-YYY` | Replaced by a newer decision |
| `rejected` | Considered but not adopted |

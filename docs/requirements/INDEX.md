# requirements/ — System Requirements

**Governing Process:** PROC-LC-002 (Requirements Engineering)

Requirements define **what** the system must do and **why**. Each requirement
traces upstream to research or stakeholder needs and downstream to architecture
decisions and implementation specs.

## ID Convention

- Prefix: `REQ-XXX` (zero-padded three digits)
- Filename: `REQ-XXX-<short-description>.md`
- Example: `REQ-001-plugin-encryption.md`

## Document Template

```markdown
# REQ-XXX: <Title>

**Status:** draft | active | deprecated | superseded-by REQ-YYY
**Priority:** must-have | should-have | nice-to-have
**Created:** YYYY-MM-DD
**Governing Process:** PROC-LC-002 (Requirements Engineering)

## Context

Why this requirement exists. Link to research papers or stakeholder needs.

## Requirement

Clear, testable statement of what the system must do.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Traces

- **Upstream:** <research paper or stakeholder need>
- **Downstream:** ADR-XXX, SPEC-XXX (downstream documents that implement this)
- **Quality Attributes:** <QA-XXX references or "None identified">
```

## Valid Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Under discussion, not yet committed to |
| `active` | Accepted and drives implementation |
| `deprecated` | No longer relevant |
| `superseded-by REQ-YYY` | Replaced by a newer requirement |

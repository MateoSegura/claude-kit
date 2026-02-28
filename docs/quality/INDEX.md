# quality/ — Quality Attributes and Architectural Constraints

**Governing Process:** PROC-SP-002 (Quality Assurance)

Quality attribute documents (QA-XXX) describe HOW the product must behave to be
sellable in its target markets. Unlike requirements (REQ-XXX) which define what
the product delivers, constraints define the external rules, certifications, and
architectural boundaries that the product must satisfy.

## Scope

claude-kit serves defense contractors, federal agencies, and enterprises that
handle Controlled Unclassified Information (CUI), ITAR-controlled data, and
classified-adjacent workloads. These markets impose compliance, regulatory, and
deployment constraints that fundamentally shape the product architecture.

## Document Format

Each QA document is an actionable playbook:

```markdown
# QA-XXX — <Title>

**Status:** draft | active | deferred | deprecated
**Priority:** must | should | could
**Category:** compliance | ai-regulation | deployment | business | insurance

## Context

Why this constraint exists and who imposes it.

## Constraint

What the product must satisfy, with specific control numbers and standards.

## Architectural Impact

How this constraint shapes the product's design and deployment model.

## Phased Approach

Ordered steps to satisfy the constraint, with cost and timeline estimates.

## Artifacts Required

Documents, certifications, and evidence the organization must produce.

## Traces

- From: REQ-XXX, research papers, or external standards
- To: ADR-XXX, SPEC-XXX, or future implementation work
```

## Document Inventory

| ID | Title | Category | Priority | Status |
|----|-------|----------|----------|--------|
| QA-001 | SOC 2 Certification | compliance | must | draft |
| QA-002 | FedRAMP Authorization | compliance | should | draft |
| QA-003 | Defense Contractor Compliance | compliance | must | draft |
| QA-004 | Export Control | compliance | must | draft |
| QA-005 | DoD Cloud Impact Levels | compliance | could | draft |
| QA-006 | Supply Chain Security | compliance | must | draft |
| QA-007 | AI Regulatory Compliance | ai-regulation | must | draft |
| QA-008 | Dual Deployment Architecture | deployment | must | draft |
| QA-009 | Vendor Risk and Incident Response | business | should | draft |
| QA-010 | IP Ownership of AI-Generated Code | business | should | draft |
| QA-011 | Accessibility | compliance | should | draft |
| QA-012 | Insurance and Escrow | insurance | should | draft |

## Relationship to Other Layers

Quality attributes trace upstream to requirements (the product capabilities they
constrain) and downstream to architecture decisions and specs (the design
choices they force).

```
requirements/ ──→ quality/ ──→ architecture/decisions/
     ↑                                 ↓
  research/                         specs/
```

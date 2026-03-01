# QA-005 — DoD Cloud Impact Levels

**Status:** draft
**Priority:** could
**Category:** compliance
**Governing Process:** PROC-SP-002 (Quality Assurance)

## Context

The DoD Cloud Computing Security Requirements Guide (CC SRG) defines Impact
Levels (ILs) that classify information systems by data sensitivity. Each level
adds controls on top of FedRAMP baselines. If claude-kit's SaaS offering
(REQ-009) ever needs to serve DoD directly (not through a contractor's on-prem
deployment), IL4 or IL5 authorization is required on top of FedRAMP.

The on-prem deployment model sidesteps this entirely — the customer's
environment already has its own IL authorization, and claude-kit operates within
their boundary. This constraint is prioritized "could" because on-prem covers
the immediate DoD market; direct DoD SaaS is a future expansion.

## Constraint

| Impact Level | Data Types | FedRAMP Baseline | Additional Controls | Access Restriction |
|-------------|------------|-----------------|---------------------|-------------------|
| **IL2** | Public, non-CUI | FedRAMP Moderate | Minimal | Open to non-U.S. providers |
| **IL4** | CUI, mission data | FedRAMP Moderate + 38 | NIPRNet connectivity | U.S. persons only |
| **IL5** | Higher-sensitivity CUI, NSS (unclassified) | FedRAMP Moderate + 47 | 421+ total controls, dedicated infrastructure | U.S. citizens only |
| **IL6** | Classified up to SECRET | Separate infrastructure | Completely isolated | Cleared U.S. citizens only |

### Key Technical Requirements at IL4+

1. **U.S. persons access restriction** — at IL4, all data must be accessible
   only to U.S. persons; at IL5, only U.S. citizens. This affects the
   engineering team, support staff, SRE, and DevOps.
2. **Dedicated infrastructure** — IL5 requires dedicated physical or virtual
   infrastructure, not shared multi-tenant.
3. **NIPRNet connectivity** — IL4+ may require connectivity to the Non-classified
   Internet Protocol Router Network.
4. **DoD-specific incident reporting** — more stringent than standard FedRAMP
   continuous monitoring.

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| U.S. persons / citizens only | Engineering hiring, support staffing, and SRE must be restricted. No offshore contractors for IL4/5 infrastructure. |
| Dedicated infrastructure | Cannot use shared multi-tenant for IL5; must architect for single-tenant deployment option in SaaS model. |
| NIPRNet connectivity | Network architecture must support DoD network interconnection, which requires additional ISAs (Interconnection Security Agreements). |
| 421+ controls | Every FedRAMP control plus DoD-specific additions; significantly more evidence and documentation than FedRAMP alone. |

## Phased Approach

### Prerequisite: FedRAMP Moderate (see QA-002)

IL4/IL5 authorization is built ON TOP of FedRAMP. FedRAMP must be obtained first.

### Phase 1: IL Assessment (months 1–3 after FedRAMP)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Engage DoD-experienced assessor for IL gap analysis | Month 1 | $25K–$50K |
| Determine target IL (IL4 vs IL5) based on customer needs | Month 1 | — |
| Identify additional controls beyond FedRAMP baseline | Month 2–3 | Included in assessment |

### Phase 2: Implementation (months 3–9 after FedRAMP)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Deploy dedicated infrastructure in authorized cloud region | Month 3–5 | $50K–$150K/year infrastructure |
| Implement additional DoD-specific controls | Month 4–8 | Engineering effort |
| Obtain provisional authorization from DoD sponsoring agency | Month 8–9 | $100K–$200K (assessment) |

### Phase 3: Ongoing (continuous)

| Step | Frequency | Cost Estimate |
|------|-----------|---------------|
| DoD-specific continuous monitoring | Monthly | Included in FedRAMP ConMon |
| Annual reassessment | Annual | $50K–$100K |

**Estimated total (on top of FedRAMP): $175K–$400K + dedicated infrastructure
costs.**

## Artifacts Required

All FedRAMP artifacts (see QA-002) plus:

| Artifact | Purpose |
|----------|---------|
| DoD CC SRG compliance matrix | Maps controls to DoD-specific requirements |
| Interconnection Security Agreement (ISA) | For NIPRNet connectivity |
| U.S. person/citizen verification records | Proves access restrictions |
| Dedicated infrastructure documentation | Architecture diagrams for isolated deployment |

## Traces

- **Upstream:** QA-002 (FedRAMP — prerequisite authorization), REQ-009 (Cloud
  Platform — the SaaS offering)
- **Downstream:** Future SPEC for DoD-dedicated infrastructure deployment
- **Standards:** DoD CC SRG, NIST SP 800-53 Rev 5

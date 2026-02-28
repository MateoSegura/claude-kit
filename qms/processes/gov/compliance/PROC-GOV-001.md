# PROC-GOV-001: CMMC Compliance

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Ensure that claude-kit and its cloud platform satisfy CMMC 2.0 requirements at the level required by the organization's Defense Industrial Base (DIB) contracts. This process maps existing security controls to CMMC practices, identifies gaps, and drives remediation to achieve certification readiness before C3PAO assessment.

## 2. Scope

This process covers CMMC Level 1 (Foundational) and Level 2 (Advanced) compliance for all claude-kit components that handle, store, or transmit Federal Contract Information (FCI) or Controlled Unclassified Information (CUI). Level 3 (Expert) is excluded pending future DoD contract requirements.

Included:
- Cloud platform infrastructure (REQ-009)
- Plugin distribution pipeline (encryption, signing, delivery)
- Air-gapped deployment configurations
- AI agent execution environments
- Developer workstations that access CUI-scoped projects

Excluded:
- Customer environments beyond the shared responsibility boundary
- Anthropic model training infrastructure (covered by vendor risk assessment)

## 3. Entry Criteria

- [ ] PROC-SP-002 (Quality Assurance) base process is established and operational
- [ ] PROC-SEC-001 through PROC-SEC-005 (Security processes) are established
- [ ] Organization has at least one active or pending DoD contract requiring CMMC
- [ ] Executive sponsor designated for CMMC compliance program
- [ ] CUI boundary and data flow diagrams are documented
- [ ] Current security posture baseline assessment is complete

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| NIST SP 800-171 Rev 2 control catalog | NIST | PDF / structured data |
| CMMC 2.0 Model Assessment Guide (Level 2) | DoD CIO | PDF |
| Current security control inventory | PROC-SEC-001 | Spreadsheet / GRC tool |
| System Security Plan (SSP) | Security team | Markdown / document |
| Network and data flow diagrams | Architecture team | Diagrams (draw.io, Mermaid) |
| Contract DFARS clauses | Contracts team | Contract excerpts |
| QA-003 (Defense Contractor Compliance) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 CMMC Level Determination

Review all active and pending DoD contracts for DFARS 252.204-7012, 7019, 7020, and 7021 clauses. Determine the required CMMC level based on whether FCI only (Level 1) or CUI (Level 2) is involved. Document the determination with contract references and route for legal review.

### 5.2 Control Mapping

Map each CMMC practice to existing organizational controls from PROC-SEC-001 through PROC-SEC-005. Use the NIST 800-171 to CMMC crosswalk published by the DoD. Record mappings in the GRC tool or compliance tracking spreadsheet, noting which controls are fully implemented, partially implemented, or missing.

### 5.3 Gap Analysis

For each CMMC practice not fully satisfied, document:
- The specific practice ID (e.g., AC.L2-3.1.1)
- Current implementation status (not implemented, partially implemented)
- Technical and procedural gaps
- Estimated remediation effort (hours, cost, dependencies)
- Risk rating if the gap remains open

Produce a formal gap analysis report prioritized by risk.

### 5.4 Plan of Action and Milestones (POA&M)

Create a POA&M for all identified gaps. Each entry must include:
- Weakness description and associated CMMC practice
- Scheduled remediation date
- Responsible party
- Milestones with measurable completion criteria
- Resources required (budget, personnel, tools)

Track POA&M items weekly during active remediation phases.

### 5.5 Remediation Execution

Implement control changes according to the POA&M. Each remediation must:
- Be tracked in a ticketing system with traceability to the POA&M item
- Include evidence of implementation (configuration screenshots, policy documents, test results)
- Be validated by an independent reviewer (not the implementer)
- Update the SSP to reflect the new or modified control

### 5.6 Self-Assessment

Conduct a formal self-assessment against the CMMC Assessment Guide before engaging a C3PAO. Use the DoD scoring methodology (110 points for Level 2) and submit the score to SPRS (Supplier Performance Risk System). Address any practices scoring below MET before scheduling the external assessment.

### 5.7 C3PAO Assessment Preparation

Prepare for the Certified Third-Party Assessment Organization (C3PAO) assessment:
- Assemble all evidence artifacts organized by CMMC domain
- Conduct tabletop walkthroughs with control owners
- Prepare system demonstrations for technical controls
- Brief all interview participants on assessment protocol
- Designate an assessment coordinator as the single point of contact

### 5.8 Assessment Execution and Remediation

Support the C3PAO during the on-site or virtual assessment. If preliminary findings identify deficiencies:
- Evaluate whether in-assessment remediation is feasible (within the assessment window)
- Document corrective actions with evidence for each finding
- If POA&M items are accepted by the assessor, establish firm remediation timelines

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| CMMC Level Determination Memo | `qms/artifacts/gov/` | — | GOV-DET-XXX |
| Gap Analysis Report | `qms/artifacts/gov/` | — | GOV-GAP-XXX |
| Plan of Action and Milestones | `qms/artifacts/gov/` | — | GOV-POAM-XXX |
| Self-Assessment Score | `qms/artifacts/gov/` | — | GOV-SPRS-XXX |
| Assessment Evidence Package | `qms/artifacts/gov/` | — | GOV-EVID-XXX |
| Updated System Security Plan | `qms/artifacts/gov/` | — | GOV-SSP-XXX |

## 7. Exit Criteria

- [ ] All 110 CMMC Level 2 practices are scored MET or have approved POA&M items
- [ ] SPRS score is submitted and current
- [ ] C3PAO assessment is complete with a passing certification recommendation
- [ ] All assessment findings are either remediated or on an approved POA&M
- [ ] SSP is updated to reflect the assessed system boundary
- [ ] Certification status is communicated to contracts and business development teams

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Level determination review | Legal and security lead joint review | Written concurrence on required CMMC level |
| Gap analysis completeness | Cross-reference with CMMC practice list | 100% of practices evaluated and scored |
| POA&M approval | Executive sponsor sign-off | All items have owners, dates, and milestones |
| Self-assessment threshold | SPRS scoring methodology | Score >= 110 for Level 2 (all MET) or documented POA&M for gaps |
| Evidence package review | Internal mock assessment team | All evidence artifacts present, current, and traceable |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns the CMMC compliance program, conducts gap analysis, coordinates assessment |
| Compliance Officer | Maintains POA&M, tracks remediation, manages evidence collection |
| Engineering Lead | Implements technical controls, provides system demonstrations |
| Legal Counsel | Reviews contract requirements, validates CMMC level determination |
| Executive Sponsor | Approves budget, resolves escalations, signs self-assessment |
| Assessment Coordinator | Single point of contact for C3PAO, schedules interviews, manages logistics |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| CMMC practice coverage | Percentage of practices scored MET | 100% at target level | GRC tool / spreadsheet |
| POA&M aging | Average age of open POA&M items | < 90 days | Weekly POA&M review |
| Remediation velocity | POA&M items closed per month | >= 10/month during active remediation | Ticketing system |
| SPRS score | Submitted self-assessment score | 110 (Level 2) | SPRS portal |
| Time to certification | Months from program start to C3PAO pass | <= 12 months | Project timeline |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| CMMC 2.0 Level 2 | All 14 domains, 110 practices | Primary certification target |
| NIST SP 800-171 Rev 2 | All 14 control families, 110 controls | Technical control baseline (CMMC L2 = 800-171) |
| DFARS 252.204-7012 | Safeguarding Covered Defense Information | Contract clause requiring CUI protection |
| DFARS 252.204-7021 | CMMC Requirements | Contract clause mandating CMMC certification |
| 32 CFR Part 170 | CMMC Program Rule | Final rule establishing CMMC framework |

## 12. Tailoring Guidance

**Level 1 only (FCI, no CUI):**
- Skip Activities 5.3 through 5.6 for practices beyond the 17 Level 1 requirements
- Self-assessment is sufficient — no C3PAO required
- Annual self-assessment and affirmation in SPRS replaces external audit
- POA&M scope reduced to 17 practices

**Level 2 with low CUI volume:**
- Minimize the CUI boundary by isolating CUI-handling components
- Focus gap analysis on the boundary systems rather than the full enterprise
- Consider a phased approach: certify the smallest viable scope first, expand later

**Level 2 full scope:**
- Execute all activities as written
- Plan for 6–12 months of preparation before engaging a C3PAO
- Budget for potential reassessment if significant findings emerge

**Air-gapped deployments (QA-008):**
- Additional controls for media transfer and physical security
- Coordinate with PROC-GOV-011 (Air-Gap Deployment) for offline-specific practices
- Document air-gap boundary in the SSP as a separate authorization boundary

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SP-002 | Extends — CMMC compliance builds on the base QA process |
| PROC-SEC-001 | Extends — leverages security controls as CMMC evidence |
| PROC-SEC-002 | Extends — vulnerability management maps to CMMC RA/CA domains |
| PROC-SEC-003 | Extends — incident response maps to CMMC IR domain |
| PROC-SEC-004 | Extends — access control maps to CMMC AC domain |
| PROC-SEC-005 | Extends — encryption maps to CMMC SC domain |
| PROC-GOV-006 | Depends on — CUI handling is prerequisite for CMMC Level 2 |
| PROC-GOV-008 | Feeds into — audit readiness process prepares for C3PAO |
| PROC-GOV-009 | Feeds into — evidence collection provides assessment artifacts |
| PROC-GOV-013 | Related — customer boundary integration affects CMMC scope |

## 14. Traces

- **Governs:** CMMC certification artifacts, SPRS submissions, POA&M records
- **Enforced by:** Quarterly self-assessment reviews, annual C3PAO reassessment cycle
- **Related QA:** QA-003 (Defense Contractor Compliance)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

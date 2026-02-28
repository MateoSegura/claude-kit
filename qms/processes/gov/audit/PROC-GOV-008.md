# PROC-GOV-008: Audit Readiness

**Version:** 1.0.0
**Status:** draft
**Category:** audit
**Layer:** gov
**Maturity:** initial
**Owner:** Compliance Officer
**Last Reviewed:** 2026-02-28

## 1. Purpose

Prepare the organization for successful completion of external audits and assessments across multiple compliance frameworks (SOC 2, FedRAMP, CMMC). Audit readiness is a continuous discipline, not a last-minute effort. This process ensures that evidence is current, control owners are prepared, and gaps are identified and remediated before assessors arrive.

## 2. Scope

This process covers audit preparation for:
- SOC 2 Type I and Type II audits (CPA firm)
- FedRAMP 3PAO assessments (initial and annual)
- CMMC C3PAO assessments (Level 1 and Level 2)
- Customer-initiated security assessments and questionnaires
- Internal audit and management review cycles

Included:
- Evidence inventory and gap analysis
- Mock assessments and tabletop exercises
- Assessor coordination and logistics
- Finding remediation tracking

Excluded:
- The audit execution itself (that is the assessor's responsibility)
- Defining the controls (covered by framework-specific processes: PROC-GOV-001, 002)

## 3. Entry Criteria

- [ ] PROC-SP-002 (Quality Assurance) base process is established
- [ ] At least one compliance framework target is identified (SOC 2, FedRAMP, or CMMC)
- [ ] Control owners are designated for all in-scope controls
- [ ] GRC tool or compliance tracking system is operational
- [ ] Budget allocated for external assessment engagement

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Control catalog (framework-specific) | PROC-GOV-001, 002 | GRC tool / spreadsheet |
| Evidence collection inventory | PROC-GOV-009 | Evidence register |
| Previous audit findings (if any) | Prior audit reports | PDF |
| POA&M items | PROC-GOV-001, 002 | POA&M register |
| QA-001 (SOC 2 Certification) | docs/quality/ | Markdown |
| QA-002 (FedRAMP Authorization) | docs/quality/ | Markdown |
| QA-003 (Defense Contractor Compliance) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 Evidence Inventory

Maintain a comprehensive inventory of all evidence artifacts required for each compliance framework:

| Evidence Type | Example | Framework(s) | Collection Method | Refresh Cadence |
|---------------|---------|--------------|-------------------|-----------------|
| Access control logs | IAM audit trail | SOC 2, FedRAMP, CMMC | Automated export | Continuous |
| Vulnerability scan results | Nessus/Qualys reports | SOC 2, FedRAMP, CMMC | Automated scan | Monthly |
| Change management records | PR merge history, deployment logs | SOC 2, FedRAMP | Git + CI/CD logs | Continuous |
| Incident response records | IR tickets and post-mortems | SOC 2, FedRAMP, CMMC | Ticketing system | Per incident |
| Training completion records | Security awareness certificates | SOC 2, FedRAMP, CMMC | LMS export | Quarterly |
| Configuration baselines | Infrastructure-as-code snapshots | FedRAMP, CMMC | Git repository | Per change |
| Encryption verification | Certificate inventory, key rotation logs | SOC 2, FedRAMP, CMMC | Certificate manager | Quarterly |

Map each evidence item to the specific control(s) it satisfies. Identify items that serve multiple frameworks to avoid duplicate collection.

### 5.2 Gap Analysis

Quarterly, conduct a gap analysis comparing the evidence inventory against framework requirements:

1. For each in-scope control, verify that evidence exists and is current
2. Identify controls with missing, stale, or insufficient evidence
3. Categorize gaps by severity:
   - Critical: No evidence exists for a required control
   - High: Evidence is stale (older than the collection cadence)
   - Medium: Evidence exists but does not fully demonstrate control effectiveness
   - Low: Evidence format or labeling does not meet assessor expectations
4. Produce a gap report with remediation priorities and deadlines
5. Track gaps to closure in the POA&M or a dedicated readiness tracker

### 5.3 Mock Assessment

Conduct an internal mock assessment 60–90 days before any scheduled external assessment:

**Preparation:**
- Assign a mock assessment lead (ideally someone not responsible for the controls being tested)
- Use the assessor's methodology (SOC 2 trust criteria, FedRAMP test procedures, CMMC assessment guide)
- Prepare a sample request list mirroring what the assessor will ask for

**Execution:**
- Review evidence artifacts as the assessor would
- Interview control owners using standardized questions
- Test technical controls (attempt access violations, verify logging, check encryption)
- Document findings using the same format as an external assessment

**Remediation:**
- Treat mock findings as real findings
- Remediate all critical and high findings before the external assessment
- Track medium and low findings for improvement

### 5.4 Assessor Coordination

Manage the logistical and administrative aspects of external assessments:

**Pre-assessment:**
- Schedule assessment windows that avoid major releases or infrastructure changes
- Provide assessor with read-ahead materials (SSP, architecture diagrams, prior reports)
- Set up assessor accounts with minimum necessary access
- Reserve conference rooms or virtual meeting links for interviews
- Brief control owners on the assessment schedule and their interview slots

**During assessment:**
- Designate a single point of contact (assessment coordinator)
- Maintain a shared tracker for document requests and responses
- Stage-manage evidence delivery — provide organized, labeled evidence packages
- Escalate blockers immediately (e.g., a control owner unavailable)

**Post-assessment:**
- Review draft findings before the final report
- Submit remediation evidence for any findings addressed during the assessment window
- Document lessons learned for future assessments

### 5.5 Finding Remediation Tracking

Maintain a unified tracker for all audit findings across frameworks:

| Finding ID | Framework | Severity | Control | Description | Owner | Due Date | Status |
|------------|-----------|----------|---------|-------------|-------|----------|--------|
| SOC2-F001 | SOC 2 | Medium | CC6.1 | MFA not enforced for service accounts | DevOps | 2026-04-15 | In Progress |

Track findings through remediation lifecycle: Open → In Progress → Remediated → Verified → Closed.

Report finding status monthly to leadership. Unresolved findings beyond their due date require escalation to the CISO.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Evidence Inventory Register | `qms/artifacts/gov/` | — | GOV-EIR-XXX |
| Gap Analysis Report | `qms/artifacts/gov/` | — | GOV-GAP-XXX |
| Mock Assessment Report | `qms/artifacts/gov/` | — | GOV-MOCK-XXX |
| Assessment Coordination Plan | `qms/artifacts/gov/` | — | GOV-ACP-XXX |
| Finding Remediation Tracker | `qms/artifacts/gov/` | — | GOV-FRT-XXX |

## 7. Exit Criteria

- [ ] Evidence inventory is complete and all items are current
- [ ] Gap analysis shows zero critical and zero high gaps
- [ ] Mock assessment is complete and all critical findings are remediated
- [ ] Assessor is engaged and assessment is scheduled
- [ ] Control owners are briefed and prepared for interviews
- [ ] Finding remediation tracker is active with no overdue items

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Evidence completeness | Inventory audit against control catalog | 100% of controls have mapped evidence |
| Evidence currency | Date check on all evidence artifacts | All evidence within collection cadence |
| Mock assessment readiness | Pre-mock checklist review | All preparation steps complete |
| Mock finding resolution | Remediation verification | Zero critical/high mock findings open |
| Assessor readiness | Pre-assessment checklist | All logistics confirmed, access provisioned |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Compliance Officer | Owns audit readiness program, maintains evidence inventory, coordinates assessors |
| Security Lead | Conducts gap analysis, leads mock assessments, verifies technical evidence |
| Control Owners (various) | Maintain evidence for their controls, participate in interviews |
| Assessment Coordinator | Manages assessment logistics, serves as assessor point of contact |
| CISO | Reviews readiness status, approves assessment engagement, escalation point |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Evidence coverage | Controls with current evidence | 100% | Evidence inventory audit |
| Gap count by severity | Open gaps from quarterly analysis | 0 critical, 0 high | Gap analysis report |
| Mock-to-real finding ratio | Mock findings that recur in real assessment | < 10% | Finding comparison |
| Assessment cycle time | Days from assessment start to final report | < 30 days | Assessment timeline |
| Finding closure rate | Findings closed within due date | >= 90% | Remediation tracker |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| AICPA TSC 2017 | CC4.1, CC4.2 (Monitoring Activities) | SOC 2 audit preparation |
| NIST SP 800-53 Rev 5 | CA-2 (Security Assessments), CA-7 (Continuous Monitoring) | FedRAMP assessment readiness |
| CMMC Assessment Guide | All assessment objectives | CMMC C3PAO preparation |
| ISO 19011:2018 | Clause 5 (Managing an Audit Programme) | Audit management best practices |
| ISACA COBIT 2019 | MEA02 (Monitor Internal Controls) | Control monitoring framework |

## 12. Tailoring Guidance

**Single framework (SOC 2 only):**
- Evidence inventory scoped to Trust Services Criteria only
- Gap analysis quarterly is sufficient
- Mock assessment 90 days before Type II observation period ends
- Assessor coordination for one CPA firm engagement

**Multi-framework (SOC 2 + FedRAMP + CMMC):**
- Unified evidence inventory with framework cross-references
- Gap analysis monthly during first year, quarterly once stable
- Stagger mock assessments: one per quarter for different frameworks
- Consider a GRC tool (Vanta, Drata) to automate evidence collection across frameworks

**Continuous audit readiness (mature organization):**
- Real-time evidence collection dashboards
- Automated gap detection with alerting
- Rolling mock assessments (test a subset of controls each month)
- Standing assessor relationship with annual engagement

**First-time audit (no prior assessment):**
- Start with evidence inventory 12 months before target assessment date
- Conduct two mock assessments: one at 6 months (identify major gaps) and one at 2 months (validate readiness)
- Engage a readiness consultant in addition to the assessor
- Budget additional time for control implementation (not just evidence collection)

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SP-002 | Extends — audit readiness builds on base QA process |
| PROC-GOV-001 | Depends on — CMMC control catalog drives evidence requirements |
| PROC-GOV-002 | Depends on — FedRAMP control catalog drives evidence requirements |
| PROC-GOV-009 | Feeds into — evidence collection provides the artifacts reviewed here |
| PROC-GOV-010 | Related — continuous monitoring produces ongoing evidence |
| PROC-ORG-002 | Extends — measurement process provides metrics evidence |

## 14. Traces

- **Governs:** Evidence inventories, gap analysis reports, mock assessment reports, finding trackers
- **Enforced by:** Quarterly gap analysis cadence, mock assessment 60–90 days before external assessment
- **Related QA:** QA-001 (SOC 2 Certification), QA-002 (FedRAMP Authorization), QA-003 (Defense Contractor Compliance)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

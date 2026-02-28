# PROC-GOV-010: Continuous Monitoring

**Version:** 1.0.0
**Status:** draft
**Category:** audit
**Layer:** gov
**Maturity:** initial
**Owner:** DevOps Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Establish a continuous monitoring (ConMon) program that maintains security posture visibility and satisfies ongoing federal compliance obligations after initial authorization. FedRAMP, CMMC, and SOC 2 all require evidence of continuous security monitoring — not just point-in-time assessments. This process defines the scanning cadence, configuration monitoring, POA&M management, and reporting required to maintain authorization and certification status.

## 2. Scope

This process covers continuous monitoring for:
- Vulnerability scanning and remediation across all claude-kit infrastructure
- Configuration drift detection and correction
- Plan of Action and Milestones (POA&M) lifecycle management
- Monthly and annual compliance reporting
- Significant change management

Included:
- Cloud platform infrastructure (compute, network, storage)
- Container images (devcontainer and any deployment containers)
- Application-layer vulnerabilities
- Dependency vulnerabilities (supply chain monitoring per PROC-GOV-004)
- AI agent execution environment security

Excluded:
- Customer environment monitoring (customer responsibility)
- Anthropic infrastructure monitoring (Anthropic responsibility)

## 3. Entry Criteria

- [ ] PROC-SEC-002 (Vulnerability Management) base process is established
- [ ] Initial authorization or certification is achieved (FedRAMP ATO, CMMC cert, or SOC 2 report)
- [ ] Vulnerability scanning tools are deployed and configured
- [ ] Configuration baselines are documented
- [ ] POA&M register is initialized with any open findings from initial assessment
- [ ] Reporting templates and distribution lists are established

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| FedRAMP Continuous Monitoring Strategy Guide | FedRAMP PMO | PDF |
| NIST SP 800-137 (Information Security Continuous Monitoring) | NIST | PDF |
| Vulnerability scanner output | Nessus/Qualys/Trivy | XML/PDF |
| Configuration management database (CMDB) | DevOps | Structured data |
| Previous POA&M register | PROC-GOV-001, 002 | Spreadsheet / GRC tool |
| Change request log | Engineering team | Ticketing system |

## 5. Activities

### 5.1 Vulnerability Scanning Cadence

Implement a tiered scanning program:

**Infrastructure scanning (monthly):**
- Scan all cloud infrastructure (servers, load balancers, databases) with an authenticated vulnerability scanner
- Include network-level and host-level scanning
- Scan results must be available within 72 hours of scan completion

**Container image scanning (per build + weekly):**
- Scan devcontainer image and any deployment images on every build
- Weekly re-scan of all production images to detect newly disclosed vulnerabilities
- Integrate Trivy or equivalent into CI/CD pipeline

**Application scanning (quarterly):**
- Static application security testing (SAST) on the claude-kit CLI
- Dynamic application security testing (DAST) on the cloud platform web interface and API
- Dependency scanning (SCA) for known vulnerabilities in runtime tools

**Penetration testing (annual):**
- Engage a qualified firm for annual penetration test
- Scope includes external attack surface and authenticated testing
- Report findings in the SAR format (for FedRAMP) or as a standalone report

**Remediation SLAs:**

| Severity | Remediation Timeline | Reporting Requirement |
|----------|---------------------|----------------------|
| Critical (CVSS >= 9.0) | 30 days | Report to AO within 72 hours, monthly update |
| High (CVSS 7.0–8.9) | 30 days | Include in monthly report |
| Medium (CVSS 4.0–6.9) | 90 days | Include in monthly report |
| Low (CVSS < 4.0) | 180 days | Include in quarterly report |

### 5.2 Configuration Monitoring

Detect and correct configuration drift from approved baselines:

**Baseline definition:**
- Document approved configurations for all infrastructure components
- Store baselines as infrastructure-as-code (Terraform, CloudFormation, Ansible)
- Version control all configuration files (already in Git for claude-kit)

**Drift detection:**
- Automated configuration comparison against baselines (daily or on-change)
- Alert on any deviation from approved configuration
- Classify drift by risk level:
  - Security-relevant drift: immediate alert and remediation
  - Operational drift: alert within 24 hours, remediate within 7 days
  - Cosmetic drift: log and remediate at next maintenance window

**Drift remediation:**
- Automated remediation for known-safe corrections (e.g., resetting a security group rule)
- Manual review required for complex or ambiguous drift
- All remediation actions logged with before/after states

### 5.3 Plan of Action and Milestones (POA&M) Management

Maintain the POA&M as a living document tracking all open findings:

**POA&M lifecycle:**
1. **Open:** New finding documented with description, risk level, and affected control
2. **In Progress:** Remediation work started, milestone updates recorded
3. **Completed:** Fix applied, evidence collected
4. **Verified:** Independent verification confirms the finding is resolved
5. **Closed:** Finding removed from active POA&M, archived

**POA&M fields (per FedRAMP requirements):**
- Weakness identifier and description
- Point of contact (responsible party)
- Resources required (budget, personnel, tools)
- Scheduled completion date
- Milestones with dates
- Source (scan, assessment, incident)
- Status and status date
- Vendor dependency flag (if remediation depends on Anthropic or another vendor)

**Deviation requests:**
- If remediation cannot meet the SLA, submit a deviation request to the AO
- Include: reason for delay, revised timeline, compensating controls, residual risk
- Track deviation approvals in the POA&M register

### 5.4 Monthly Reporting

Produce and submit monthly ConMon reports:

**FedRAMP monthly deliverables:**
- Vulnerability scan results (raw and summary)
- POA&M updates (new items, closed items, status changes)
- Significant change requests (if any)
- Incident reports (if any occurred during the month)
- Hardware and software inventory updates

**SOC 2 evidence (continuous):**
- Monitoring dashboards showing control effectiveness
- Exception reports for any control failures
- Remediation status for any exceptions

**CMMC evidence (continuous):**
- SPRS score updates (if practices changed status)
- POA&M progress updates

**Report distribution:**
- FedRAMP: Submit to sponsoring agency AO and FedRAMP PMO
- SOC 2: Archive for next audit cycle evidence package
- CMMC: Archive for C3PAO reassessment evidence

### 5.5 Significant Change Management

Evaluate and report significant changes that may affect the authorization boundary:

**Significant change triggers:**
- New external service integration (e.g., new API endpoint)
- Change to authentication mechanism
- Change to encryption methods or key management
- New data types processed (especially CUI or PII)
- Infrastructure migration (cloud provider change, region change)
- Major version upgrade of critical components

**Significant change process:**
1. Identify the change as potentially significant
2. Conduct security impact analysis
3. Submit significant change request to the AO (FedRAMP) or document internally (SOC 2, CMMC)
4. If approved, implement the change with enhanced monitoring
5. If the AO requires re-assessment, coordinate with 3PAO

### 5.6 Annual Assessment

Support the annual assessment required by all frameworks:

**FedRAMP annual assessment:**
- 3PAO assesses a subset of controls (typically 1/3 of the baseline per year)
- Over three years, all controls are assessed
- Coordinate with PROC-GOV-008 for assessment preparation

**SOC 2 Type II:**
- CPA firm assesses all Trust Services Criteria during the observation period
- Coordinate with PROC-GOV-008 for audit preparation

**CMMC reassessment:**
- Triennial C3PAO assessment for Level 2
- Annual self-assessment and affirmation for Level 1
- Coordinate with PROC-GOV-001 for assessment preparation

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Monthly ConMon Report | `qms/artifacts/gov/` | — | GOV-CONMON-XXX |
| POA&M Register | `qms/artifacts/gov/` | FedRAMP POA&M template | GOV-POAM-XXX |
| Vulnerability Scan Reports | `qms/artifacts/gov/` | — | GOV-VSCAN-XXX |
| Configuration Drift Reports | `qms/artifacts/gov/` | — | GOV-DRIFT-XXX |
| Significant Change Requests | `qms/artifacts/gov/` | — | GOV-SCR-XXX |
| Annual Assessment Support Package | `qms/artifacts/gov/` | — | GOV-ASP-XXX |

## 7. Exit Criteria

- [ ] Vulnerability scanning cadence is operational and producing results
- [ ] Configuration monitoring is active with drift detection and alerting
- [ ] POA&M register is current with all open findings tracked
- [ ] First monthly ConMon report is delivered on time
- [ ] Significant change process is documented and understood by engineering
- [ ] Annual assessment schedule is confirmed with assessor

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Scanning coverage | Scan scope vs. asset inventory | 100% of in-scope assets scanned on cadence |
| Remediation SLA compliance | POA&M aging analysis | Zero SLA breaches for critical/high |
| Report timeliness | Delivery date tracking | Monthly reports delivered by 5th business day |
| Configuration compliance | Drift report review | < 5% of configurations in drift state |
| POA&M accuracy | Cross-reference with scan results | All critical/high findings captured in POA&M |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| DevOps Lead | Owns scanning infrastructure, configuration monitoring, automated reporting |
| Security Lead | Reviews scan results, prioritizes remediation, manages POA&M |
| Compliance Officer | Assembles and submits monthly reports, tracks reporting SLAs |
| Engineering Lead | Remediates application-layer vulnerabilities, supports significant change analysis |
| CISO | Reviews monthly reports, approves deviation requests, briefs leadership |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Scan completion rate | Scheduled scans completed on time | 100% | Scanner logs |
| Remediation SLA compliance | Vulnerabilities remediated within SLA | >= 95% | POA&M aging report |
| Mean time to remediate (MTTR) | Average days from finding to closure by severity | Critical: < 15 days, High: < 30 days | POA&M analysis |
| Monthly report SLA | Reports delivered by deadline | 100% | Delivery log |
| POA&M item count | Total open POA&M items (trend) | Decreasing trend | Monthly POA&M snapshot |
| Configuration drift rate | Percentage of assets with detected drift | < 5% | Configuration monitoring |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-137 | All sections | Continuous monitoring framework |
| FedRAMP ConMon Guide | Monthly deliverables, scanning requirements | FedRAMP-specific ConMon |
| NIST SP 800-53 Rev 5 | RA-5 (Vulnerability Scanning), CM-3 (Configuration Change Control), CA-7 (Continuous Monitoring) | Security controls for ConMon |
| AICPA TSC 2017 | CC7.1 (Detection), CC7.2 (Monitoring) | SOC 2 continuous monitoring |
| CMMC 2.0 | CA.L2-3.12.1 (Security Assessments), RA.L2-3.11.2 (Vulnerability Scan) | CMMC monitoring practices |

## 12. Tailoring Guidance

**SOC 2 only (no federal authorization):**
- Monthly vulnerability scanning (internal and external)
- Configuration monitoring recommended but not mandatory at specific cadence
- POA&M equivalent: exception tracking in the GRC tool
- No formal monthly reporting to an AO — evidence archived for auditor

**FedRAMP Moderate (full ConMon):**
- Execute all activities as written
- Monthly reporting to AO is mandatory
- 3PAO annual assessment is mandatory
- Significant change process is mandatory

**CMMC Level 2:**
- Monthly scanning per RA.L2-3.11.2
- POA&M management per CA.L2-3.12.2
- No monthly reporting to an external authority (self-managed)
- Triennial C3PAO reassessment

**Air-gapped environments:**
- Scanning must use locally installed tools (no cloud-based scanners)
- Results exported via approved media transfer process
- Configuration monitoring operates locally within the air-gapped enclave
- Reporting delivered via secure, out-of-band channels
- Coordinate with PROC-GOV-011 for offline-specific monitoring procedures

**Early stage (just received authorization):**
- Focus on establishing monthly scanning and reporting rhythm
- POA&M may have many items from initial assessment — prioritize by risk
- Accept that the first few monthly reports will be rough — improve format iteratively
- Automate reporting as much as possible to reduce manual burden

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-002 | Extends — continuous monitoring extends base vulnerability management |
| PROC-GOV-001 | Related — CMMC requires ongoing monitoring of 800-171 controls |
| PROC-GOV-002 | Related — FedRAMP ConMon is a post-ATO requirement |
| PROC-GOV-008 | Feeds into — continuous monitoring evidence supports audit readiness |
| PROC-GOV-009 | Depends on — evidence collection provides monitoring artifacts |
| PROC-GOV-007 | Related — zero trust telemetry feeds into monitoring |

## 14. Traces

- **Governs:** Monthly ConMon reports, POA&M register, vulnerability scan reports, drift reports
- **Enforced by:** Monthly reporting deadlines, automated scanning schedules, configuration monitoring alerts
- **Related QA:** (Cross-cutting — supports QA-001, QA-002, QA-003 ongoing compliance)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

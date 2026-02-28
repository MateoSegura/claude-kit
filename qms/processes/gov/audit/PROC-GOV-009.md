# PROC-GOV-009: Evidence Collection

**Version:** 1.0.0
**Status:** draft
**Category:** audit
**Layer:** gov
**Maturity:** initial
**Owner:** Compliance Officer
**Last Reviewed:** 2026-02-28

## 1. Purpose

Define the systematic process for collecting, organizing, and maintaining compliance evidence across all regulatory frameworks. Evidence is the tangible proof that controls are designed and operating effectively. Without reliable, current, and traceable evidence, audit outcomes are jeopardized regardless of how well controls actually function. This process establishes evidence chain of custody, automated collection pipelines, and evidence lifecycle management.

## 2. Scope

This process covers evidence collection for all compliance frameworks applicable to claude-kit:
- SOC 2 Type II Trust Services Criteria
- FedRAMP Moderate baseline (NIST 800-53)
- CMMC Level 2 (NIST 800-171)
- EO 14028 supply chain requirements
- AI transparency requirements (OMB M-25-22, NIST AI RMF)

Included:
- Automated evidence gathering from technical systems
- Manual evidence collection for procedural controls
- Evidence chain of custody and integrity
- Evidence refresh cadence and lifecycle management
- Evidence package assembly for assessors

Excluded:
- Evidence assessment (assessor responsibility)
- Control design and implementation (covered by framework-specific processes)

## 3. Entry Criteria

- [ ] PROC-ORG-002 (Measurement) base process is established
- [ ] Control catalogs are defined for at least one target framework
- [ ] Evidence sources are identified and accessible
- [ ] Evidence storage system is provisioned with appropriate access controls
- [ ] Evidence collection schedule is drafted

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Control catalog with evidence requirements | PROC-GOV-001, 002 | GRC tool / spreadsheet |
| System access credentials for evidence sources | DevOps / Security | Credential vault |
| Evidence collection schedule | Compliance Officer | Calendar / schedule document |
| Previous evidence packages (if any) | Prior audit cycles | Archived packages |
| Assessor evidence request lists | External assessors | Document / spreadsheet |

## 5. Activities

### 5.1 Evidence Source Mapping

Map each control to its evidence source(s) and collection method:

| Control Family | Evidence Type | Source System | Collection Method | Format |
|---------------|---------------|---------------|-------------------|--------|
| Access Control | User access logs | IdP (Okta, Azure AD) | API export | JSON/CSV |
| Access Control | Access review records | GRC tool | Manual export | PDF |
| Audit and Accountability | Audit logs | SIEM (Datadog, Panther) | Automated export | JSON |
| Change Management | PR merge records | GitHub | API export | JSON |
| Change Management | Deployment logs | GitHub Actions | API export | JSON |
| Vulnerability Management | Scan results | Nessus/Qualys/Trivy | Automated export | PDF/XML |
| Incident Response | IR tickets and post-mortems | Ticketing system | Manual export | PDF |
| Configuration Management | IaC configurations | Git repository | Git snapshot | YAML/HCL |
| Encryption | Certificate inventory | Certificate manager | Automated inventory | JSON |
| Personnel Security | Training records | LMS | Automated export | CSV |
| Supply Chain | SBOM artifacts | CI/CD pipeline | Automated generation | SPDX/CDX |
| AI Transparency | AI risk assessments | PROC-GOV-005 | Manual collection | Markdown/PDF |

Maintain this mapping in the GRC tool. Review and update quarterly or when systems change.

### 5.2 Automated Evidence Gathering

Implement automated collection pipelines for technical evidence:

**CI/CD pipeline evidence:**
- GitHub Actions workflow logs are retained automatically
- PR review records are preserved in GitHub's audit log
- Build artifacts include SBOM and provenance attestations (per PROC-GOV-004)
- Plugin validation results are logged in CI output

**Infrastructure evidence:**
- Schedule automated exports from IdP, SIEM, and vulnerability scanners
- Use API integrations to pull evidence into the GRC tool on a scheduled cadence
- Implement heartbeat monitoring to detect collection failures

**Compliance automation platform:**
- If using Vanta/Drata/Secureframe, configure integrations with all evidence sources
- Verify automated evidence passes the platform's own validation checks
- Use the platform's evidence history as a continuous evidence timeline

**claude-kit specific evidence:**
- Plugin validation scripts (`validate-plugins.py`, `test-plugin-consistency.sh`) produce evidence of quality control
- Encryption verification can be automated via `openssl` commands in CI
- Hook execution logs demonstrate runtime governance
- The `fast-validate` CI job produces build and test evidence on every push

### 5.3 Manual Evidence Collection

For evidence that cannot be automated, establish manual collection procedures:

**Procedural evidence:**
- Policy documents: collect signed/approved versions with revision history
- Meeting minutes: capture security review and management review meeting notes
- Risk acceptance decisions: document with approver signatures
- Vendor risk assessments: collect completed questionnaires and certifications

**Collection protocol:**
1. Identify the evidence item on the collection schedule
2. Collect from the designated source
3. Label with: evidence ID, control mapping, collection date, collector name
4. Store in the evidence repository with read-only permissions
5. Log the collection event in the evidence chain of custody record

### 5.4 Evidence Chain of Custody

Maintain chain of custody for all evidence to ensure integrity and admissibility:

**Integrity controls:**
- Evidence stored in write-once storage or with versioning enabled (S3 versioning, Git LFS)
- SHA-256 hash computed at collection time and recorded in the evidence register
- Any modification to evidence creates a new version (original preserved)

**Custody log:**

| Evidence ID | Collected By | Collection Date | Hash (SHA-256) | Storage Location | Access Granted To |
|-------------|--------------|-----------------|----------------|------------------|-------------------|
| EV-001 | System (automated) | 2026-02-28 | a1b2c3... | s3://evidence/2026-02/ | Compliance team, assessor |

**Access controls:**
- Evidence repository access limited to compliance team and authorized assessors
- All access logged with timestamp and identity
- Assessor access provisioned at engagement start, revoked at engagement end

### 5.5 Evidence Refresh Cadence

Define and enforce refresh schedules to keep evidence current:

| Evidence Category | Refresh Cadence | Staleness Threshold |
|-------------------|-----------------|---------------------|
| Access logs | Continuous (automated) | 24 hours |
| Vulnerability scans | Monthly | 45 days |
| Configuration baselines | Per change (automated) | 7 days after change |
| Training records | Quarterly | 120 days |
| Policy documents | Annual | 15 months |
| Vendor assessments | Annual | 15 months |
| Risk assessments | Annual or per change | 15 months |
| Incident response records | Per incident | N/A (event-driven) |
| SBOM | Per release | N/A (event-driven) |

Monitor evidence freshness weekly. Alert when evidence approaches the staleness threshold. Escalate stale evidence to the control owner for refresh.

### 5.6 Evidence Package Assembly

Assemble evidence packages for assessor consumption:

**Pre-assessment package:**
- Organize evidence by control family or domain
- Include an evidence index mapping each item to its control(s)
- Label every artifact with collection date and source
- Verify all items are within freshness thresholds
- Package in a secure, shareable format (encrypted ZIP or secure file share)

**During assessment:**
- Respond to ad-hoc evidence requests within the agreed SLA (typically 24-48 hours)
- Log all evidence provided to the assessor
- Track outstanding requests in a shared tracker

**Post-assessment archive:**
- Archive the complete evidence package with the final assessment report
- Retain per the longest applicable retention requirement (typically 7 years for federal)
- Store in the evidence repository with read-only access

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Evidence Source Map | `qms/artifacts/gov/` | — | GOV-ESM-XXX |
| Evidence Chain of Custody Log | `qms/artifacts/gov/` | — | GOV-COC-XXX |
| Evidence Freshness Report | `qms/artifacts/gov/` | — | GOV-EFR-XXX |
| Evidence Package (per assessment) | `qms/artifacts/gov/` | — | GOV-EPKG-XXX |
| Collection Pipeline Configuration | `qms/artifacts/gov/` | — | GOV-CPC-XXX |

## 7. Exit Criteria

- [ ] Evidence source map covers 100% of in-scope controls
- [ ] Automated collection pipelines are operational for all technical evidence
- [ ] Manual collection procedures are documented and assigned
- [ ] Chain of custody system is operational with integrity verification
- [ ] Evidence refresh cadence is enforced with monitoring and alerting
- [ ] At least one evidence package has been assembled and reviewed

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Source map completeness | Cross-reference with control catalog | 100% of controls mapped to evidence sources |
| Automation coverage | Audit of automated vs. manual collection | >= 70% of evidence items collected automatically |
| Freshness compliance | Evidence freshness report | Zero items past staleness threshold |
| Integrity verification | Hash verification on random sample | 100% of sampled items pass hash check |
| Package review | Pre-submission quality review | Evidence index complete, all items labeled and current |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Compliance Officer | Owns evidence program, maintains source map, manages collection schedule |
| DevOps Lead | Implements automated collection pipelines, manages evidence storage |
| Control Owners (various) | Provide manual evidence on schedule, verify evidence accuracy |
| Security Lead | Reviews evidence integrity, supports chain of custody |
| Assessment Coordinator | Assembles evidence packages, manages assessor evidence requests |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Evidence coverage | Controls with mapped and collected evidence | 100% | Evidence source map audit |
| Automation rate | Percentage of evidence collected automatically | >= 70% | Collection pipeline audit |
| Freshness compliance | Evidence items within staleness threshold | 100% | Weekly freshness report |
| Collection SLA | Evidence requests fulfilled within SLA | >= 95% within 48 hours | Request tracker |
| Evidence integrity | Items passing hash verification | 100% | Monthly hash audit |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| AICPA TSC 2017 | CC4.1 (COSO Monitoring) | Evidence supports SOC 2 monitoring activities |
| NIST SP 800-53 Rev 5 | AU-2, AU-3, AU-6 (Audit and Accountability) | Audit log evidence collection |
| NIST SP 800-53 Rev 5 | CA-2 (Security Assessments) | Evidence assembly for assessments |
| CMMC Assessment Guide | Evidence requirements per practice | CMMC evidence collection |
| FedRAMP ConMon Guide | Monthly evidence submission | Continuous monitoring evidence |
| ISO 27001:2022 | A.5.36 (Compliance with policies and standards) | Evidence of compliance verification |

## 12. Tailoring Guidance

**Single framework (SOC 2 only):**
- Evidence source map scoped to Trust Services Criteria
- Annual evidence package for Type II observation period
- Manual collection acceptable if team size is small
- Compliance automation platform (Vanta/Drata) handles most collection

**Multi-framework:**
- Unified evidence source map with framework cross-references
- Automated collection is essential — manual does not scale
- GRC tool required for multi-framework evidence management
- Evidence packages may share artifacts across frameworks (document the mapping)

**Early stage (first audit cycle):**
- Start with manual collection to understand what assessors expect
- Automate incrementally based on collection frequency and volume
- Accept lower automation rates (50%) for the first cycle
- Focus on evidence quality over quantity — assessors prefer well-organized subsets

**Mature organization:**
- Real-time evidence dashboards
- Assessor self-service portal for evidence access
- Automated integrity verification (scheduled hash checks)
- Predictive freshness alerts (warn before staleness, not after)

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-ORG-002 | Extends — evidence collection builds on base measurement process |
| PROC-GOV-008 | Feeds into — audit readiness consumes evidence from this process |
| PROC-GOV-010 | Feeds into — continuous monitoring relies on ongoing evidence collection |
| PROC-GOV-001 | Depends on — CMMC control catalog defines required evidence |
| PROC-GOV-002 | Depends on — FedRAMP control catalog defines required evidence |
| PROC-GOV-005 | Related — AI transparency evidence requires specific collection methods |

## 14. Traces

- **Governs:** Evidence source maps, chain of custody logs, evidence packages, freshness reports
- **Enforced by:** Weekly freshness monitoring, automated collection pipeline heartbeats, quarterly source map reviews
- **Related QA:** QA-001 (SOC 2 Certification), QA-002 (FedRAMP Authorization), QA-003 (Defense Contractor Compliance)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

# PROC-GOV-002: FedRAMP Authorization

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Compliance Officer
**Last Reviewed:** 2026-02-28

## 1. Purpose

Define the process for achieving and maintaining FedRAMP authorization for the claude-kit cloud platform. FedRAMP authorization is required to sell cloud services to federal agencies and is increasingly expected by state and local governments. This process covers the full authorization lifecycle from impact level determination through continuous monitoring.

## 2. Scope

This process covers the FedRAMP authorization lifecycle for the claude-kit cloud platform (REQ-009):
- FedRAMP Moderate baseline (the most common for B2G SaaS)
- Both Agency ATO and JAB P-ATO paths
- Continuous monitoring (ConMon) post-authorization

Included:
- Cloud platform infrastructure and application layers
- Plugin distribution service endpoints
- AI agent orchestration services
- Customer-facing APIs and web interfaces
- Administrative and operational tooling

Excluded:
- Air-gapped deployment variants (covered by PROC-GOV-011)
- Customer-side infrastructure (covered by shared responsibility matrix in PROC-GOV-013)
- Anthropic model API internals (covered by vendor risk assessment)

## 3. Entry Criteria

- [ ] PROC-SP-002 (Quality Assurance) base process is established and operational
- [ ] PROC-SEC-001 through PROC-SEC-005 (Security processes) are established
- [ ] Cloud platform architecture is documented with boundary diagrams
- [ ] A sponsoring federal agency is identified (for Agency ATO path) or JAB prioritization is approved
- [ ] FedRAMP readiness assessment is complete
- [ ] Budget allocated for 3PAO engagement ($150K–$500K range)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| NIST SP 800-53 Rev 5 control catalog | NIST | Structured data / OSCAL |
| FedRAMP Moderate baseline | FedRAMP PMO | Excel / OSCAL |
| System architecture diagrams | Architecture team | Diagrams |
| Data flow diagrams | Architecture team | Diagrams |
| Current security control inventory | PROC-SEC-001 | GRC tool export |
| QA-002 (FedRAMP Authorization) | docs/quality/ | Markdown |
| FedRAMP Readiness Assessment Report | 3PAO | PDF |

## 5. Activities

### 5.1 Impact Level Determination

Determine the FIPS 199 impact level (Low, Moderate, High) for the cloud system based on data sensitivity:
- Low: No CUI, no PII beyond basic user accounts
- Moderate: CUI, sensitive PII, or financial data
- High: National security systems, law enforcement sensitive data

For claude-kit, Moderate is the expected baseline given potential CUI handling in customer environments. Document the categorization rationale with references to FIPS 199 and CNSSI 1253.

### 5.2 FedRAMP Path Selection

Choose between Agency ATO and JAB P-ATO:

**Agency ATO:** Faster path when a willing agency sponsor exists. The agency's Authorizing Official (AO) reviews and issues the ATO. Authorization is then listed on the FedRAMP Marketplace for reuse by other agencies.

**JAB P-ATO:** Higher initial bar but broader acceptance. Requires JAB prioritization (competitive process). The JAB (DoD, DHS, GSA) reviews directly. Preferred if no single agency sponsor is available.

Document the selected path and rationale.

### 5.3 System Security Plan (SSP) Authoring

Author the SSP using the FedRAMP SSP template (or OSCAL-based equivalent). The SSP must document:
- System boundary and architecture
- All 325 Moderate baseline controls with implementation descriptions
- Customer responsibilities (for controls shared with customer environments)
- Inherited controls (from IaaS/PaaS providers like AWS GovCloud or Azure Government)
- Control implementation narratives that reference specific technical configurations

Leverage existing documentation from PROC-SEC-001 through PROC-SEC-005 and rewrite as FedRAMP-formatted control responses.

### 5.4 Security Assessment Plan (SAP) Development

Work with the selected 3PAO to develop the SAP:
- Define assessment scope and methodology
- Identify testable controls vs. interview-only controls
- Schedule assessment windows (typically 4–6 weeks for Moderate)
- Prepare test environments that mirror production

### 5.5 3PAO Assessment Execution

Support the 3PAO during the security assessment:
- Provide system access and documentation
- Facilitate control owner interviews
- Demonstrate technical controls (scanning, logging, encryption, access control)
- Remediate findings in real-time where feasible
- Track all findings in the Security Assessment Report (SAR)

### 5.6 ATO Package Assembly

Assemble the complete authorization package:
- System Security Plan (SSP)
- Security Assessment Plan (SAP)
- Security Assessment Report (SAR)
- Plan of Action and Milestones (POA&M)
- Continuous Monitoring Strategy
- Incident Response Plan
- Configuration Management Plan
- Supply Chain Risk Management Plan
- Privacy Impact Assessment (if PII is processed)

Submit to the authorizing authority (agency AO or JAB).

### 5.7 Authorization Decision

Support the AO or JAB review process:
- Respond to additional questions or clarification requests
- Provide risk acceptance justification for any open POA&M items
- Brief the AO or JAB on residual risk
- Receive the ATO letter or P-ATO memo

### 5.8 FedRAMP Marketplace Listing

After authorization:
- Submit the authorization package to the FedRAMP PMO
- List the system on the FedRAMP Marketplace
- Publish the customer responsibility matrix
- Enable other agencies to leverage the existing authorization

### 5.9 Continuous Monitoring (ConMon)

Post-authorization, maintain the ATO through ongoing monitoring (see also PROC-GOV-010):
- Monthly vulnerability scanning and remediation
- Annual security assessment (subset of controls)
- Significant change requests when architecture changes occur
- Monthly POA&M updates to the authorizing authority
- Annual SSP update

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| FIPS 199 Categorization | `qms/artifacts/gov/` | — | GOV-FIPS-XXX |
| System Security Plan (SSP) | `qms/artifacts/gov/` | FedRAMP SSP template | GOV-SSP-XXX |
| Security Assessment Plan (SAP) | `qms/artifacts/gov/` | FedRAMP SAP template | GOV-SAP-XXX |
| Security Assessment Report (SAR) | `qms/artifacts/gov/` | FedRAMP SAR template | GOV-SAR-XXX |
| Plan of Action and Milestones | `qms/artifacts/gov/` | FedRAMP POA&M template | GOV-POAM-XXX |
| ATO Letter / P-ATO Memo | `qms/artifacts/gov/` | — | GOV-ATO-XXX |
| ConMon Monthly Reports | `qms/artifacts/gov/` | — | GOV-CONMON-XXX |

## 7. Exit Criteria

- [ ] ATO or P-ATO is granted by the authorizing authority
- [ ] System is listed on the FedRAMP Marketplace
- [ ] Continuous monitoring cadence is established and first month completed
- [ ] Customer responsibility matrix is published
- [ ] All critical and high findings from the SAR are remediated or on approved POA&M

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Impact level determination | CISO review and concurrence | Documented rationale with FIPS 199 references |
| SSP completeness | 3PAO readiness review | All 325 Moderate controls have implementation narratives |
| SAR risk threshold | Risk analysis of findings | No more than 5 high findings; zero critical findings open |
| ATO package completeness | FedRAMP PMO checklist | All required documents present and current |
| ConMon establishment | First monthly report delivery | Vulnerability scans, POA&M update, and deviation reports submitted |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Compliance Officer | Owns FedRAMP program, manages 3PAO relationship, tracks authorization timeline |
| Security Lead | Authors SSP control narratives, implements technical controls |
| CISO | Approves risk decisions, briefs AO, signs authorization artifacts |
| Engineering Lead | Provides system architecture documentation, supports 3PAO testing |
| DevOps Lead | Configures scanning tools, maintains ConMon automation |
| Legal Counsel | Reviews privacy impact assessment, contract obligations |
| 3PAO | Independent assessor — conducts SAP, SAR, annual assessments |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| SSP control coverage | Percentage of baseline controls with complete narratives | 100% | GRC tool |
| 3PAO finding count | Number of findings by severity | < 5 high, 0 critical | SAR review |
| Time to ATO | Months from readiness assessment to authorization | <= 12 months | Project timeline |
| ConMon SLA compliance | Percentage of monthly reports delivered on time | 100% | FedRAMP PMO tracker |
| POA&M aging | Average age of open POA&M items | < 90 days for high, < 180 days for moderate | POA&M register |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-53 Rev 5 | All 325 Moderate baseline controls | Technical control foundation for FedRAMP |
| FIPS 199 | Security Categorization | Determines the FedRAMP impact level |
| FIPS 200 | Minimum Security Requirements | Establishes the minimum control baseline |
| NIST SP 800-37 Rev 2 | Risk Management Framework | Process framework for authorization lifecycle |
| FedRAMP Authorization Act (P.L. 117-263) | Title XXXV | Legislative mandate for FedRAMP program |
| OMB A-130 | Managing Information as a Strategic Resource | Federal information security requirements |

## 12. Tailoring Guidance

**FedRAMP Low (Li-SaaS or Low baseline):**
- Reduce SSP scope to 156 Low baseline controls
- 3PAO assessment is shorter (2–3 weeks vs. 4–6 weeks)
- ConMon reporting may be quarterly instead of monthly (check current FedRAMP guidance)
- Lower cost ($50K–$150K vs. $150K–$500K for Moderate)

**FedRAMP Moderate (standard path):**
- Execute all activities as written
- Plan for 9–18 months end-to-end
- Budget $150K–$500K for 3PAO and consulting

**FedRAMP High:**
- Extends Moderate with additional controls (421 total)
- Requires GovCloud or equivalent high-boundary infrastructure
- Physical security and personnel security controls become stringent
- Coordinate with PROC-GOV-012 (Impact Level Qualification) for IL4/IL5 requirements

**Agency ATO reuse (leveraging existing P-ATO):**
- Skip Activities 5.4 and 5.5 (assessment already complete)
- Agency reviews the existing package and issues its own ATO
- Focus on gap analysis between agency-specific requirements and the existing authorization

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SP-002 | Extends — FedRAMP builds on base QA controls |
| PROC-SEC-001 | Extends — security controls map to NIST 800-53 families |
| PROC-SEC-002 | Extends — vulnerability management feeds ConMon |
| PROC-SEC-003 | Extends — incident response is a FedRAMP requirement |
| PROC-SEC-004 | Extends — access control maps to AC family |
| PROC-SEC-005 | Extends — encryption maps to SC family |
| PROC-GOV-010 | Feeds into — continuous monitoring is post-ATO lifecycle |
| PROC-GOV-012 | Depends on — impact level qualification for DoD cloud SRG |
| PROC-GOV-013 | Related — shared responsibility boundary affects SSP scope |
| PROC-GOV-008 | Feeds into — audit readiness process supports 3PAO prep |

## 14. Traces

- **Governs:** FedRAMP authorization artifacts (SSP, SAP, SAR, POA&M, ATO letter)
- **Enforced by:** FedRAMP PMO ConMon requirements, annual 3PAO reassessment
- **Related QA:** QA-002 (FedRAMP Authorization)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

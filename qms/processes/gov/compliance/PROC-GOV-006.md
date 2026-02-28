# PROC-GOV-006: CUI Handling

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Define the controls for handling Controlled Unclassified Information (CUI) within claude-kit environments. While claude-kit itself does not process CUI, customers in the Defense Industrial Base (DIB) may deploy it in environments where CUI is present. This process ensures that claude-kit's architecture supports CUI protection requirements and that organizational handling of any CUI received during development, testing, or support is compliant with 32 CFR Part 2002 and NIST SP 800-171.

## 2. Scope

This process covers:
- CUI that may be encountered during customer support or integration activities
- CUI marking, handling, and destruction requirements for organizational personnel
- Architecture requirements for claude-kit to function in CUI-designated environments
- Access controls for personnel who may handle CUI
- Incident reporting obligations when CUI is compromised

Excluded:
- Customer CUI management within their own environments (customer responsibility)
- Classified information handling (separate process required for SECRET and above)
- CUI within Anthropic's infrastructure (Anthropic's responsibility per DPA)

## 3. Entry Criteria

- [ ] PROC-SEC-004 (Access Control) base process is established
- [ ] PROC-SEC-005 (Encryption) base process is established
- [ ] CUI organizational policy is documented and approved
- [ ] Personnel with potential CUI access have completed CUI training
- [ ] CUI-designated systems are identified and inventoried
- [ ] NIST SP 800-171 self-assessment is current (from PROC-GOV-001)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| 32 CFR Part 2002 | Federal Register | Regulatory text |
| NIST SP 800-171 Rev 2 | NIST | PDF / structured data |
| CUI Registry (categories and subcategories) | NARA (National Archives) | Web / PDF |
| Contract DFARS clauses | Contracts team | Contract excerpts |
| System boundary documentation | Architecture team | Diagrams |
| QA-003 (Defense Contractor Compliance) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 CUI Identification and Marking

Establish procedures for identifying and marking CUI:

**CUI categories relevant to claude-kit:**
- CTI (Controlled Technical Information) — technical data with military or space application
- OPSEC — operational security information
- Proprietary Business Information — when received from government customers
- Source Selection Information — during contract competitions

**Marking requirements:**
- Banner marking: "CUI" or "CONTROLLED" at top and bottom of documents
- Category marking: Include the CUI category (e.g., "CUI//SP-CTI")
- Portion marking: Mark individual paragraphs when documents contain mixed CUI/non-CUI
- Electronic files: Include CUI markings in file metadata and visible headers

Train all personnel who may encounter CUI on recognition and marking procedures. Provide marking templates and quick-reference guides.

### 5.2 Access Controls for CUI

Implement access controls that satisfy NIST SP 800-171 requirements:

**Personnel controls:**
- Limit CUI access to personnel with a legitimate need-to-know
- Verify citizenship status for CUI access (CUI does not require clearance but is restricted to authorized persons)
- Maintain access lists with regular reviews (quarterly)
- Revoke access immediately upon role change or separation

**System controls:**
- Multi-factor authentication (MFA) required for all CUI systems
- Role-based access control (RBAC) with least privilege
- Session timeout after 15 minutes of inactivity
- Audit logging of all CUI system access

**Physical controls (for air-gapped environments):**
- CUI areas restricted to authorized personnel
- Visitor escort and logging requirements
- Clean desk policy enforcement
- Approved storage containers for CUI media

### 5.3 Encryption Requirements

Ensure all CUI is protected by FIPS 140-2 validated encryption:

**At rest:**
- AES-256 encryption for stored CUI (claude-kit already uses AES-256-CBC for plugin encryption)
- Encryption keys managed per NIST SP 800-57
- FIPS 140-2 validated cryptographic modules required in CUI environments

**In transit:**
- TLS 1.2 or higher for all network communications
- VPN or encrypted tunnels for remote access to CUI systems
- Email containing CUI must use S/MIME or equivalent encryption

**claude-kit specific:**
- Plugin content encryption (AES-256-CBC) satisfies the at-rest requirement for plugin data
- Customer environments must configure FIPS-validated crypto modules at the OS level
- Document FIPS mode requirements in customer deployment guides

### 5.4 CUI in AI Agent Contexts

Address CUI handling specific to AI agent workflows:

**Context window isolation:**
- AI agents must not carry CUI between separate customer sessions
- Session data (prompts, responses, tool outputs) that may contain CUI must not persist beyond the session
- Anthropic API data handling must comply with CUI requirements (verify via DPA)

**Plugin knowledge:**
- Knowledge skills must not contain CUI — they provide reference material only
- If a customer's codebase contains CUI, the AI agent's context window temporarily holds CUI during the session
- Document this data flow in the CUI handling guide

**Logging:**
- Session logs that may capture CUI must be stored in CUI-designated systems
- Log retention must follow the contract-specified retention period
- Log destruction must follow approved sanitization methods

### 5.5 Incident Reporting to DIBCAC

When CUI is potentially compromised:

**Detection triggers:**
- Unauthorized access to CUI systems (detected via audit logs)
- CUI found in non-designated systems or locations
- Loss of media containing CUI
- Suspected exfiltration or unauthorized disclosure

**Reporting timeline:**
- Report to DIBCAC (Defense Industrial Base Cybersecurity Assessment Center) within 72 hours of discovery
- Provide: incident description, affected CUI categories, scope assessment, containment actions
- Preserve all evidence for forensic analysis
- Coordinate with PROC-SEC-003 (Incident Response) for technical response

**Remediation:**
- Contain the incident (isolate affected systems)
- Assess the scope of CUI exposure
- Implement corrective actions
- Update POA&M if control weaknesses are identified
- Brief affected government program offices

### 5.6 CUI Destruction

When CUI is no longer needed or retention period expires:

**Electronic media:** Use NIST SP 800-88 sanitization methods:
- Clear: overwrite with non-sensitive data (acceptable for reuse within CUI environment)
- Purge: degauss or cryptographic erase (for media leaving CUI environment)
- Destroy: physical destruction for end-of-life media

**Paper:** Cross-cut shredding (particle size per NSA/CSS EPL)

**Cloud environments:** Verify cloud provider's data destruction procedures satisfy 800-88. For air-gapped environments, document destruction on a media accountability log.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| CUI Handling Guide | `qms/artifacts/gov/` | — | GOV-CUI-XXX |
| Access Control List (CUI) | `qms/artifacts/gov/` | — | GOV-ACL-XXX |
| CUI Incident Report | `qms/artifacts/gov/` | — | GOV-CUI-INC-XXX |
| Media Destruction Log | `qms/artifacts/gov/` | — | GOV-MDL-XXX |
| CUI Training Records | `qms/artifacts/gov/` | — | GOV-CUI-TRN-XXX |

## 7. Exit Criteria

- [ ] CUI handling guide is published and distributed to all relevant personnel
- [ ] Access controls are implemented and validated for CUI systems
- [ ] Encryption meets FIPS 140-2 validation requirements
- [ ] Incident reporting procedure is documented and tested
- [ ] Personnel CUI training is complete with documented records
- [ ] CUI destruction procedures are documented and operational

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Access control review | Quarterly access list audit | No unauthorized personnel, all access justified |
| Encryption validation | FIPS 140-2 module verification | All CUI systems using validated modules |
| Training completion | Training record audit | 100% of CUI-authorized personnel trained |
| Incident response test | Tabletop exercise | CUI incident reported within 72-hour SLA |
| Marking compliance | Random sample review | 100% of sampled CUI documents correctly marked |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns CUI protection program, implements access controls, manages incidents |
| Compliance Officer | Tracks training compliance, maintains CUI handling guide, files DIBCAC reports |
| Engineering Lead | Implements encryption controls, AI context isolation, logging requirements |
| All Personnel | Complete CUI training, follow marking and handling procedures, report incidents |
| CUI Program Manager (if designated) | Day-to-day CUI program operations, access list management |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Training completion rate | Personnel with current CUI training | 100% | Training records |
| Access review cadence | Quarterly access list reviews completed | 100% | Review log |
| Incident response time | Time from detection to DIBCAC notification | < 72 hours | Incident log |
| Marking compliance | Correctly marked CUI documents (sample) | 100% | Quarterly audit |
| Encryption coverage | CUI systems with FIPS 140-2 validated crypto | 100% | System inventory |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| 32 CFR Part 2002 | Subparts A–C (establishment, marking, handling) | CUI program regulation |
| NIST SP 800-171 Rev 2 | 3.1 (Access Control), 3.8 (Media Protection), 3.13 (System/Comm Protection) | Technical control requirements |
| DFARS 252.204-7012 | Safeguarding Covered Defense Information | Contract clause mandating CUI protection |
| NIST SP 800-88 Rev 1 | Media Sanitization Guidelines | CUI destruction standards |
| FIPS 140-2 | Security Requirements for Cryptographic Modules | Encryption validation requirement |
| NIST SP 800-57 Part 1 | Key Management | Encryption key lifecycle |

## 12. Tailoring Guidance

**Organizations that do not handle CUI:**
- Maintain awareness training only (recognize CUI if received unexpectedly)
- Document the determination that CUI is not handled
- Skip Activities 5.2 through 5.6 unless CUI status changes

**Limited CUI (support interactions only):**
- Implement marking and access controls for CUI received during customer support
- Minimize CUI retention — destroy after the support interaction concludes
- Incident reporting still applies at full rigor
- Simplified access list (support team only)

**Full CUI environment (cloud platform processing CUI):**
- Execute all activities as written
- FIPS 140-2 validated crypto modules on all platform components
- Coordinate with PROC-GOV-001 for CMMC alignment
- Coordinate with PROC-GOV-002 for FedRAMP SSP CUI documentation
- Annual third-party assessment of CUI controls

**Air-gapped CUI environments:**
- Physical security controls are paramount
- Media transfer procedures must enforce CUI markings
- Destruction must be performed on-site
- Coordinate with PROC-GOV-011 for deployment-specific CUI requirements

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-004 | Extends — CUI access controls build on base access control process |
| PROC-SEC-005 | Extends — CUI encryption extends base encryption requirements |
| PROC-SEC-003 | Related — incident response includes CUI-specific reporting |
| PROC-GOV-001 | Related — CMMC Level 2 maps to NIST 800-171 CUI controls |
| PROC-GOV-002 | Related — FedRAMP SSP documents CUI handling |
| PROC-GOV-007 | Related — zero trust controls strengthen CUI protection |
| PROC-GOV-011 | Related — air-gapped deployments have additional CUI physical controls |

## 14. Traces

- **Governs:** CUI handling guides, access control lists, incident reports, destruction logs
- **Enforced by:** Quarterly access reviews, CUI training requirements, DIBCAC reporting SLA
- **Related QA:** QA-003 (Defense Contractor Compliance)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

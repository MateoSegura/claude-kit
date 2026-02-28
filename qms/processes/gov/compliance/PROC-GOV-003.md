# PROC-GOV-003: Export Control

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Legal Counsel
**Last Reviewed:** 2026-02-28

## 1. Purpose

Ensure that claude-kit's distribution, deployment, and use comply with U.S. export control regulations. As an AI-powered developer tool with encrypted plugin distribution, claude-kit may be subject to Export Administration Regulations (EAR) and potentially the International Traffic in Arms Regulations (ITAR) when used in defense contexts. This process establishes controls for classification, screening, licensing, and technology control.

## 2. Scope

This process covers export control compliance for:
- The claude-kit CLI and encrypted plugin bundles
- Cloud platform access by non-U.S. persons or entities
- Air-gapped deployment media shipped to international locations
- Technical data shared with international partners or subsidiaries
- AI model integration (Anthropic API) in export-controlled contexts

Excluded:
- Anthropic's own export control compliance for Claude models (Anthropic's responsibility)
- Customer use of claude-kit outputs (customer's export control responsibility)

## 3. Entry Criteria

- [ ] PROC-LC-004 (Implementation) base process is established
- [ ] PROC-LC-006 (Release) base process is established
- [ ] Legal counsel with export control expertise is retained
- [ ] Initial ECCN classification of claude-kit has been performed
- [ ] Denied party screening capability is in place (tool or service subscription)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| EAR Commerce Control List (CCL) | BIS (Bureau of Industry and Security) | Regulatory text |
| USML (United States Munitions List) | DDTC (Directorate of Defense Trade Controls) | Regulatory text |
| Consolidated Screening List | trade.gov | API / CSV |
| Product technical specifications | Engineering team | Markdown / design docs |
| Encryption technical parameters | Security team | Technical documentation |
| Customer and partner entity list | Sales / BD team | CRM export |
| QA-004 (Export Control) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 ECCN Classification

Classify claude-kit components under the Commerce Control List:

**Encryption consideration:** claude-kit uses AES-256-CBC encryption for plugin distribution. Software with encryption functionality is typically classified under ECCN 5D002. Determine whether the encryption exception at EAR 740.17 (License Exception ENC) applies — it generally does for mass-market or publicly available encryption.

**AI consideration:** AI software may fall under ECCN 4D090 (added in 2020 for certain geospatial AI). Evaluate whether claude-kit's AI agent orchestration triggers this classification. For developer tooling that orchestrates a third-party AI API (Anthropic), the classification likely remains under 5D002 or EAR99.

Document the classification rationale with references to specific CCL entries and submit a commodity jurisdiction (CJ) request to BIS if classification is ambiguous.

### 5.2 ITAR Screening

Determine whether any claude-kit functionality or deployment context falls under ITAR jurisdiction:
- Review USML Categories XI (military electronics) and XXI (articles, technical data, defense services)
- If claude-kit is used to develop ITAR-controlled software, the tool itself may not be ITAR-controlled, but the plugins containing domain knowledge about defense articles could be
- For defense-specific plugins (e.g., embedded-zephyr team targeting military platforms), evaluate whether the plugin content constitutes ITAR technical data

If ITAR applies, engage a registered broker and initiate DDTC registration.

### 5.3 Denied Party Screening

Before any distribution, licensing, or support engagement:
- Screen all customers, partners, and end-users against the Consolidated Screening List
- Screen against Entity List, Denied Persons List, Specially Designated Nationals (SDN) list
- Document screening results with timestamp and list version
- Repeat screening at each transaction and on a quarterly batch basis for ongoing relationships

Automate screening using a commercial screening service (e.g., Visual Compliance, Descartes) integrated into the sales and distribution pipeline.

### 5.4 Export License Management

When a license is required (i.e., no exception applies):
- Prepare and submit export license applications to BIS (EAR) or DDTC (ITAR)
- Track license conditions, quantities, expiration dates, and authorized end-users
- Maintain a license register with all active, expired, and returned licenses
- Report any violations or suspected diversions to the appropriate authority

### 5.5 Technology Control Plan (TCP)

For any engagement involving foreign nationals or international access to controlled technology:
- Document what technical data or technology is controlled
- Define access controls (physical and logical) to prevent unauthorized disclosure
- Identify authorized and unauthorized recipients
- Establish secure communication channels for controlled exchanges
- Brief all personnel with access on their TCP obligations

### 5.6 Distribution Channel Controls

Implement controls in the plugin distribution pipeline:
- Geo-blocking for embargoed countries (Cuba, Iran, North Korea, Syria, and others per OFAC)
- IP-based access controls for the cloud platform
- Customer attestation during onboarding confirming end-use and end-user information
- Encryption of all distribution channels (already implemented via AES-256-CBC)

### 5.7 Recordkeeping and Reporting

Maintain records required by EAR (5 years) and ITAR (5 years):
- All classification determinations and rationale
- Screening results for every transaction
- License applications, approvals, denials, and returns
- Technology control plan documents
- Semi-annual and annual reports as required (ENC reports for 740.17)

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| ECCN Classification Memo | `qms/artifacts/gov/` | — | GOV-ECCN-XXX |
| ITAR Screening Determination | `qms/artifacts/gov/` | — | GOV-ITAR-XXX |
| Denied Party Screening Log | `qms/artifacts/gov/` | — | GOV-DPS-XXX |
| Export License Register | `qms/artifacts/gov/` | — | GOV-LIC-XXX |
| Technology Control Plan | `qms/artifacts/gov/` | — | GOV-TCP-XXX |
| Semi-Annual ENC Report | `qms/artifacts/gov/` | — | GOV-ENC-XXX |

## 7. Exit Criteria

- [ ] ECCN classification is documented and reviewed by legal counsel
- [ ] ITAR screening determination is documented
- [ ] Denied party screening is operational and automated
- [ ] Technology control plan is in place for any foreign national access
- [ ] Distribution pipeline has geo-blocking and access controls implemented
- [ ] Recordkeeping system is established with appropriate retention periods

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Classification review | Legal counsel sign-off | ECCN determination documented with CCL references |
| Screening completeness | Audit of screening logs vs. customer list | 100% of customers screened, no gaps |
| TCP review | Security Lead and Legal review | All controlled technology identified and access restricted |
| Distribution controls | Penetration test of geo-blocking | Embargoed country access blocked, documented |
| Annual compliance review | External compliance audit | No findings of unauthorized exports |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Legal Counsel | ECCN classification, ITAR determination, license applications, regulatory interpretation |
| Compliance Officer | Denied party screening, recordkeeping, reporting, training |
| Security Lead | Technology control plan implementation, access control enforcement |
| Engineering Lead | Distribution pipeline controls, geo-blocking implementation |
| Sales Lead | Customer end-use attestation collection, flagging of high-risk transactions |
| Export Control Officer (if designated) | Day-to-day compliance operations, BIS/DDTC liaison |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Screening coverage | Percentage of transactions screened | 100% | Screening tool audit log |
| Classification currency | Time since last ECCN review | < 12 months | Classification register |
| License compliance | Active licenses within conditions | 100% compliant | License register audit |
| Training completion | Personnel with current export control training | 100% of relevant roles | Training records |
| Violation incidents | Number of known or suspected violations | 0 | Incident tracking |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| EAR (15 CFR 730–774) | Part 742 (control reasons), Part 740.17 (ENC exception) | Primary export control regulation |
| ITAR (22 CFR 120–130) | Part 121 (USML), Part 125 (licenses) | Defense article control regulation |
| OFAC Sanctions | 31 CFR 500–599 | Embargoed country and entity restrictions |
| EO 13526 | Classified National Security Information | Classification and handling (if applicable) |
| NIST SP 800-171 | 3.1.22 (control CUI per external agreements) | CUI protection in export-controlled contexts |

## 12. Tailoring Guidance

**EAR99 classification (no significant controls):**
- Skip Activity 5.4 (license management) — no license required for most destinations
- Denied party screening still required
- Maintain ECCN classification documentation for audit purposes
- Annual review of classification suffices

**5D002 with License Exception ENC:**
- File required ENC reports (semi-annual or annual per BIS guidance)
- No individual license needed for most destinations
- Maintain records of all distributions for 5 years
- Re-evaluate classification when encryption parameters change

**ITAR-controlled content (defense-specific plugins):**
- Execute all activities with maximum rigor
- Register with DDTC if not already registered
- All foreign national access requires a Technical Assistance Agreement (TAA) or Manufacturing License Agreement (MLA)
- Implement physical and logical access controls per TCP
- Brief all personnel annually on ITAR obligations

**Air-gapped media shipments:**
- Treat as a deemed export if media leaves U.S. jurisdiction
- Label media with export control markings
- Track chain of custody from creation to delivery
- Coordinate with PROC-GOV-011 for packaging procedures

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-004 | Extends — export classification occurs during implementation |
| PROC-LC-006 | Extends — export controls apply at release and distribution |
| PROC-GOV-001 | Related — CMMC compliance environments may also have export controls |
| PROC-GOV-006 | Related — CUI handling intersects with export-controlled technical data |
| PROC-GOV-011 | Related — air-gap deployment media may be export-controlled |
| PROC-GOV-004 | Related — supply chain assurance must account for export-controlled components |

## 14. Traces

- **Governs:** ECCN classification records, export license register, denied party screening logs
- **Enforced by:** Legal counsel review, automated screening tool, semi-annual BIS reporting
- **Related QA:** QA-004 (Export Control)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

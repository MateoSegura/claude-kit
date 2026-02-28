# PROC-GOV-012: Impact Level Qualification

**Version:** 1.0.0
**Status:** draft
**Category:** deployment
**Layer:** gov
**Maturity:** initial
**Owner:** Compliance Officer
**Last Reviewed:** 2026-02-28

## 1. Purpose

Determine and document the appropriate DoD Impact Level (IL) for claude-kit deployments within Department of Defense cloud environments. The DoD Cloud Computing Security Requirements Guide (CC SRG) defines six impact levels (IL2 through IL6), each with progressively stricter security controls. Correct impact level qualification is a prerequisite for deploying in DoD networks and affects infrastructure selection, authorization scope, and ongoing compliance obligations.

## 2. Scope

This process covers:
- Data categorization for claude-kit workloads in DoD environments
- Impact level determination (IL2, IL4, IL5, IL6)
- DoD CC SRG control mapping beyond FedRAMP baseline
- Provisional Authorization (PA) assessment preparation
- Infrastructure qualification for each impact level

Included:
- Cloud platform hosting selection (commercial cloud, GovCloud, on-premise)
- Data types processed by claude-kit in DoD contexts
- AI model data flow considerations for impact level determination
- Inheritance model for DoD cloud services

Excluded:
- FedRAMP authorization process (covered by PROC-GOV-002)
- Air-gap deployment procedures (covered by PROC-GOV-011)
- Classified systems above IL6 (separate authorization process)

## 3. Entry Criteria

- [ ] PROC-GOV-002 (FedRAMP Authorization) is established (IL2+ requires FedRAMP baseline)
- [ ] DoD customer requirements are documented (contract, task order, or RFP)
- [ ] Data types to be processed are cataloged
- [ ] Cloud infrastructure options are identified
- [ ] DoD CC SRG current version is obtained from DISA

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| DoD CC SRG (current version) | DISA (Defense Information Systems Agency) | PDF |
| CNSSI 1253 (Security Categorization) | CNSS | PDF |
| DoD contract requirements | Contracts team | Contract excerpts |
| Data categorization questionnaire | Customer / internal | Questionnaire responses |
| FedRAMP authorization status | PROC-GOV-002 | Authorization letter / status |
| QA-005 (DoD Impact Levels) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 Data Categorization

Categorize all data types that claude-kit will process, store, or transmit in the DoD environment:

| Data Type | Example in claude-kit Context | Sensitivity |
|-----------|------------------------------|-------------|
| Publicly releasable | Open-source code, public documentation | Low |
| Non-CUI mission data | Non-sensitive project configurations, build logs | Low-Moderate |
| CUI (Controlled Unclassified) | Defense contractor source code, technical specs | Moderate |
| CUI with ITAR controls | Weapons system firmware code, ITAR technical data | Moderate-High |
| National Security Systems data | Data on classified networks | High (beyond scope) |

**claude-kit specific considerations:**
- Plugin knowledge content: May contain CUI if defense-specific (e.g., embedded-zephyr plugins referencing defense platforms)
- AI agent context windows: Temporarily hold customer code that may include CUI
- Session logs: May capture CUI if logging is enabled in CUI environments
- Encrypted plugin bundles: Encryption satisfies at-rest protection but data type still determines IL

### 5.2 Impact Level Determination

Map data categorization to DoD Impact Levels:

| Impact Level | Data Types | Hosting | Authorization |
|--------------|-----------|---------|---------------|
| **IL2** | Non-CUI, publicly releasable, non-critical mission data | Commercial cloud with FedRAMP Moderate | FedRAMP Moderate + SRG overlay |
| **IL4** | CUI, non-national security | GovCloud (AWS GovCloud, Azure Government, etc.) | FedRAMP Moderate + DoD IL4 SRG controls |
| **IL5** | CUI, national security, mission-critical | GovCloud with additional controls | FedRAMP High + DoD IL5 SRG controls |
| **IL6** | Classified (SECRET) | Classified cloud or on-premise | Separate classification authority |

**Decision criteria for claude-kit:**
- If customer code contains no CUI → IL2
- If customer code contains CUI (most DIB scenarios) → IL4 minimum
- If customer code is mission-critical or national security → IL5
- If customer code is classified → IL6 (coordinate with PROC-GOV-011 for air-gap)

Document the determination with:
- Data types identified and their categorization
- Customer concurrence on the categorization
- Impact level selected with rationale
- Any assumptions made during determination

### 5.3 SRG Control Mapping

Map DoD CC SRG controls beyond the FedRAMP baseline:

**IL2 overlay controls (over FedRAMP Moderate):**
- Additional access control requirements for DoD users
- DoD-specific audit logging requirements
- Incident reporting to DoD CSSP (Cybersecurity Service Provider)
- Data sovereignty requirements (CONUS hosting)

**IL4 overlay controls (over FedRAMP Moderate + IL2):**
- Logical separation of DoD tenants from non-DoD tenants
- Background investigation requirements for personnel with data access
- CUI marking and handling per PROC-GOV-006
- Enhanced monitoring and logging
- DoD PKI integration (CAC/PIV authentication)

**IL5 overlay controls (over FedRAMP High + IL4):**
- Physical separation or dedicated infrastructure for DoD workloads
- Cryptographic separation using NSA-approved algorithms
- STIG compliance for all components
- Enhanced personnel security (TS clearance for certain roles)
- DoD network connectivity requirements (NIPRNet/SIPRNet)

For each overlay control:
1. Map to existing organizational controls
2. Identify gaps requiring implementation
3. Document the implementation narrative in SRG format
4. Track gaps in the POA&M

### 5.4 Infrastructure Qualification

Qualify the hosting infrastructure for the determined impact level:

**Cloud Service Provider (CSP) selection:**

| Impact Level | Approved Infrastructure |
|--------------|------------------------|
| IL2 | Any FedRAMP Moderate authorized commercial cloud |
| IL4 | AWS GovCloud, Azure Government, Google Cloud for Government, Oracle Government Cloud |
| IL5 | AWS GovCloud (IL5), Azure Government (IL5), dedicated DoD regions |
| IL6 | AWS Secret Region, Azure Government Secret, on-premise classified |

**Infrastructure verification:**
- Confirm CSP has the required DoD PA (Provisional Authorization) at the target IL
- Verify that the CSP's shared responsibility model aligns with claude-kit's architecture
- Document inherited controls from the CSP
- Identify any control gaps that claude-kit must implement at the application layer

**claude-kit specific infrastructure needs:**
- AI model inference endpoint must be available at the target IL
- Encrypted plugin distribution must function within the CSP environment
- Git-based workflow must be available (may require local git server at IL5/IL6)
- CI/CD pipeline must operate within the boundary (GitHub Actions may not be available at IL5+)

### 5.5 PA Assessment Preparation

Prepare for the DoD Provisional Authorization assessment:

**DISA SRG assessment (for CSP-level authorization):**
- If using an already-authorized CSP, leverage their existing PA
- Document the inheritance relationship in the SSP

**Mission owner authorization (for application-level):**
- Prepare the application-level SSP documenting claude-kit's controls
- Map controls to the appropriate SRG overlay (IL2/IL4/IL5)
- Prepare evidence of control implementation
- Coordinate with the Authorizing Official Designated Representative (AODR)
- Support the assessment team during technical evaluation

**Timeline expectations:**

| Impact Level | Typical PA Timeline | Key Dependencies |
|--------------|--------------------|--------------------|
| IL2 | 3–6 months (after FedRAMP) | FedRAMP Moderate ATO |
| IL4 | 6–12 months | GovCloud deployment, CUI controls |
| IL5 | 12–18 months | FedRAMP High, dedicated infrastructure |
| IL6 | 18–24 months | Classified infrastructure, cleared personnel |

### 5.6 Ongoing IL Compliance

Maintain compliance at the authorized impact level:

- Continuous monitoring per PROC-GOV-010 with SRG-specific requirements
- STIG compliance scanning (for IL4+) on all components
- DoD CSSP incident reporting (in addition to FedRAMP ConMon reporting)
- Annual reassessment with the AO
- Re-evaluation of impact level when data types or mission context change

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Data Categorization Report | `qms/artifacts/gov/` | — | GOV-DCAT-XXX |
| Impact Level Determination Memo | `qms/artifacts/gov/` | — | GOV-IL-XXX |
| SRG Control Mapping | `qms/artifacts/gov/` | — | GOV-SRG-XXX |
| Infrastructure Qualification Report | `qms/artifacts/gov/` | — | GOV-IQR-XXX |
| PA Assessment Package | `qms/artifacts/gov/` | — | GOV-PA-XXX |

## 7. Exit Criteria

- [ ] Data categorization is complete and customer-concurred
- [ ] Impact level is determined and documented with rationale
- [ ] SRG control mapping identifies all overlay controls and gaps
- [ ] Infrastructure is qualified for the target impact level
- [ ] PA assessment package is prepared (or existing CSP PA is leveraged)
- [ ] Ongoing compliance procedures are established

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Data categorization review | Security Lead and customer review | All data types identified and correctly categorized |
| Impact level approval | Customer AO concurrence | Written concurrence on selected impact level |
| Control mapping completeness | Cross-reference with SRG overlay | 100% of overlay controls mapped |
| Infrastructure qualification | CSP PA verification | CSP PA at or above required impact level |
| PA readiness | Internal review of assessment package | All sections complete, evidence current |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Compliance Officer | Owns impact level qualification process, maintains SRG control mapping |
| Security Lead | Conducts data categorization, implements overlay controls |
| DevOps Lead | Qualifies infrastructure, implements STIG compliance |
| Engineering Lead | Supports application-layer control implementation |
| Customer AO/AODR | Approves impact level determination, grants PA |
| DISA Assessor | Evaluates SRG compliance (for IL4+) |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| SRG control coverage | Overlay controls with complete implementation | 100% | Control mapping review |
| STIG compliance rate | Components passing STIG scans | >= 95% (waivers for remainder) | STIG scanner output |
| PA timeline adherence | Actual vs. planned PA milestone dates | Within 30 days of plan | Project timeline |
| Data categorization currency | Time since last categorization review | < 12 months | Categorization log |
| Infrastructure qualification | CSP PA validity | Active and current | CSP PA verification |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| DoD CC SRG | Sections 3–5 (Impact Levels, Control Selection) | Primary DoD cloud authorization guide |
| CNSSI 1253 | Security Categorization | Data categorization methodology |
| NIST SP 800-53 Rev 5 | Full control catalog (baseline varies by IL) | Control framework foundation |
| DoDI 8510.01 | DoD Risk Management Framework | Authorization process for DoD systems |
| DISA STIGs | Various (OS, app, network, database) | Configuration compliance baselines |
| FedRAMP | Moderate and High baselines | Foundation for IL2 and IL4/IL5 |

## 12. Tailoring Guidance

**IL2 (commercial, non-CUI):**
- Simplest path — start here for initial DoD engagements
- FedRAMP Moderate authorization is the primary prerequisite
- Minimal SRG overlay controls beyond FedRAMP
- Commercial cloud infrastructure is acceptable
- AI model access via standard Anthropic API

**IL4 (CUI, most common for DIB):**
- Requires GovCloud infrastructure
- CUI handling per PROC-GOV-006 is mandatory
- CAC/PIV authentication for DoD users
- STIG compliance required for all components
- AI model access must be within GovCloud boundary

**IL5 (mission-critical CUI):**
- Dedicated infrastructure (not multi-tenant with non-DoD)
- FedRAMP High baseline plus SRG overlay
- Enhanced personnel security requirements
- May require NIPRNet connectivity
- AI model deployment within the IL5 boundary is complex — evaluate carefully

**IL6 (classified):**
- Air-gapped deployment per PROC-GOV-011
- Classified cloud or on-premise only
- All personnel must hold appropriate clearances
- Classified data handling procedures (beyond CUI)
- AI model must be deployed within the classified boundary

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-GOV-002 | Extends — DoD IL qualification builds on FedRAMP authorization |
| PROC-GOV-001 | Related — CMMC certification may be required alongside IL qualification |
| PROC-GOV-006 | Related — CUI handling is required for IL4+ |
| PROC-GOV-007 | Related — zero trust alignment supports SRG control implementation |
| PROC-GOV-010 | Related — continuous monitoring must include SRG-specific checks |
| PROC-GOV-011 | Related — IL6 deployments are air-gapped |
| PROC-GOV-013 | Related — customer boundary integration affects IL scoping |
| PROC-LC-006 | Extends — IL qualification gates apply to release management |
| PROC-SP-002 | Extends — quality assurance must include SRG control verification |

## 14. Traces

- **Governs:** Data categorization reports, impact level determination memos, SRG control mappings
- **Enforced by:** DoD AO authorization decision, DISA SRG assessment, annual reassessment
- **Related QA:** QA-005 (DoD Impact Levels)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

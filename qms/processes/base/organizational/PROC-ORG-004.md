# PROC-ORG-004: Risk Management

**Version:** 1.0.0
**Status:** draft
**Category:** organizational
**Layer:** base
**Maturity:** initial
**Owner:** Technical Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Risk Management provides a structured approach to identifying, assessing, mitigating, and monitoring risks that could threaten claude-kit's development, distribution, or operational integrity. claude-kit operates in a risk environment shaped by AI model supplier dependency (Anthropic), encryption-based distribution, defense and federal market requirements, and rapid evolution of the AI developer tools landscape. Without formal risk management, these risks are addressed reactively — after they materialize as incidents — rather than proactively through planned mitigations.

## 2. Scope

**Included:**
- Identification of technical, operational, supply chain, regulatory, and market risks
- Qualitative risk assessment (likelihood and impact scoring)
- Mitigation planning and implementation tracking
- Periodic risk register review and updates
- Risk communication to stakeholders

**Excluded:**
- Financial risk management (investment, cash flow) — outside QMS scope
- Individual project scheduling risk — handled by development planning
- Compliance-specific risk assessments (handled by PROC-GOV-001, PROC-GOV-002)

## 3. Entry Criteria

- [ ] A new project phase, feature, or market expansion is being planned
- [ ] A scheduled risk review interval has arrived (quarterly)
- [ ] An incident or near-miss has occurred that reveals a previously unidentified risk
- [ ] An external event has changed the risk landscape (vendor announcement, regulatory change, security advisory)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Architecture decisions | `docs/architecture/decisions/` (ADR-XXX) | Structured decision records |
| Quality attributes | `docs/quality/` (QA-XXX) | Constraint documents |
| Incident records | `docs/operations/incidents/` (INC-XXX) | Incident post-mortems |
| Market analysis | `docs/research/` | Research papers |
| Supplier information | Anthropic documentation, API changelogs | External content |
| Measurement data | `docs/benchmarks/` (BM-XXX) | Trend reports |
| Security assessment | PROC-SEC-001, PROC-SEC-002 outputs | Vulnerability reports |

## 5. Activities

### 5.1 Risk Identification

Systematically identify risks across six categories relevant to claude-kit:

**Technical risks:**
- Claude model API breaking changes that invalidate agent definitions
- Plugin encryption algorithm deprecation or vulnerability
- Single-file CLI architecture scaling limits
- Self-hosted CI runner failure or compromise

**Supply chain risks:**
- Anthropic API availability or deprecation (primary AI supplier)
- Anthropic pricing changes that affect product economics
- GitHub Actions service disruption (CI/CD dependency)
- GitHub Container Registry (ghcr.io) availability for devcontainer images

**Regulatory risks:**
- CMMC certification requirement changes for defense market
- FedRAMP authorization changes for federal market
- AI transparency regulations affecting Claude-based tooling
- Export control restrictions on AI-powered development tools

**Operational risks:**
- Encryption key compromise or loss
- CI pipeline failure causing blocked releases
- Nightly/weekly automation producing false positives that erode trust

**Market risks:**
- Competing tools (Cursor, Windsurf, Cline) adding plugin management features
- Claude model quality regression affecting plugin agent effectiveness
- Customer churn due to tool switching costs

**People risks:**
- Bus factor for encryption key knowledge
- Knowledge concentration in AI agent training (rules and skills)

### 5.2 Risk Assessment

For each identified risk, assess:

- **Likelihood:** Low (unlikely in next 12 months), Medium (possible in next 12 months), High (probable in next 6 months)
- **Impact:** Low (minor inconvenience, workaround available), Medium (significant disruption, manual intervention needed), High (critical — data loss, security breach, or service outage)
- **Risk score:** Likelihood x Impact (L/M/H matrix)
- **Velocity:** How quickly the risk could materialize once triggered (immediate, days, weeks)

Maintain a risk register as a markdown table documenting each risk with its assessment.

### 5.3 Mitigation Planning

For each medium or high risk score, define a mitigation strategy:

- **Avoid:** Eliminate the risk source entirely (e.g., remove the dependency)
- **Mitigate:** Reduce likelihood or impact through controls (e.g., backup encryption keys, multi-vendor strategy)
- **Transfer:** Shift the risk to a third party (e.g., insurance, SLA with supplier)
- **Accept:** Consciously accept the risk with documented rationale (only for low-impact risks)

Each mitigation must have: an owner, a target implementation date, and a verification method.

### 5.4 Risk Monitoring

Quarterly, review the risk register:
- Have any risk assessments changed? (Likelihood or impact shifted)
- Have new risks emerged from incidents, market changes, or architecture decisions?
- Are mitigation controls still effective? (Verify through measurement data)
- Can any risks be closed? (No longer applicable due to architecture changes or market shifts)

Triggered reviews occur when: an incident record (INC-XXX) reveals a new risk, Anthropic announces a significant API change, or a regulatory update affects target markets.

### 5.5 Risk Communication

Communicate risk status to stakeholders:
- Include top risks in quarterly trend reports (PROC-ORG-002)
- Flag high-risk items in PR descriptions when changes affect risk posture
- Update ADR documents when architecture decisions are made to mitigate identified risks

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Risk register | `docs/quality/` or `qms/` (organizational) | — | — |
| Risk assessment records | Embedded in risk register | — | — |
| Mitigation plans | Embedded in risk register | — | — |
| Quality attributes (risk-related) | `docs/quality/` | `quality-attribute.md.tmpl` | QA-XXX |

## 7. Exit Criteria

- [ ] All identified risks are recorded in the risk register with likelihood, impact, and velocity assessments
- [ ] Every medium and high risk has a documented mitigation strategy with an assigned owner
- [ ] Risk register has been reviewed and dated within the last 90 days
- [ ] New risks from recent incidents or external events have been incorporated

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Risk coverage | Review risk categories against the six categories in Activity 5.1 | At least one risk identified per category; no category left blank |
| Mitigation completeness | Audit medium/high risks in register | 100% of medium/high risks have a mitigation strategy, owner, and target date |
| Assessment currency | Check risk register review date | Last review within 90 days |
| Mitigation effectiveness | Cross-reference mitigations with incident records | No incident caused by a risk that had an "implemented" mitigation status |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Technical Lead | Owns the risk register; leads quarterly risk reviews; assigns mitigation owners |
| Security Lead | Identifies and assesses security-specific risks; validates security mitigation effectiveness |
| DevOps Lead | Identifies and assesses operational and CI/CD risks; implements operational mitigations |
| Product Lead | Identifies and assesses market and regulatory risks; communicates risk posture to stakeholders |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Risk register completeness | Percentage of identified risks with full assessment (likelihood, impact, velocity, mitigation) | 100% | Audit risk register |
| Mitigation implementation rate | Percentage of planned mitigations implemented by target date | >= 80% | Track mitigation status in register |
| Risk materialization rate | Number of incidents caused by previously identified risks per quarter | Decreasing trend | Cross-reference INC-XXX records with risk register |
| Review cadence compliance | Percentage of quarterly reviews conducted on schedule | 100% | Track review dates |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO 31000 | Risk management principles and framework | Overall risk management methodology |
| ISO/IEC 12207:2017 | 7.2.6 Risk management | Software lifecycle risk management |
| NIST SP 800-30 | Risk assessment | Risk assessment methodology for information systems |
| NIST SP 800-218 | PO.1.1 | Security risk identification as part of secure development |
| CMMI | RSKM (Risk Management) | Organizational risk management capability |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Maintain a simple risk register as a markdown table with columns: Risk, Likelihood (L/M/H), Impact (L/M/H), Mitigation, Status. Review it when starting a new major feature or after an incident. Focus on the top 5 highest-impact risks rather than comprehensive coverage.

**Full ceremony (team targeting defense/federal):** Execute all activities. Maintain a formal risk register with quantitative scoring. Conduct quarterly risk review meetings. Integrate with CMMC and FedRAMP risk assessment requirements. Track mitigation implementation via project management tooling.

**When to simplify:** For internal development milestones that do not change the product's risk posture (documentation updates, internal tooling improvements), skip risk review. Always perform risk review before releases that change encryption, distribution, or authentication mechanisms.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-ORG-005 | Related: supplier risks (Anthropic dependency) overlap with supplier management concerns |
| PROC-SEC-001 | Feeds into: security risks drive secure development practices |
| PROC-SEC-002 | Feeds into: vulnerability findings update risk assessments |
| PROC-SEC-003 | Related: realized security risks become security incidents |
| PROC-LC-001 | Receives from: market analysis identifies competitive and regulatory risks |
| PROC-LC-008 | Feeds into: risk trends contribute to improvement prioritization |
| PROC-ORG-002 | Related: measurement data informs risk likelihood assessments |

## 14. Traces

- **Governs:** Risk register, `docs/quality/` (QA-XXX quality attributes that express risk constraints)
- **Enforced by:** Quarterly review schedule (manual); incident-triggered reviews (reactive)
- **Related QA:** Supplier dependency resilience, encryption integrity, regulatory compliance readiness

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — establishes formal risk management for claude-kit's unique risk profile |

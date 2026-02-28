# PROC-GOV-007: Zero Trust Alignment

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Align claude-kit's security architecture with federal Zero Trust principles as mandated by OMB M-22-09 and NIST SP 800-207. Federal agencies are required to adopt Zero Trust Architecture (ZTA) by the end of FY2024, and their vendors are increasingly expected to support zero trust principles in their products. This process ensures claude-kit can operate within customer zero trust environments and that the platform's own security posture reflects zero trust principles.

## 2. Scope

This process covers zero trust alignment for:
- claude-kit cloud platform infrastructure and services
- Plugin distribution and update mechanisms
- AI agent execution and tool access controls
- Customer integration points (API, CLI, web interface)
- Internal development and operations environments

Included:
- Five pillars of Zero Trust per CISA model: Identity, Devices, Networks, Applications/Workloads, Data
- Zero Trust maturity progression from Traditional through Optimal

Excluded:
- Customer network architecture (customer's ZTA responsibility)
- Anthropic API infrastructure zero trust posture (Anthropic's responsibility)

## 3. Entry Criteria

- [ ] PROC-SEC-004 (Access Control) base process is established
- [ ] Identity provider (IdP) is selected and operational
- [ ] Network architecture diagrams are current
- [ ] Application inventory is complete with data flow documentation
- [ ] Zero Trust maturity baseline assessment is complete

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| NIST SP 800-207 (Zero Trust Architecture) | NIST | PDF |
| OMB M-22-09 (Federal Zero Trust Strategy) | OMB | Memorandum |
| CISA Zero Trust Maturity Model v2 | CISA | PDF |
| DoD Zero Trust Reference Architecture v2 | DoD CIO | PDF |
| Current network and identity architecture | DevOps team | Diagrams |
| Application and data inventory | Engineering team | Spreadsheet |

## 5. Activities

### 5.1 Zero Trust Maturity Assessment

Assess current posture against the CISA Zero Trust Maturity Model across five pillars:

**Identity pillar:**
- Current: Password-based authentication with optional MFA
- Target: Phishing-resistant MFA (FIDO2/WebAuthn), continuous identity validation
- Assessment: Evaluate identity provider capabilities, session management, risk-based authentication

**Devices pillar:**
- Current: Developer workstations with basic endpoint protection
- Target: Device compliance verification before granting access, EDR on all endpoints
- Assessment: Inventory managed vs. unmanaged devices, evaluate MDM/EDR coverage

**Networks pillar:**
- Current: Perimeter-based security with VPN for remote access
- Target: Microsegmented networks, encrypted east-west traffic, ZTNA replacing VPN
- Assessment: Map network segments, identify lateral movement paths, evaluate ZTNA readiness

**Applications/Workloads pillar:**
- Current: Application-level access control with role-based permissions
- Target: Continuous authorization, application-layer encryption, immutable workloads
- Assessment: Review application authentication, evaluate container security, assess CI/CD pipeline integrity

**Data pillar:**
- Current: Encryption at rest and in transit, basic data classification
- Target: Automated data classification, DLP, granular data access policies
- Assessment: Inventory data stores, evaluate classification coverage, assess DLP capabilities

Produce a maturity scorecard rating each pillar as Traditional, Initial, Advanced, or Optimal.

### 5.2 Identity and Access Management Enhancement

Implement zero trust identity controls:

**Phishing-resistant MFA:**
- Deploy FIDO2/WebAuthn for all user-facing services
- Eliminate SMS/email-based second factors (phishable)
- Require hardware security keys for administrative access

**Continuous authentication:**
- Implement session risk scoring based on device posture, location, and behavior
- Re-authenticate for sensitive operations (plugin distribution, configuration changes)
- Reduce session lifetimes and implement step-up authentication

**Service identity:**
- Implement mutual TLS (mTLS) for service-to-service communication
- Use short-lived certificates (SPIFFE/SPIRE or equivalent)
- Eliminate long-lived API keys and static credentials

### 5.3 Microsegmentation

Implement network microsegmentation to limit lateral movement:

**Cloud platform segmentation:**
- Separate the plugin distribution service, AI agent orchestration, and management plane into distinct network segments
- Apply deny-by-default firewall rules between segments
- Allow only explicitly authorized traffic flows

**Container-level segmentation:**
- Network policies restricting pod-to-pod communication in Kubernetes
- Sidecar proxies (Istio/Envoy) for mTLS and traffic policy enforcement
- Egress controls limiting outbound connections to known destinations (Anthropic API, GitHub, etc.)

**Air-gapped environment segmentation:**
- Physical network isolation (already achieved by air gap)
- Internal segmentation within the air-gapped enclave
- DMZ for controlled media import/export

### 5.4 Continuous Authorization for AI Agents

Apply zero trust principles to AI agent execution within claude-kit:

**Agent tool access:**
- claude-kit's hook system already implements pre-call authorization for agent tool use
- Enhance hooks with dynamic policy evaluation based on context (project, user role, risk level)
- Log all authorization decisions for audit

**Plugin loading authorization:**
- Verify plugin integrity (hash check) before loading
- Validate plugin signature against authorized publisher list
- Check plugin version against known-vulnerable versions
- Enforce companion declarations (only load declared companions)

**Session-scoped access:**
- Each AI agent session operates with minimal necessary permissions
- Tool access is restricted by the agent's role (engineer, grader, tester, debugger)
- File system access is scoped to the active project directory

### 5.5 Zero Trust Network Access (ZTNA) Implementation

Replace traditional VPN with ZTNA for remote access:

**Cloud platform access:**
- Deploy a ZTNA broker (e.g., Cloudflare Access, Zscaler ZPA, or equivalent)
- Authenticate users and devices before granting application access
- Apply granular policies based on identity, device posture, and context
- Hide the network topology from end users

**Developer access:**
- ZTNA for internal development tools (CI/CD, artifact registry, monitoring)
- Device compliance checks (OS patch level, EDR running, disk encryption enabled)
- Just-in-time access for privileged operations with automatic expiry

**Customer access:**
- API authentication using OAuth 2.0 with PKCE
- Rate limiting and anomaly detection at the API gateway
- Mutual TLS for system-to-system integrations

### 5.6 Data Protection Alignment

Implement zero trust data protection controls:

**Data classification:**
- Classify all data stores by sensitivity (public, internal, confidential, CUI)
- Apply data loss prevention (DLP) policies based on classification
- Tag data with classification labels (coordinate with PROC-GOV-006 for CUI markings)

**Data access policies:**
- Attribute-based access control (ABAC) for data stores
- Data access logging and anomaly detection
- Encryption key management with hardware security modules (HSMs) for high-sensitivity data

**AI-specific data controls:**
- Context window isolation between customers
- Session data retention policies aligned with customer agreements
- Data residency controls for jurisdiction-sensitive deployments

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Zero Trust Maturity Scorecard | `qms/artifacts/gov/` | — | GOV-ZT-XXX |
| Zero Trust Architecture Document | `qms/artifacts/gov/` | — | GOV-ZTA-XXX |
| Microsegmentation Policy | `qms/artifacts/gov/` | — | GOV-SEG-XXX |
| ZTNA Deployment Plan | `qms/artifacts/gov/` | — | GOV-ZTNA-XXX |
| Data Classification Inventory | `qms/artifacts/gov/` | — | GOV-DCI-XXX |

## 7. Exit Criteria

- [ ] Zero trust maturity assessment is complete with baseline scores
- [ ] Phishing-resistant MFA is deployed for all user-facing services
- [ ] Microsegmentation is implemented for cloud platform components
- [ ] ZTNA replaces VPN for remote access
- [ ] Data classification is applied to all data stores
- [ ] AI agent authorization is enhanced with dynamic policy evaluation

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Maturity assessment | Independent review of scorecard | All pillars at least "Initial" maturity |
| MFA deployment | Authentication system audit | Zero non-MFA access paths for production |
| Microsegmentation | Network penetration test | No unauthorized lateral movement paths |
| ZTNA coverage | Access audit of remote users | 100% of remote access through ZTNA |
| Data classification | Sample audit of data stores | 100% of data stores classified and labeled |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns zero trust program, conducts maturity assessment, defines policies |
| DevOps Lead | Implements microsegmentation, deploys ZTNA, configures identity infrastructure |
| Engineering Lead | Implements AI agent authorization enhancements, supports application-layer controls |
| CISO | Approves zero trust architecture, prioritizes pillar investments |
| Compliance Officer | Maps zero trust controls to FedRAMP and CMMC requirements |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| ZT maturity score | Aggregate maturity across five pillars | "Advanced" in all pillars within 24 months | Annual maturity assessment |
| MFA adoption | Users with phishing-resistant MFA | 100% | IdP reporting |
| Microsegmentation coverage | Network segments with deny-by-default policies | 100% | Network policy audit |
| ZTNA adoption | Remote access sessions through ZTNA (vs. VPN) | 100% | Access logs |
| Authorization denial rate | Percentage of access requests denied by dynamic policy | Track trend (not a fixed target) | Authorization logs |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-207 | Sections 2–4 (ZTA tenets, deployment models) | Zero trust architecture reference |
| OMB M-22-09 | All sections | Federal zero trust strategy mandate |
| CISA Zero Trust Maturity Model v2 | Five pillars, four maturity levels | Maturity assessment framework |
| DoD Zero Trust Reference Architecture v2 | Seven pillars | DoD-specific zero trust guidance |
| NIST SP 800-53 Rev 5 | AC-2, AC-3, AC-17, IA-2, IA-8, SC-7, SC-8 | Security controls aligned with ZTA |
| EO 14028 | Section 3 (Modernizing Federal Cybersecurity) | Executive mandate for zero trust adoption |

## 12. Tailoring Guidance

**Cloud-only deployment (no air gap):**
- Focus on network microsegmentation and ZTNA
- Leverage cloud-native zero trust services (AWS VPC, Azure NSG, Cloudflare Access)
- Container-level segmentation using Kubernetes network policies
- Full telemetry and continuous monitoring

**Air-gapped deployment:**
- Physical isolation provides the network pillar inherently
- Focus on identity, device, and data pillars
- Implement internal segmentation within the air-gapped enclave
- Device compliance enforcement via local MDM (no cloud-based EDR)

**Small team / early stage:**
- Prioritize identity pillar first (MFA, IdP, SSO)
- Implement basic microsegmentation at the VPC/subnet level
- ZTNA can be phased — start with administrative access, expand to all users
- Data classification can start with manual labeling, automate later

**Full federal compliance (OMB M-22-09):**
- Execute all activities with target maturity "Advanced" or higher
- Integrate with agency ICAM (Identity, Credential, and Access Management) where required
- Support PIV/CAC authentication for DoD customers
- Quarterly maturity reassessment and reporting

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-004 | Extends — zero trust enhances base access control with continuous authorization |
| PROC-GOV-001 | Related — CMMC AC domain aligns with zero trust identity controls |
| PROC-GOV-002 | Related — FedRAMP requires access control and network security controls |
| PROC-GOV-006 | Related — CUI protection benefits from zero trust data controls |
| PROC-GOV-010 | Related — continuous monitoring provides telemetry for zero trust decisions |
| PROC-GOV-011 | Related — air-gapped deployments have unique zero trust considerations |

## 14. Traces

- **Governs:** Zero trust maturity scorecards, architecture documents, segmentation policies
- **Enforced by:** Annual maturity assessment, continuous monitoring telemetry, access policy enforcement
- **Related QA:** (Cross-cutting — supports QA-001 through QA-003 security posture requirements)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

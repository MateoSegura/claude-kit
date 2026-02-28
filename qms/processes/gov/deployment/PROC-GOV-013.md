# PROC-GOV-013: Customer Boundary Integration

**Version:** 1.0.0
**Status:** draft
**Category:** deployment
**Layer:** gov
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Define the process for documenting and managing the authorization boundary between claude-kit and customer environments. In federal and defense contexts, every system must have a clearly defined authorization boundary, and where systems interconnect, the responsibilities for security controls must be explicitly allocated. This process establishes the shared responsibility matrix, boundary documentation, customer SSP integration, and inheritance mapping required for multi-party authorization.

## 2. Scope

This process covers:
- Shared responsibility model between claude-kit (vendor) and customers
- Authorization boundary documentation for cloud and air-gapped deployments
- Customer SSP integration — helping customers incorporate claude-kit into their authorization packages
- Control inheritance mapping — documenting which controls customers inherit from claude-kit
- Interconnection agreements (ISA/MOU) for system-to-system connections

Included:
- All deployment models (cloud SaaS, air-gapped on-premise)
- All compliance frameworks (FedRAMP, CMMC, SOC 2)
- Customer-facing boundary documentation
- Vendor-customer responsibility delineation for AI model access

Excluded:
- Claude-kit internal security architecture (covered by PROC-SEC-001 through 005)
- Customer internal security controls (customer responsibility)
- Anthropic-to-claude-kit boundary (covered by vendor risk assessment in PROC-GOV-004)

## 3. Entry Criteria

- [ ] PROC-GOV-001 (CMMC Compliance) is established
- [ ] Authorization boundary for claude-kit's cloud platform is documented
- [ ] Customer deployment model is identified (cloud SaaS or air-gapped)
- [ ] Customer's compliance requirements are understood (FedRAMP, CMMC, etc.)
- [ ] Customer's existing authorization status is known

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| claude-kit System Security Plan (SSP) | PROC-GOV-002 | Document |
| claude-kit authorization boundary diagrams | Architecture team | Diagrams |
| Customer compliance requirements | Customer security team | Requirements document |
| Customer SSP (existing) | Customer | Document |
| FedRAMP Customer Responsibility Matrix (CRM) template | FedRAMP PMO | Spreadsheet |
| NIST SP 800-47 (Interconnecting IT Systems) | NIST | PDF |

## 5. Activities

### 5.1 Shared Responsibility Matrix Development

Create a comprehensive shared responsibility matrix documenting control ownership:

**Responsibility categories:**
- **claude-kit (vendor) responsibility:** Controls that claude-kit fully implements and maintains
- **Customer responsibility:** Controls that the customer must implement in their environment
- **Shared responsibility:** Controls where both parties have obligations
- **Inherited:** Controls that the customer inherits from claude-kit's authorization

**Matrix structure (by NIST 800-53 control family):**

| Control Family | Example Control | claude-kit | Customer | Shared | Notes |
|---------------|-----------------|------------|----------|--------|-------|
| Access Control (AC) | AC-2 Account Management | Platform accounts | Customer user accounts | MFA enforcement | claude-kit provides MFA capability; customer enables it |
| Audit (AU) | AU-2 Audit Events | Platform audit logs | Customer activity logging | Log review | claude-kit logs agent activity; customer reviews |
| Configuration (CM) | CM-6 Configuration Settings | Platform configuration | Customer project config | Baseline enforcement | STIG-compliant platform; customer follows deployment guide |
| Identification (IA) | IA-2 Identification | Platform authentication | Customer identity federation | SSO integration | claude-kit supports SAML/OIDC; customer configures IdP |
| Incident Response (IR) | IR-6 Incident Reporting | Platform incidents | Customer environment incidents | Joint notification | claude-kit reports platform incidents; customer reports their own |
| System/Comm (SC) | SC-8 Transmission Confidentiality | TLS for platform APIs | TLS for customer networks | End-to-end encryption | claude-kit encrypts in transit; customer ensures their network does too |

Develop the full matrix covering all NIST 800-53 families relevant to the customer's authorization baseline.

### 5.2 Authorization Boundary Documentation

Document the technical boundary between claude-kit and customer environments:

**Cloud SaaS deployment boundary:**
```
Customer Environment          │  claude-kit Platform              │  Anthropic API
─────────────────────────────│──────────────────────────────────│─────────────────
Customer network              │  API gateway                      │  Model inference
Customer workstations         │  Plugin distribution service      │  
Customer code repositories    │  AI agent orchestration           │
Customer CI/CD pipelines      │  Session management               │
                              │  Encrypted plugin storage         │
                              │  Audit logging                    │
```

**Air-gapped deployment boundary:**
```
Customer Air-Gapped Enclave                    │  Vendor Connected Environment
──────────────────────────────────────────────│────────────────────────────
Customer network (isolated)                    │  Update packaging
claude-kit CLI (installed locally)             │  Plugin encryption
Decrypted plugins (local storage)              │  Release management
Local AI model endpoint (if on-premise)        │  Vendor support
Customer code and data                         │
```

Document:
- All connection points between boundaries
- Data flows across boundaries (type, direction, protocol, encryption)
- Authentication mechanisms at each boundary crossing
- Monitoring and logging at boundary interfaces

### 5.3 Customer SSP Integration Support

Help customers incorporate claude-kit into their System Security Plan:

**For customers pursuing FedRAMP authorization:**
- Provide a "FedRAMP Customer Package" containing:
  - Customer Responsibility Matrix (CRM) in FedRAMP format
  - System interconnection diagram
  - Data flow diagrams showing claude-kit integration
  - Inherited control narratives that customers can reference in their SSP
  - Contact information for claude-kit security team

**For customers pursuing CMMC certification:**
- Provide a "CMMC Integration Guide" containing:
  - Mapping of claude-kit controls to CMMC practices
  - Identification of practices the customer inherits from claude-kit
  - Practices requiring joint implementation
  - Evidence that claude-kit provides for customer C3PAO assessment
  - Shared POA&M items (if any)

**For customers with existing SOC 2:**
- Provide a "Vendor SOC 2 Bridge Document" containing:
  - How claude-kit's SOC 2 report covers Trust Services Criteria
  - Gaps that the customer must address independently
  - Complementary user entity controls (CUECs) from claude-kit's SOC 2 report

### 5.4 Control Inheritance Mapping

Document which controls customers can inherit from claude-kit's authorization:

**Fully inheritable controls (customer does not need to implement):**
- Platform infrastructure security (physical, network, hypervisor)
- Platform encryption at rest (AES-256-CBC for plugins)
- Platform-level audit logging
- Platform vulnerability management
- Platform change management (CI/CD pipeline security)

**Partially inheritable controls (customer inherits platform portion, implements their part):**
- Access control: Platform provides MFA capability; customer configures authentication policy
- Configuration management: Platform provides secure defaults; customer applies to their projects
- Incident response: Platform provides incident detection; customer defines response for their data

**Non-inheritable controls (customer must implement independently):**
- Customer personnel security (background checks, training)
- Customer network security (firewall, segmentation)
- Customer physical security
- Customer data classification (beyond what claude-kit categorizes)
- Customer media protection (for their own media)

Map inheritance at the individual control level using the FedRAMP inheritance model (Full, Partial, None).

### 5.5 Interconnection Agreements

Establish formal interconnection agreements where required:

**Interconnection Security Agreement (ISA):**
- Required when claude-kit connects to a federal information system
- Documents: system names, connection type, data types, security controls, points of contact
- Reviewed and signed by both parties' AOs (Authorizing Officials)
- Renewed annually or upon significant change

**Memorandum of Understanding (MOU):**
- For less formal arrangements or pre-ATO planning
- Documents: roles, responsibilities, security expectations, escalation procedures
- May serve as the precursor to a formal ISA

**Contents of ISA/MOU:**

| Section | Content |
|---------|---------|
| System Identification | Names, FISMA IDs, impact levels for both systems |
| Connection Description | Type (API, VPN, data diode), protocols, ports |
| Data Description | Types, sensitivity, direction of flow |
| Security Controls | Controls at the connection point, monitoring, incident response |
| Roles and Responsibilities | Points of contact, escalation paths |
| Service Level Agreement | Availability, response times, maintenance windows |
| Review and Termination | Review cadence, conditions for disconnection |

### 5.6 Boundary Change Management

Manage changes that affect the authorization boundary:

**Triggers for boundary review:**
- New data type processed by claude-kit
- New integration point with customer systems
- Architecture change affecting the boundary (new service, new API)
- Customer authorization level change (e.g., upgrading from IL2 to IL4)
- New compliance requirement (e.g., customer now requires CMMC)

**Change process:**
1. Identify the boundary change
2. Assess impact on shared responsibility matrix and inheritance mapping
3. Update boundary documentation and diagrams
4. Notify affected customers
5. Revise ISA/MOU if applicable
6. Submit significant change request to AO if FedRAMP-authorized (per PROC-GOV-010)

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Shared Responsibility Matrix | `qms/artifacts/gov/` | FedRAMP CRM template | GOV-SRM-XXX |
| Authorization Boundary Diagrams | `qms/artifacts/gov/` | — | GOV-ABD-XXX |
| Customer Integration Packages | `qms/artifacts/gov/` | — | GOV-CIP-XXX |
| Control Inheritance Map | `qms/artifacts/gov/` | — | GOV-CIM-XXX |
| Interconnection Security Agreement | `qms/artifacts/gov/` | ISA template | GOV-ISA-XXX |

## 7. Exit Criteria

- [ ] Shared responsibility matrix is complete for all NIST 800-53 families
- [ ] Authorization boundary is documented with diagrams and data flow descriptions
- [ ] Customer integration packages are prepared for FedRAMP, CMMC, and SOC 2
- [ ] Control inheritance mapping is complete at the individual control level
- [ ] ISA/MOU template is prepared and available for customer engagements
- [ ] Boundary change management process is documented and understood

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| SRM completeness | Cross-reference with NIST 800-53 catalog | All families addressed with clear ownership |
| Boundary diagram accuracy | Architecture team review | Diagrams match current deployment architecture |
| Customer package review | Security Lead and Legal review | Packages are accurate, complete, and legally reviewed |
| Inheritance mapping validation | Cross-reference with claude-kit SSP | Inherited controls match SSP implementation narratives |
| ISA template review | Legal and CISO review | Template covers all required sections |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns boundary documentation, develops SRM, maps control inheritance |
| Architecture Lead | Maintains boundary diagrams, documents data flows |
| Compliance Officer | Prepares customer integration packages, manages ISA/MOU lifecycle |
| Legal Counsel | Reviews ISA/MOU terms, validates shared responsibility language |
| Customer Success Lead | Delivers integration packages to customers, facilitates boundary discussions |
| Customer Security Team | Reviews and accepts SRM, signs ISA/MOU, integrates into their SSP |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| SRM currency | Time since last SRM update | < 6 months | Document review log |
| Customer package delivery | Time from customer request to package delivery | <= 5 business days | Customer request tracker |
| ISA completion rate | Active connections with signed ISAs | 100% | ISA register |
| Boundary change response | Time from change detection to documentation update | <= 30 days | Change log |
| Customer satisfaction | Customer feedback on boundary documentation clarity | >= 4/5 | Customer survey |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-47 Rev 1 | Managing the Security of Information Exchanges | Interconnection agreement guidance |
| NIST SP 800-53 Rev 5 | CA-3 (System Interconnections), SA-9 (External System Services) | Interconnection and external service controls |
| FedRAMP | Customer Responsibility Matrix requirements | FedRAMP CRM format and content |
| CMMC 2.0 | SC.L2-3.13.1 (Boundary Protection) | Network boundary controls |
| NIST SP 800-171 Rev 2 | 3.13.1, 3.13.2 (System Communications Protection) | CUI boundary protection |
| DoDI 8510.01 | Authorization boundary definition | DoD RMF boundary requirements |

## 12. Tailoring Guidance

**Cloud SaaS with SOC 2 customers only:**
- Simplified shared responsibility — standard SaaS vendor model
- No ISA required — standard terms of service cover the relationship
- Customer integration package limited to SOC 2 bridge document and CUECs
- Boundary documentation focuses on API and web interface access points

**Cloud SaaS with federal customers (FedRAMP):**
- Full shared responsibility matrix in FedRAMP CRM format
- Customer integration package with inherited control narratives
- ISA for each connected federal information system
- Boundary diagrams per FedRAMP SSP requirements

**Air-gapped deployment:**
- Boundary is primarily physical — the air gap itself is the boundary control
- Shared responsibility shifts heavily to the customer (they own the infrastructure)
- claude-kit responsibility is limited to: software quality, encryption effectiveness, update package integrity
- Customer integration package focuses on installation validation and update procedures
- ISA may not apply if no network connection exists (but MOU for the vendor relationship still recommended)

**Multi-tenant (single claude-kit instance, multiple customers):**
- Each customer needs their own boundary documentation
- Logical separation evidence is critical (tenant isolation)
- Shared responsibility matrix must clearly delineate tenant-to-tenant isolation
- Extra attention to data flow diagrams showing no cross-tenant data leakage

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-GOV-001 | Extends — customer boundary affects CMMC assessment scope |
| PROC-GOV-002 | Related — FedRAMP CRM is a key output of this process |
| PROC-GOV-006 | Related — CUI handling at the boundary is a critical control |
| PROC-GOV-011 | Related — air-gapped deployment has distinct boundary model |
| PROC-GOV-012 | Related — impact level affects boundary control requirements |
| PROC-GOV-010 | Related — boundary monitoring is part of continuous monitoring |
| PROC-SEC-004 | Extends — access control at the boundary crossing |
| PROC-LC-007 | Extends — deployment operations must account for customer boundaries |

## 14. Traces

- **Governs:** Shared responsibility matrices, boundary diagrams, customer integration packages, ISAs/MOUs
- **Enforced by:** Annual ISA review, boundary change management process, customer feedback
- **Related QA:** (Cross-cutting — supports QA-001 through QA-003 by defining vendor vs. customer obligations)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |

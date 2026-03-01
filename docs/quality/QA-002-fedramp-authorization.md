# QA-002 — FedRAMP Authorization

**Status:** draft
**Priority:** should
**Category:** compliance
**Governing Process:** PROC-SP-002 (Quality Assurance)

## Context

FedRAMP (Federal Risk and Authorization Management Program) is a
government-wide program that provides a standardized approach to security
assessment, authorization, and continuous monitoring for cloud services used by
federal agencies. Any cloud service provider that stores, processes, or
transmits federal data must be FedRAMP-authorized.

claude-kit's SaaS offering (REQ-009) will need FedRAMP authorization if any
federal agency wants to use it directly. Even if deferred initially, every
federal sales cycle will ask "when?" — having a timeline is a competitive
advantage. The on-prem deployment model (QA-008) is exempt since it does not
operate as a cloud service.

FedRAMP 20x (rolling out through 2026) is replacing the traditional
documentation-heavy process with continuous compliance via machine-readable Key
Security Indicators (KSIs). Phase 3 formalization expected FY26 Q3–Q4. Timing
the FedRAMP journey to align with 20x significantly reduces the burden.

## Constraint

The SaaS cloud platform must satisfy FedRAMP controls at the appropriate impact
level. FedRAMP is built on NIST 800-53 Rev 5.

| Impact Level | Controls | Data Types | Likely Target |
|-------------|----------|------------|---------------|
| **Low** | ~125 | Public information | Not applicable |
| **Moderate** | ~325 | Controlled but unclassified (majority of federal systems) | Initial target |
| **High** | ~421 | High-impact data where loss causes severe harm | Future if needed |

### Non-Negotiable Technical Requirements

1. **FIPS 140-2/140-3 validated cryptographic modules** for all encryption —
   the current `_get_key()` approach with OpenSSL satisfies this if using a
   FIPS-validated OpenSSL build, but this must be verified
2. **Continuous monitoring** — monthly vulnerability scans, annual penetration
   testing, real-time incident detection
3. **Multi-tenant isolation** — FedRAMP permits multi-tenant at Moderate and
   High with controls ensuring isolation (NIST 800-53 SC-7)
4. **U.S. data residency** — FedRAMP High requires continental U.S. data centers
5. **3PAO assessment** — a Third-Party Assessment Organization must independently
   evaluate the system

## Architectural Impact

- The cloud platform must be deployable on FedRAMP-authorized infrastructure
  (AWS GovCloud, Azure Government, or Google Cloud for Government)
- All AI API calls route through infrastructure that satisfies FedRAMP boundary
  requirements — if Anthropic's API is not FedRAMP-authorized, this creates a
  boundary issue
- Logging, monitoring, and incident response capabilities must meet NIST 800-53
  AU-family (Audit and Accountability) controls
- Configuration management must satisfy CM-family controls (baseline
  configurations, change tracking, least functionality)
- Every component in the technology stack needs a FIPS 140-2/3 validation
  certificate or must be replaced

## Phased Approach

### Phase 0: FedRAMP Readiness Assessment (months 1–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Engage FedRAMP-experienced consultant for gap analysis | Month 1 | $15K–$40K |
| Determine impact level (Moderate vs High) | Month 1 | Included |
| Identify sponsoring agency or pursue JAB P-ATO path | Month 2–3 | — |
| Evaluate FedRAMP 20x eligibility and timeline | Month 2 | — |

### Phase 1: Boundary Definition and SSP (months 3–9)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Define authorization boundary (what's in scope) | Month 3–4 | $20K–$50K (consultant) |
| Write System Security Plan (SSP) documenting all controls | Month 4–8 | 400–800 hours internal |
| Implement technical controls not already in place | Month 4–9 | $50K–$200K infrastructure |

### Phase 2: 3PAO Assessment (months 9–14)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Engage 3PAO for Security Assessment | Month 9 | $150K–$300K |
| Remediate findings from assessment | Month 11–12 | Varies |
| Submit authorization package to FedRAMP PMO or agency | Month 13 | — |
| Receive ATO (Authorization to Operate) | Month 14+ | — |

### Phase 3: Continuous Monitoring (ongoing)

| Step | Frequency | Cost Estimate |
|------|-----------|---------------|
| Monthly vulnerability scans and reporting | Monthly | $5K–$15K/year |
| Annual penetration testing | Annual | $20K–$50K |
| Significant change requests | As needed | Varies |
| Annual assessment by 3PAO | Annual | $75K–$150K |

**Estimated total for initial authorization: $250K–$650K + 12–18 months.**
**Estimated annual continuous monitoring: $100K–$215K/year.**

## Artifacts Required

| Artifact | Purpose | Maintenance |
|----------|---------|-------------|
| System Security Plan (SSP) | Documents all 325+ controls | Living document |
| Security Assessment Report (SAR) | 3PAO evaluation results | Per assessment |
| Plan of Action and Milestones (POA&M) | Tracks deficiency remediation | Monthly updates |
| Continuous monitoring deliverables | Monthly scans, incident reports | Monthly |
| Authorization package | Submission to FedRAMP PMO | Initial + updates |
| Interconnection Security Agreements (ISA) | For external service dependencies | Per connection |

## Relationship to NIST 800-53

FedRAMP is a selection of NIST 800-53 Rev 5 controls with additional FedRAMP-
specific requirements. The 20 control families include:

Access Control (AC), Awareness and Training (AT), Audit and Accountability (AU),
Security Assessment (CA), Configuration Management (CM), Contingency Planning
(CP), Identification and Authentication (IA), Incident Response (IR),
Maintenance (MA), Media Protection (MP), Physical and Environmental Protection
(PE), Planning (PL), Program Management (PM), Personnel Security (PS),
Personally Identifiable Information Processing (PT), Risk Assessment (RA),
System and Services Acquisition (SA), System and Communications Protection (SC),
System and Information Integrity (SI), Supply Chain Risk Management (SR).

**Supply Chain Risk Management (SR)** is a Rev 5 addition directly relevant to
claude-kit as an AI tool in the customer's software supply chain.

## Traces

- **Upstream:** REQ-009 (Cloud Platform — the SaaS offering that requires
  authorization), QA-001 (SOC 2 — prerequisite baseline)
- **Downstream:** QA-005 (DoD Impact Levels — built on top of FedRAMP), future SPEC
  for cloud platform infrastructure
- **Standards:** NIST SP 800-53 Rev 5, FIPS 140-2/140-3

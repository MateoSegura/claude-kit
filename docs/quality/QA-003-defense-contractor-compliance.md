# QA-003 — Defense Contractor Compliance

**Status:** draft
**Priority:** must
**Category:** compliance
**Governing Process:** PROC-SP-002 (Quality Assurance)

## Context

CMMC 2.0 (Cybersecurity Maturity Model Certification) is the DoD's framework
for certifying the cybersecurity posture of defense contractors. It was finalized
September 2025, became effective November 10, 2025, and is rolling out in phases
through 2028. CMMC Level 2 maps directly to NIST SP 800-171's 110 security
requirements across 14 control families.

claude-kit does not need CMMC certification itself. But claude-kit's customers —
defense contractors handling CUI — must prove their tooling ecosystem is
compliant within their CMMC boundary. If claude-kit processes, stores, or
transmits CUI (source code for defense programs IS CUI), it falls within the
customer's CUI boundary and must not break their CMMC posture.

The on-prem deployment model is a significant advantage here: it keeps
everything within the customer's existing CMMC boundary.

## Constraint

### CMMC 2.0 Levels

| Level | Practices | Assessment | Target Audience |
|-------|-----------|------------|-----------------|
| **Level 1 (Foundational)** | 15 basic safeguarding (FAR 52.204-21) | Annual self-assessment | All FCI handlers |
| **Level 2 (Advanced)** | 110 practices (NIST 800-171) | C3PAO third-party assessment | Most defense contractors |
| **Level 3 (Expert)** | NIST 800-172 enhanced requirements | Government-led assessment | Most sensitive programs |

### Rollout Timeline

| Phase | Window | Requirement |
|-------|--------|-------------|
| Phase 1 | Nov 2025 – Nov 2026 | Level 1 and Level 2 self-assessments in contract awards |
| Phase 2 | Nov 2026 – 2027 | Level 2 C3PAO assessments required |
| Phase 3–4 | 2027+ | Level 3 enforcement |

### NIST 800-171 Control Families (Level 2)

All 14 families apply when claude-kit handles CUI:

1. **Access Control** (22 requirements)
2. **Awareness and Training** (3 requirements)
3. **Audit and Accountability** (9 requirements)
4. **Configuration Management** (9 requirements)
5. **Identification and Authentication** (11 requirements)
6. **Incident Response** (3 requirements)
7. **Maintenance** (6 requirements)
8. **Media Protection** (9 requirements)
9. **Personnel Security** (2 requirements)
10. **Physical Protection** (6 requirements)
11. **Risk Assessment** (3 requirements)
12. **Security Assessment** (4 requirements)
13. **System and Communications Protection** (16 requirements)
14. **System and Information Integrity** (7 requirements)

## Architectural Impact

claude-kit must support (not break) each of these control families:

| Control Family | What claude-kit Must Provide |
|----------------|---------------------------|
| **Audit and Accountability** | Tamper-evident agent action logs, session recordings, file modification trails |
| **Access Control** | Configurable session permissions, least-privilege enforcement, role-based tool restrictions |
| **Identification and Authentication** | Integration with customer IdP, unique session identification, MFA-compatible auth flow |
| **System and Communications Protection** | FIPS-validated encryption for data at rest and in transit, session isolation |
| **Configuration Management** | Baseline configuration documentation, change tracking for plugin updates |
| **Incident Response** | Anomaly detection in agent behavior, integration points for customer SIEM/SOC |
| **Media Protection** | Secure deletion of temporary decrypted plugin content, CUI-aware cleanup |

## Phased Approach

### Phase 1: Customer-Facing Documentation (months 1–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Map claude-kit features to all 110 NIST 800-171 requirements | Month 1–2 | 120–200 hours internal |
| Create shared responsibility matrix (what customer handles vs what claude-kit handles) | Month 2 | 40 hours |
| Produce customer-facing SSP contribution document | Month 2–3 | 60 hours |
| Create deployment guide for CMMC-compliant environments | Month 3 | 40 hours |

### Phase 2: Technical Hardening (months 3–6)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Implement audit logging that satisfies AU-family requirements | Month 3–4 | Engineering effort |
| Add FIPS-mode encryption option for on-prem deployments | Month 4–5 | Engineering effort |
| Build SIEM integration points (syslog, CEF, or STIX/TAXII) | Month 5–6 | Engineering effort |
| Implement configurable session access controls | Month 4–5 | Engineering effort |

### Phase 3: Validation and Certification Support (months 6–9)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Engage C3PAO-experienced consultant to review documentation | Month 6 | $10K–$25K |
| Pilot with defense contractor customer in their CMMC boundary | Month 7–8 | — |
| Iterate on documentation based on pilot findings | Month 8–9 | — |

**Estimated total: $10K–$25K external + 260–340 hours internal.**

## Artifacts Required

| Artifact | Audience | Purpose |
|----------|----------|---------|
| NIST 800-171 control mapping | Customer security teams | Shows how claude-kit supports each of 110 controls |
| Shared responsibility matrix | Customer + auditors | Delineates customer vs vendor obligations |
| SSP contribution document | Customer's SSP authors | Pre-written sections customers paste into their SSP |
| Deployment guide for CUI environments | Customer IT/DevSecOps | Step-by-step secure deployment instructions |
| POA&M support documentation | Customer compliance teams | Helps customers track and remediate gaps |

## Traces

- **Upstream:** REQ-004 (Runtime Enforcement — enforcement mechanisms map to access
  control and audit requirements), REQ-005 (Transparent Execution — session
  logging maps to audit and accountability), REQ-008 (Secure Distribution —
  encryption maps to system and communications protection)
- **Downstream:** QA-004 (Export Control — many CMMC-bound programs are also
  ITAR-controlled), QA-008 (Dual Deployment — on-prem is the primary path for
  CUI environments), ADR-003 (Dual Enforcement)
- **Standards:** CMMC 2.0, NIST SP 800-171

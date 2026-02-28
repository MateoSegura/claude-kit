# QA-006 — Supply Chain Security

**Status:** draft
**Priority:** must
**Category:** compliance

---

## Context

Executive Order 14028 (Biden, May 2021) established mandatory Software Bill of
Materials (SBOM) requirements for software sold to federal agencies. EO 14144
(January 2025) extended and strengthened these. The Trump administration's June
2025 EO retained most supply chain directives but extended deadlines and removed
some attestation requirements. Regardless of executive order changes, SBOM and
supply chain transparency have become permanent expectations in federal and
enterprise procurement.

Additionally, all federal agencies are mandated to adopt Zero Trust architectures
(NIST 800-207) under EO 14028 and OMB M-22-09. CISA's Zero Trust Maturity Model
Version 2.0 provides the implementation roadmap. claude-kit orchestrates AI
agents that access and modify code — a high-privilege operation that demands Zero
Trust principles.

---

## Constraint

### SBOM Requirements

Software sold to federal agencies must include a machine-readable SBOM with
minimum elements per CISA 2025 guidance:

| Element | Description |
|---------|-------------|
| Supplier name | Organization that created the component |
| Component name | Name of the software component |
| Version string | Version of the component |
| Unique identifier | CPE, PURL, or equivalent |
| Dependency relationships | How components relate to each other |
| Author of the SBOM | Who generated the SBOM document |
| Timestamp | When the SBOM was generated |

### Secure Software Development Attestation

Vendors must attest to following secure development practices aligned with the
NIST Secure Software Development Framework (SSDF, SP 800-218):

1. Prepare the organization (PO) — security training, tools, environments
2. Protect the software (PS) — source code protection, integrity verification
3. Produce well-secured software (PW) — secure design, code review, testing
4. Respond to vulnerabilities (RV) — disclosure policy, remediation process

### Zero Trust Principles

| Principle | Application to claude-kit |
|-----------|--------------------------|
| No implicit trust | Every agent session authenticated and authorized independently |
| No session inheritance | Sessions do not inherit trust from previous sessions |
| Full audit trail | All agent actions logged and auditable |
| Network-agnostic access | Location (inside/outside firewall) does not determine access level |
| Policy-driven decisions | Access decisions based on dynamic policy evaluation |

---

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| SBOM production | Build pipeline must generate SBOM in SPDX or CycloneDX format with each release |
| Minimal dependency surface | claude-kit's stdlib-only Python design is a significant advantage — minimal SBOM complexity |
| Build provenance | Signed builds, reproducible builds, provenance tracking (who built what, when, with what dependencies) |
| Vulnerability disclosure | Public vulnerability disclosure policy and process |
| Zero Trust integration | On-prem deployments must integrate with customer identity providers and policy engines |
| Session authentication | Each claude-kit session must be independently authenticated, not relying on prior session state |

---

## Phased Approach

### Phase 1: SBOM and Build Provenance (months 1–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Select SBOM format (SPDX recommended for government market) | Week 1 | — |
| Integrate SBOM generation into CI/CD pipeline | Month 1 | 20–40 hours |
| Generate SBOM for claude-kit CLI (stdlib dependencies) | Month 1 | Included |
| Generate SBOM for distributable package (CLI + OpenSSL + plugins + scripts) | Month 2 | 20 hours |
| Implement signed builds with provenance metadata | Month 2–3 | 40 hours |
| Publish vulnerability disclosure policy | Month 1 | 8 hours |

### Phase 2: SSDF Attestation (months 3–6)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Document alignment with SSDF practices (PO, PS, PW, RV) | Month 3–4 | 40–80 hours |
| Implement automated security testing in CI (SAST, dependency scanning) | Month 4–5 | $5K–$15K/year tooling |
| Produce secure development attestation letter | Month 5 | 8 hours + $2K–$5K legal review |

### Phase 3: Zero Trust Alignment (months 3–9)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Design session authentication model (no inherited trust) | Month 3–4 | Engineering effort |
| Implement IdP integration for on-prem (SAML, OIDC) | Month 5–7 | Engineering effort |
| Add policy-driven access controls for agent capabilities | Month 6–8 | Engineering effort |
| Document Zero Trust architecture alignment for customers | Month 8–9 | 20 hours |

**Estimated total: $7K–$20K external + 156–216 hours internal.**

---

## Artifacts Required

| Artifact | Format | Frequency |
|----------|--------|-----------|
| SBOM (claude-kit CLI) | SPDX or CycloneDX | Per release |
| SBOM (distributable package) | SPDX or CycloneDX | Per release |
| Build provenance records | In-toto or SLSA format | Per build |
| Vulnerability disclosure policy | Public webpage | Maintained continuously |
| SSDF attestation letter | PDF/document | Annual |
| Zero Trust architecture documentation | Markdown/PDF | Per major version |

---

## Recommended Tools

| Tool | Purpose | Cost Range |
|------|---------|------------|
| Syft (Anchore) | SBOM generation | Free/open source |
| Grype (Anchore) | Vulnerability scanning against SBOM | Free/open source |
| Sigstore / cosign | Build signing and provenance | Free/open source |
| SLSA framework | Supply chain integrity levels | Standard/free |
| Semgrep | SAST for secure coding practices | Free tier available |

---

## Traces

- **From:** REQ-008 (Secure Distribution — encryption and distribution
  mechanisms are part of the supply chain), REQ-005 (Transparent Execution —
  session logging supports Zero Trust audit requirements)
- **To:** QA-003 (Defense Contractor Compliance — CMMC requires supply chain
  documentation), QA-008 (Dual Deployment — air-gapped distribution requires
  offline integrity verification)

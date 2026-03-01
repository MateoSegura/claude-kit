# QA-004 — Export Control

**Status:** draft
**Priority:** must
**Category:** compliance
**Governing Process:** PROC-SP-002 (Quality Assurance)

## Context

Two export control regimes affect claude-kit: ITAR (International Traffic in
Arms Regulations) for defense articles and technical data, and EAR (Export
Administration Regulations) for commercial and dual-use items including
encryption software.

ITAR creates the most severe constraint: ITAR-controlled technical data may
only be accessed by U.S. persons (citizens, permanent residents, or protected
persons). No exceptions without a license. If claude-kit processes source code
or prompts containing ITAR-controlled data, that processing constitutes access.
If the tool sends that data to an external AI API (like Anthropic's Claude API),
that constitutes an "export" — a hard blocker for ITAR work unless the AI model
runs entirely on-prem.

ITAR violations carry penalties of up to $1M per violation and up to 10 years
imprisonment.

EAR is less restrictive but still requires compliance. Since claude-kit uses
AES-256-CBC encryption (REQ-008), it likely falls under ECCN 5D002 (information
security software) or 5D992 (mass-market encryption software). Mass-market
classification has simplified export procedures.

## Constraint

### ITAR Requirements

1. **Access restriction is absolute** — only U.S. persons may access
   ITAR-controlled data. This applies to all personnel who could theoretically
   access the data, including through logs, debugging, or support channels.
2. **No external API calls with ITAR data** — sending ITAR-controlled code or
   prompts to an external AI API constitutes an "export." The SaaS offering
   CANNOT be used for ITAR work unless it runs in ITAR-compliant infrastructure
   (AWS GovCloud, Azure Government with ITAR designation).
3. **On-prem with local model is the only viable path** for most ITAR
   customers — the AI model must run entirely within the ITAR boundary.
4. **Technology Control Plan (TCP)** required for any ITAR-compliant
   deployment configuration.

### EAR Requirements

1. **ECCN self-classification** — file with the Bureau of Industry and Security
   (BIS) before making the software available outside the U.S.
2. **Annual self-classification report** — required for encryption software
   under EAR Part 740.17(e)(3)
3. **Denied party screening** — screen customers against BIS Entity List,
   OFAC SDN list, and other restricted party lists before selling internationally

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| No external API calls for ITAR | Must support a "bring your own model" (BYOM) architecture where customers point to their own AI endpoint |
| U.S. persons only access | Support model must restrict ITAR-tier customer data to U.S.-person engineers; no offshore support |
| On-prem mandatory for ITAR | The dual deployment architecture (QA-008) is not optional — it is required for this market |
| Data flow isolation | Data flow diagrams must prove no ITAR data leaves the controlled boundary, including through logs, telemetry, crash reports, or analytics |
| ECCN classification | One-time filing requirement; does not affect architecture but must happen before international distribution |

## Phased Approach

### Phase 1: EAR Compliance (month 1)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Determine ECCN classification (likely 5D992 for mass-market encryption) | Week 1–2 | $2K–$5K if using trade counsel |
| File self-classification with BIS | Week 2–3 | Included |
| Implement denied party screening for international sales | Week 3–4 | $1K–$5K/year (screening service) |

### Phase 2: ITAR-Safe Architecture (months 1–6)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Design BYOM architecture (local AI endpoint configuration) | Month 1–2 | Engineering effort |
| Audit entire codebase for hidden external calls (telemetry, update checks, analytics) | Month 2 | 40–80 hours |
| Build air-gapped deployment package (see QA-008) | Month 2–4 | Engineering effort |
| Create data flow diagrams for ITAR deployment configuration | Month 3 | 20 hours |
| Develop Technology Control Plan (TCP) template for customers | Month 4–5 | 40 hours + $5K–$10K legal review |

### Phase 3: ITAR Deployment Validation (months 6–9)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Pilot ITAR-compliant deployment with a defense customer | Month 6–8 | — |
| U.S. persons verification procedure for support staff | Month 6 | HR process |
| Independent review of ITAR compliance documentation | Month 8 | $10K–$20K (ITAR consultant) |

**Estimated total: $18K–$40K external + 100–140 hours internal.**

## Artifacts Required

| Artifact | Audience | Purpose |
|----------|----------|---------|
| ECCN self-classification filing | BIS | Required before international distribution |
| Annual self-classification report | BIS | Ongoing compliance for encryption software |
| Technology Control Plan (TCP) | Customer + DDTC | Documents ITAR-safe deployment configuration |
| Data flow diagrams | Customer security teams + auditors | Proves no ITAR data leaves controlled boundary |
| Employee citizenship verification procedure | Internal | Ensures only U.S. persons access ITAR data |
| ITAR-safe deployment guide | Customer IT | Step-by-step for deploying in ITAR environments |
| Denied party screening records | Internal compliance | Evidence of screening for international sales |

## Traces

- **Upstream:** REQ-006 (Autonomous Operation — ITAR environments demand controlled
  mode with mandatory human review), REQ-008 (Secure Distribution — encryption
  must use ITAR-compliant methods), ADR-007 (IP Protection Model)
- **Downstream:** QA-003 (Defense Contractor Compliance — many ITAR programs also
  require CMMC), QA-008 (Dual Deployment Architecture — on-prem is mandatory
  for ITAR)
- **Standards:** ITAR, EAR

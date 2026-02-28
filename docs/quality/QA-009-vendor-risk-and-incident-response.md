# QA-009 — Vendor Risk and Incident Response

**Status:** draft
**Priority:** should
**Category:** business

---

## Context

Every enterprise and government customer will subject claude-kit to a vendor
risk assessment before purchasing. This includes security questionnaires
(sometimes 1,000+ questions), third-party risk management (TPRM) evaluations,
and ongoing monitoring. Additionally, defense contractors must comply with DFARS
252.204-7012, which mandates 72-hour cyber incident reporting to the DoD Cyber
Crime Center (DC3).

claude-kit is a link in the customer's supply chain. If the tool has a
vulnerability, the customer is non-compliant. This creates both a legal
obligation (incident reporting) and a business reality (vendor assessments
gate every sale).

---

## Constraint

### Vendor Risk Questionnaires

Common questionnaires claude-kit must be prepared to answer:

| Questionnaire | Source | Scope |
|--------------|--------|-------|
| **SIG Full** | Shared Assessments | 1,000+ questions across 21 risk domains |
| **SIG Lite** | Shared Assessments | ~150 questions (abbreviated version) |
| **VSAQ** | Vendor Security Alliance | 7 sections: data protection, security policies, proactive/reactive security, supply chain, application security, compliance |
| **CAIQ** | Cloud Security Alliance | Cloud-specific evaluation |
| **Custom** | Large primes (Lockheed, Raytheon, Northrop) | Proprietary security questionnaires |

**Effort estimate:** 40–80 hours for the first major questionnaire. Subsequent
ones reuse 60–80% of answers from a master repository.

### Third-Party Risk Management (TPRM)

Beyond questionnaires, customers will assess claude-kit as a third-party risk:

1. **System Security Plan (SSP)** and Plan of Action and Milestones (POA&M)
   may be requested
2. **CMMC supply chain flow-down** — if claude-kit handles CUI on behalf of a
   defense contractor, claude-kit itself may need CMMC certification at the
   appropriate level
3. **FISMA inclusion** — contractors handling federal information are included
   within the agency's security boundary
4. **OMB M-22-18 / M-23-16** — agencies may only use software from producers
   who attest to secure development practices
5. **False Claims Act risk** — the DOJ's Civil Cyber-Fraud Initiative uses the
   False Claims Act to hold entities accountable for misrepresenting
   cybersecurity practices. Penalties are severe.

### Incident Response (DFARS 252.204-7012)

For defense contractor customers:

1. **72-hour reporting** — report cyber incidents to DC3 within 72 hours of
   discovery for any incident involving covered defense information
2. **Evidence preservation** — preserve images of all affected information
   systems and monitoring/packet capture data for at least 90 days; make
   available to DoD upon request
3. **Incident detection** — build capabilities to detect anomalous agent
   behavior, unauthorized file access, and privilege escalation

### Data Retention and Destruction

1. **CUI destruction** — CUI must be destroyed in a manner that makes it
   unreadable, indecipherable, and irrecoverable (NIST 800-88)
2. **Federal contractor records retention** — FAR Subpart 4.7 requires 3-year
   retention after final payment for contract records
3. **Log classification** — session logs and AI artifacts may themselves be CUI,
   subject to the same retention and destruction requirements
4. **Customer self-service** — SaaS customers need data export and deletion
   capabilities; on-prem customers need decommissioning documentation

---

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| Questionnaire readiness | Need centralized security posture documentation reusable across questionnaires |
| Supply chain flow-down | If handling CUI, may need own CMMC certification (not just supporting customer's) |
| 72-hour incident reporting | Need incident detection capabilities baked into the product, not bolted on |
| Evidence preservation | Session logs must be immutable and retainable for 90+ days |
| Data retention configurability | Retention policies must be configurable per customer contract |
| Secure deletion | NIST 800-88 compliant deletion for temporary files, session data, and decrypted plugin content |
| SIEM integration | On-prem customers need integration points for their Security Operations Center |

---

## Phased Approach

### Phase 1: Questionnaire Readiness (months 1–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Create master security posture document (answers reusable across questionnaires) | Month 1–2 | 80–120 hours |
| Complete SIG Lite questionnaire (baseline for all future questionnaires) | Month 2 | 20–40 hours |
| Evaluate questionnaire automation tools (Whistic, OneTrust, Loopio) | Month 1 | — |
| Obtain SOC 2 Type I (see QA-001) — significantly reduces questionnaire burden | Month 3–6 | See QA-001 |

### Phase 2: Incident Response (months 2–5)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Write incident response plan (detection, triage, containment, eradication, recovery, lessons learned) | Month 2 | 40 hours |
| Implement anomaly detection for agent behavior (unusual file access, privilege escalation attempts) | Month 3–4 | Engineering effort |
| Build SIEM integration points (syslog, CEF, or STIX/TAXII) for on-prem customers | Month 4–5 | Engineering effort |
| Conduct tabletop IR exercise | Month 5 | 8 hours |
| Document customer notification process for SaaS incidents | Month 3 | 8 hours |

### Phase 3: Data Lifecycle (months 3–6)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Implement configurable data retention policies | Month 3–4 | Engineering effort |
| Implement NIST 800-88 compliant secure deletion | Month 4–5 | Engineering effort |
| Build self-service data export for SaaS customers | Month 5 | Engineering effort |
| Create decommissioning guide for on-prem customers | Month 6 | 8 hours |

**Estimated total: 156–216 hours documentation + engineering effort.**

---

## Artifacts Required

| Artifact | Audience | Frequency |
|----------|----------|-----------|
| Master security posture document | Vendor assessments | Annual update |
| SIG Lite questionnaire (completed) | Enterprise customers | Annual update |
| Incident response plan | Internal + customers | Annual review |
| IR exercise results | Auditors | Annual |
| Customer incident notification template | SaaS customers | Per incident |
| Data retention policy documentation | Customers, auditors | Per major version |
| Decommissioning guide | On-prem customers | Per major version |
| DFARS compliance documentation | Defense contractor customers | Annual update |

---

## Recommended Tools

| Tool | Purpose | Cost Range |
|------|---------|------------|
| Whistic / OneTrust / Loopio | Questionnaire automation | $5K–$20K/year |
| PagerDuty / Opsgenie | Incident management | $1K–$10K/year |
| SIEM (Datadog, Panther, Wiz) | Detection and monitoring | Varies |
| Eraser (NIST 800-88 tool) | Secure data deletion | Free/included in OS |

---

## Traces

- **From:** REQ-005 (Transparent Execution — session logs are the foundation
  for incident detection and evidence preservation), REQ-004 (Runtime
  Enforcement — enforcement mechanisms support incident prevention)
- **To:** QA-001 (SOC 2 — IR plan is a SOC 2 requirement), QA-003 (Defense
  Contractor Compliance — DFARS reporting applies to defense customers),
  QA-007 (AI Regulatory — transparency documentation feeds into vendor
  assessments)

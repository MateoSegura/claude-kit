# QA-001 — SOC 2 Certification

**Status:** draft
**Priority:** must
**Category:** compliance

## Context

SOC 2 Type II has become the baseline gate for selling SaaS to mid-market and
enterprise accounts in North America. Government buyers often require it
alongside FedRAMP. Without SOC 2, enterprise procurement teams will not advance
past the security review stage. This is the first certification most startups
pursue because it has the broadest unblocking effect on sales cycles.

SOC 2 evaluates controls across five Trust Services Criteria: Security,
Availability, Processing Integrity, Confidentiality, and Privacy.

## Constraint

The claude-kit cloud platform (REQ-009) must be designed, built, and operated
in a manner that satisfies SOC 2 Type II audit requirements. Specifically:

1. **Audit trails** — Comprehensive, tamper-evident logging of all user actions,
   AI agent activity, file modifications, and administrative operations
2. **Access control** — Role-based access control (RBAC), multi-factor
   authentication (MFA), and least-privilege enforcement
3. **Encryption** — Data encrypted at rest (AES-256) and in transit (TLS 1.2+)
4. **Change management** — Documented processes for code changes, infrastructure
   changes, and configuration changes
5. **Incident response** — Formal IR procedures with defined roles, escalation
   paths, and communication templates
6. **Vulnerability management** — Regular vulnerability scans, penetration
   testing, and remediation tracking
7. **Vendor management** — Third-party risk assessment for all service providers
   (including Anthropic as the AI model provider)

## Architectural Impact

- Session logging (REQ-005) must produce audit-grade logs that satisfy the
  Audit and Accountability trust criteria
- The cloud platform (REQ-009) must implement RBAC from day one — retrofitting
  access control is expensive and disruptive
- All encryption must use algorithms and key lengths acceptable under SOC 2
  (AES-256 for data at rest, TLS 1.2+ for transit)
- Build pipelines must produce change management evidence automatically (commit
  history, PR reviews, deployment logs)

## Phased Approach

### Phase 1: SOC 2 Type I (months 1–6)

Establishes that controls are *designed* appropriately at a point in time.

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Select compliance automation platform (Vanta, Drata, or Secureframe) | Week 1–2 | $10K–$25K/year |
| Implement security policies (access control, data classification, IR, acceptable use, vendor management) | Weeks 2–6 | Internal time: 80–120 hours |
| Deploy technical controls (MFA, RBAC, encryption, logging, vulnerability scanning) | Weeks 4–12 | Infrastructure cost varies |
| Engage CPA firm for Type I audit | Month 4 | $10K–$30K |
| Complete Type I report | Month 5–6 | — |

**Estimated total: $20K–$55K + 200–300 hours internal time.**

### Phase 2: SOC 2 Type II (months 6–18)

Proves controls are *operating effectively* over a 6–12 month observation period.

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Begin observation period (automated evidence collection) | Month 6 | Ongoing |
| Quarterly access reviews, vulnerability scans, penetration test | Quarterly | $5K–$15K/year for pentest |
| Engage CPA firm for Type II audit | Month 15 | $30K–$100K |
| Complete Type II report | Month 16–18 | — |

**Estimated total: $35K–$115K + ongoing operational overhead.**

## Artifacts Required

| Artifact | Purpose | Frequency |
|----------|---------|-----------|
| Security policies (6–10 documents) | Define control framework | Annual review |
| Access control evidence (logs, reviews) | Prove least-privilege operation | Continuous |
| Change management records | Prove controlled deployment | Per change |
| Vulnerability scan results | Prove proactive security | Monthly |
| Penetration test report | Prove external validation | Annual |
| Incident response test results | Prove IR readiness | Annual |
| Vendor risk assessments | Prove supply chain diligence | Per vendor, annual review |
| SOC 2 report (Type I or II) | Deliver to customers | Annual |

## Recommended Tools

| Tool | Purpose | Cost Range |
|------|---------|------------|
| Vanta / Drata / Secureframe | Compliance automation, evidence collection | $10K–$25K/year |
| CPA firm (Schellman, Coalfire, A-LIGN) | Audit execution | $10K–$100K per audit |
| Vulnerability scanner (Nessus, Qualys) | Continuous vuln management | $3K–$10K/year |
| SIEM (Datadog, Panther, Wiz) | Log aggregation and alerting | Varies |

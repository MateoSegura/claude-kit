# QA-007 — AI Regulatory Compliance

**Status:** draft
**Priority:** must
**Category:** ai-regulation

## Context

The AI regulatory landscape is fragmented and evolving. At the federal level,
Biden's EO 14110 (the most comprehensive AI governance order) was revoked by
Trump's EO 14179 in January 2025. However, three durable regulatory vectors
remain:

1. **NDAA FY2026 Section 1513** is creating a CMMC-like certification framework
   specifically for AI used in defense — "CMMC for AI." Status report to
   Congress due June 16, 2026.
2. **OMB Memoranda M-25-21 and M-25-22** establish AI procurement guardrails for
   federal agencies, effective September 30, 2025. Contractors must provide
   transparency documentation for AI systems.
3. **NIST AI frameworks** (AI RMF 1.0 and AI 600-1 GenAI Profile) are voluntary
   but increasingly referenced in federal procurement requirements and
   contractor evaluations.

The EU AI Act is also relevant for customers who serve European defense partners
(NATO allies), though it explicitly exempts AI used exclusively for military
purposes.

## Constraint

### NDAA FY2026 Section 1513 — AI Security Framework for Defense

This is the most consequential regulation. It directs the DoD to:

1. Develop an AI/ML security assessment framework
2. Incorporate the framework into DFARS and the CMMC program
3. Apply the framework to "covered AI/ML" including source code, model weights,
   training data, and algorithms used by DoD

**What this means:** claude-kit will need to demonstrate compliance with a
defense-specific AI security framework that does not yet fully exist but will
be formalized by late 2026. Early alignment with NIST AI RMF positions the
product well.

### OMB M-25-22 — AI Procurement Transparency

Effective September 30, 2025. Requires agencies to obtain documentation from
AI vendors that "facilitates transparency and explainability." By March 11,
2026, all agencies must revise procurement policies to include these
requirements.

**What vendors must provide:**
1. How AI models are built, trained, or modified
2. What data the AI system processes and how
3. What guardrails and oversight mechanisms exist
4. How outputs are validated and reviewed

### NIST AI Risk Management Framework (AI RMF 1.0)

Voluntary but increasingly referenced. Establishes trustworthiness
characteristics:

| Characteristic | Application to claude-kit |
|---------------|--------------------------|
| **Validity and reliability** | Grader role (REQ-003) validates output quality |
| **Safety** | Runtime enforcement (REQ-004) prevents harmful actions |
| **Fairness and bias** | Less applicable to code generation tools |
| **Security and resilience** | Dual enforcement (ADR-003), secure distribution (REQ-008) |
| **Explainability** | Glass-box transparency (REQ-005, ADR-005) |
| **Privacy** | Data isolation (QA-008), no training on customer data |
| **Accountability** | Session logging, human review workflows |

### NIST AI 600-1 — Generative AI Profile

Specific to generative AI systems. Key requirements:

1. **Content provenance** — document which model version processed what data,
   at what time, with what configuration
2. **Model provenance** — document dependency on Anthropic's model, API version,
   and any configuration applied
3. **Tamper-evident audit trails** — retained per customer retention requirements
4. **Third-party model assessment** — documentation of external model reliance

### EU AI Act

| Milestone | Date | Relevance |
|-----------|------|-----------|
| Prohibited practices enforceable | February 2025 | Not applicable to developer tools |
| GPAI model obligations | August 2025 | Anthropic's obligation, not claude-kit's directly |
| High-risk AI system rules | August 2026 | Unlikely to apply to developer tools, but dual-use gray area exists |

The defense exemption applies to AI used exclusively for military purposes.
Dual-use (tools used for both military and civilian development) may fall within
scope, creating ambiguity for claude-kit customers who serve both markets.

## Architectural Impact

| Regulation | Architectural Requirement |
|------------|--------------------------|
| NDAA §1513 | Build toward a security-assessable AI architecture; document AI decision boundaries, model dependencies, and guardrail mechanisms |
| OMB M-25-22 | Create a transparency documentation package that customers can provide to procurement officers |
| NIST AI RMF | Map every trustworthiness characteristic to a claude-kit feature; fill gaps identified in the mapping |
| NIST AI 600-1 | Implement structured provenance logging: session ID, user identity, model version, prompt hash (not CUI content), action taken, files modified, human approval status |
| EU AI Act | Support customers in demonstrating compliance for dual-use scenarios; provide risk classification documentation |

## Phased Approach

### Phase 1: Transparency Documentation (months 1–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Create AI transparency document (model dependency, data flows, guardrails) | Month 1–2 | 40–60 hours |
| Map claude-kit to NIST AI RMF trustworthiness characteristics | Month 2 | 20 hours |
| Create OMB M-25-22 compliance package for customer procurement | Month 2–3 | 30 hours |

### Phase 2: Provenance Logging (months 3–6)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Design structured provenance log format | Month 3 | 20 hours |
| Implement model version tracking in session logs | Month 4 | Engineering effort |
| Add human approval status logging (AI suggested vs human approved) | Month 4–5 | Engineering effort |
| Create tamper-evident log mechanism (hash chains or similar) | Month 5–6 | Engineering effort |

### Phase 3: NDAA Alignment (months 6–12)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Monitor NDAA framework development (status report due Jun 2026) | Ongoing | — |
| Participate in public comment period if framework is released for review | When available | 20 hours |
| Pre-align architecture with emerging requirements | Month 9–12 | Engineering effort |

**Estimated total: 110–130 hours documentation + engineering effort for
provenance system.**

## Artifacts Required

| Artifact | Audience | Frequency |
|----------|----------|-----------|
| AI transparency document | Customer procurement, auditors | Per major version |
| NIST AI RMF mapping | Customer security teams | Per major version |
| OMB M-25-22 compliance package | Federal procurement officers | Annual update |
| Model provenance documentation | Auditors, customers | Per model version change |
| Provenance log schema documentation | Customer IT integration teams | Per major version |
| EU AI Act risk classification analysis | European customers | Annual update |

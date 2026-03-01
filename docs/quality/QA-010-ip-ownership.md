# QA-010 — IP Ownership of AI-Generated Code

**Status:** draft
**Priority:** should
**Category:** business
**Governing Process:** PROC-SP-002 (Quality Assurance)

## Context

The intellectual property status of AI-generated code is legally unsettled. The
U.S. Copyright Office has indicated that purely AI-generated works are not
copyrightable, but works with sufficient human authorship that incorporate AI
assistance may be. This distinction matters enormously for defense contractors
whose government contracts specify IP rights under FAR/DFARS provisions.

claude-kit occupies a strategic framing position: it assists human developers
rather than generating code autonomously. This framing is both technically
accurate (the human developer directs, reviews, and accepts/rejects every
suggestion) and legally important (it preserves the "human authorship"
requirement for copyright protection).

## Constraint

### Federal Contract IP Rules (FAR/DFARS)

| Rights Category | What It Means | When It Applies |
|----------------|---------------|-----------------|
| **Unlimited rights** | Government gets full ownership | Software developed exclusively with government funding |
| **Government purpose rights** | Government can use and share within government; contractor retains commercial rights | Software developed with mixed funding |
| **Limited rights** | Government can use but not share | Software developed entirely at private expense |
| **Restricted rights** | Most limited government access | Commercial software licensed to government |

If AI-generated code is produced during contract performance, the government
may claim unlimited rights to both the code and the AI-generated outputs. The
category depends on funding source and contract terms.

### Copyright Status of AI-Generated Code

1. **Purely AI-generated works** are not copyrightable under current U.S. law
   (Copyright Office guidance, Thaler v. Perlmutter)
2. **AI-assisted works** — where a human exercises creative control — may be
   copyrightable if the human contribution is sufficiently creative
3. **The line between "AI-generated" and "AI-assisted" is not clearly defined**
   — this is an active area of legal development
4. **OMB guidance** requires contracts to clearly delineate IP ownership,
   data portability, and long-term interoperability for AI systems
5. **Training data restrictions** — contracts must bar vendors from using
   non-public government data to train publicly available AI

### Customer Obligations

claude-kit's customers need clarity on:

1. Whether the tool's suggestions create IP complications in their government
   contracts
2. How to classify AI-assisted code in their deliverables
3. Whether using claude-kit constitutes "development at private expense" or
   something else
4. How to document the human review and approval process for audit purposes

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| "AI-assisted" framing | All product messaging, documentation, and contracts must frame the tool as assisting human developers, not generating code autonomously |
| Human approval logging | Every AI suggestion must be logged with explicit human accept/reject/modify status for IP audit trails |
| No training on customer data | Architecture must guarantee (and document) that customer code is never used to train or fine-tune any model |
| Code provenance tracking | Audit trail must show which code was human-written vs AI-suggested vs AI-suggested-then-modified |
| Contractual language | Standard customer agreements must address IP ownership, data usage, and training restrictions |

## Phased Approach

### Phase 1: Framing and Documentation (months 1–2)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Establish official product framing: "AI-assisted development tool" (not "AI code generator") | Month 1 | 8 hours |
| Create IP FAQ for customers explaining code ownership under different contract types | Month 1 | 20 hours + $5K–$10K legal review |
| Review all marketing, website, and documentation for framing consistency | Month 1–2 | 16 hours |
| Draft standard contractual language: no training on customer data, data usage restrictions | Month 2 | $5K–$15K legal |

### Phase 2: Technical Implementation (months 2–5)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Implement human approval status logging in session traces | Month 2–3 | Engineering effort |
| Add code provenance markers (AI-suggested, human-written, human-modified) | Month 3–4 | Engineering effort |
| Create audit report generator for customers who need IP documentation | Month 4–5 | Engineering effort |

### Phase 3: Legal Monitoring (ongoing)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Monitor Copyright Office rulings on AI-generated works | Ongoing | — |
| Monitor NDAA and FAR/DFARS amendments related to AI IP | Ongoing | — |
| Update customer FAQ and contractual language as law evolves | As needed | Legal review per update |

**Estimated total: $10K–$25K legal + 44 hours documentation + engineering
effort.**

## Artifacts Required

| Artifact | Audience | Frequency |
|----------|----------|-----------|
| Customer IP FAQ | Sales, customer legal teams | Updated as law evolves |
| Standard contractual language (no-training clause, data usage) | Customer contracts | Per contract template version |
| Product framing guidelines | Marketing, documentation, sales | Maintained continuously |
| Code provenance audit report template | Customer compliance teams | Per major version |

## Traces

- **Upstream:** REQ-005 (Transparent Execution — session logging captures human
  approval status), REQ-006 (Autonomous Operation — controlled mode ensures
  human review), ADR-007 (IP Protection Model — honest assessment of what's
  protectable)
- **Downstream:** QA-007 (AI Regulatory Compliance — OMB procurement rules reference
  IP ownership), QA-009 (Vendor Risk — IP questions appear in vendor
  assessments)
- **Standards:** None identified

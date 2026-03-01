# QA-012 — Insurance and Escrow

**Status:** draft
**Priority:** should
**Category:** insurance

## Context

Enterprise and government contracts require specific insurance coverage and
often demand source code escrow as conditions of purchase. These are not
technical constraints — they are business prerequisites that gate every
enterprise and government deal. Not having the right coverage or escrow
arrangement is a deal-breaker, not a negotiation point.

## Constraint

### Cyber Liability Insurance

| Requirement | Typical Minimum |
|------------|-----------------|
| Per-occurrence limit | $5,000,000 for government contracts under $1M |
| Aggregate limit | $10,000,000 for larger contracts |
| Coverage scope | Data breach costs, ransomware, regulatory fines, forensic investigation, customer notification |
| Government entity | Must be named as "Additional Insured" |

### Technology Errors & Omissions (Tech E&O)

| Requirement | Typical Minimum |
|------------|-----------------|
| Per-occurrence limit | $2,000,000–$5,000,000 |
| Coverage scope | Software defects causing customer harm, failure to perform as promised, copyright violations |
| Separate from | Cyber liability (required as a separate policy in most government contracts) |

### Additional Insurance Typically Required

| Type | Purpose | When Required |
|------|---------|---------------|
| General commercial liability | Bodily injury, property damage | All contracts |
| Workers' compensation | Employee injury | All contracts (state-mandated) |
| Professional liability | Professional negligence | Enterprise contracts |
| Directors & officers (D&O) | Management liability | If funded by investors |

### Source Code Escrow

**What it is:** Deposit of claude-kit's source code with a third-party escrow
agent, released to the customer under specific trigger conditions.

**Trigger conditions (typically):**
1. Company bankruptcy or insolvency
2. Service discontinuation or material breach
3. Failure to provide support or maintenance
4. Acquisition by a competitor of the customer

**DFARS provisions** address data escrow agreements where the government and
contractor identify a third-party escrow agent. Escrow deposits must include:

| Item | Description |
|------|-------------|
| Executable code | All compiled/packaged binaries |
| Source code | Complete source with build instructions |
| Build procedures | Steps to build from source |
| Automation scripts | CI/CD configurations, deployment scripts |
| Tools and dependencies | All required build tools |
| Databases | Schema definitions, migration scripts |
| Libraries | All third-party dependencies |
| Test results | Latest test suite results |
| Data sets | Test fixtures and sample data |
| System configurations | Environment configuration documentation |

**Regular escrow verification** (confirming deposited code builds and runs) is
expected by sophisticated buyers.

**Alternative:** Some government contracts prefer unlimited rights to source
code rather than escrow. This decision depends on the business model and IP
strategy (see ADR-007).

## Phased Approach

### Phase 1: Insurance (months 1–2)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Obtain cyber liability insurance | Month 1 | $3K–$8K/year (seed-stage startup) |
| Obtain Tech E&O insurance | Month 1 | $2K–$5K/year (often bundled) |
| Obtain general commercial liability | Month 1 | $500–$2K/year |
| Review policy limits against target contract sizes | Month 2 | — |

**Note:** Insurance providers will want to see basic security controls in
place (MFA, encryption, IR plan). This creates a positive dependency with
QA-001 (SOC 2) and QA-009 (Incident Response).

### Phase 2: Escrow Setup (months 2–4)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Select escrow provider (Iron Mountain, Codekeeper, NCC Group) | Month 2 | — |
| Negotiate escrow agreement template | Month 2–3 | $3K–$8K legal review |
| Make initial deposit (source code + build instructions + dependencies) | Month 3 | $5K–$15K setup |
| Schedule annual verification deposit and build test | Month 4 | $3K–$8K/year ongoing |

### Phase 3: Ongoing (annual)

| Step | Frequency | Cost Estimate |
|------|-----------|---------------|
| Insurance renewal and limit review | Annual | Premium varies |
| Escrow deposit update (every major release) | Per major version | $1K–$3K per deposit |
| Escrow verification (confirm code builds) | Annual | $3K–$8K |

**Estimated annual ongoing cost: $12K–$38K (insurance + escrow).**

## Decision: Escrow vs. Source Access

| Approach | Pros | Cons |
|----------|------|------|
| **Escrow** | Protects IP, industry-standard, predictable cost | Customer cannot inspect code until trigger event |
| **Unlimited source rights** | Satisfies most demanding government buyers, simplifies procurement | Loses IP protection for government customers |
| **Source-available license** | Customer can inspect but not redistribute | Novel approach, may require legal education |

This decision intersects with ADR-007 (IP Protection Model). The recommended
approach depends on the customer segment:

- **Commercial enterprise:** Escrow with standard trigger conditions
- **Federal government:** Evaluate per contract; some will require unlimited
  rights
- **Defense (ITAR):** Escrow with verified builds; source rights may be required
  for classified-adjacent programs

## Artifacts Required

| Artifact | Audience | Frequency |
|----------|----------|-----------|
| Certificate of insurance (cyber liability) | Customer procurement | Per contract |
| Certificate of insurance (Tech E&O) | Customer procurement | Per contract |
| Escrow agreement template | Customer legal teams | Maintained continuously |
| Escrow deposit receipt | Customer legal teams | Per deposit |
| Escrow verification report | Customer legal teams | Annual |

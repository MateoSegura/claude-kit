---
name: core-security:threat-modeling
description: "STRIDE methodology, attack surface analysis, trust boundaries, data flow diagrams, and risk assessment for any software project"
user-invocable: false
---

# Threat Modeling Quick Reference

## What Is Threat Modeling

A structured approach to identifying security threats, determining their impact, and planning mitigations. Answer four questions:

1. **What are we building?** — System architecture, data flows, components
2. **What can go wrong?** — Threats, attack vectors, abuse cases
3. **What are we going to do about it?** — Mitigations, controls, acceptance
4. **Did we do a good job?** — Validation, testing, review

## When to Threat Model

- Before starting a new project or feature
- When changing authentication, authorization, or data handling
- When adding new external integrations or APIs
- When modifying infrastructure or deployment architecture
- During security reviews or compliance audits
- After a security incident (retrospective modeling)

## STRIDE Methodology

Categorize threats by what they violate:

| Category | Violates | Description | Example |
|----------|----------|-------------|---------|
| **S**poofing | Authentication | Pretending to be someone/something else | Forged JWT, stolen session cookie |
| **T**ampering | Integrity | Unauthorized modification of data | Modified API request, altered database record |
| **R**epudiation | Non-repudiation | Denying an action occurred | User claims they never placed an order |
| **I**nformation Disclosure | Confidentiality | Exposing data to unauthorized parties | Leaked API keys, verbose error messages |
| **D**enial of Service | Availability | Making a system unavailable | Resource exhaustion, algorithmic complexity attack |
| **E**levation of Privilege | Authorization | Gaining unauthorized access level | Admin access via IDOR, privilege escalation |

### Applying STRIDE

For each component in your system, ask:

- **S**: Can an attacker impersonate this component or its users?
- **T**: Can an attacker modify data in transit or at rest?
- **R**: Can an attacker perform actions without accountability?
- **I**: Can an attacker access data they should not see?
- **D**: Can an attacker make this component unavailable?
- **E**: Can an attacker gain higher privileges than intended?

## Data Flow Diagrams (DFD)

Model your system with these elements:

| Element | Symbol | Description |
|---------|--------|-------------|
| External entity | Rectangle | Users, third-party services, external systems |
| Process | Circle | Your application code, services, APIs |
| Data store | Parallel lines | Databases, file systems, caches |
| Data flow | Arrow | Data moving between elements |
| Trust boundary | Dashed line | Where trust level changes |

**Steps to create a DFD:**
1. Identify all external entities that interact with the system
2. Map all processes that handle data
3. Identify all data stores
4. Draw data flows between elements with labels (what data, what protocol)
5. Draw trust boundaries between different security zones

## Trust Boundaries

A trust boundary exists wherever the trust level changes:

**Common trust boundaries:**
- Internet to DMZ (firewall)
- DMZ to internal network
- Client to server
- Application to database
- User-space to kernel
- Container to host
- Secure enclave to normal execution (e.g., TrustZone boundary)
- Between microservices with different privilege levels

**Rule:** Every data flow crossing a trust boundary needs validation, authentication, or encryption.

## Attack Surface Analysis

**Attack surface** = the sum of all points where an attacker can interact with your system.

### Reducing Attack Surface

| Action | Example |
|--------|---------|
| Remove unused features | Disable admin panel if not needed |
| Close unused ports | Only expose 80/443 |
| Minimize API surface | Only expose endpoints clients actually need |
| Restrict input points | Validate file types, limit upload sizes |
| Reduce privileges | Run services as non-root, use read-only filesystems |
| Remove default credentials | Change or disable all factory defaults |
| Disable debug interfaces | No debug endpoints in production |

### Network Attack Surface Checklist

- [ ] All public-facing ports documented and justified
- [ ] TLS on all external connections
- [ ] Internal service-to-service communication authenticated
- [ ] DNS configuration reviewed (no dangling records)
- [ ] CDN/proxy configuration hardened
- [ ] Rate limiting on public endpoints

### Application Attack Surface Checklist

- [ ] All API endpoints require authentication (except explicitly public ones)
- [ ] File upload types and sizes restricted
- [ ] Admin interfaces protected with additional controls
- [ ] Error messages do not leak implementation details
- [ ] Debug/diagnostic endpoints disabled in production
- [ ] Unnecessary HTTP methods disabled

## Risk Assessment Matrix

Combine **likelihood** and **impact** to prioritize threats:

```
              IMPACT
           Low  Med  High
          +----+----+----+
  High    | M  | H  | C  |
LIKE-     +----+----+----+
LIHOOD Med| L  | M  | H  |
          +----+----+----+
  Low     | L  | L  | M  |
          +----+----+----+

C = Critical  H = High  M = Medium  L = Low
```

**Likelihood factors:**
- Attacker skill required (script kiddie vs. nation-state)
- Availability of exploit tools
- Discoverability of the vulnerability
- Whether the attack can be automated

**Impact factors:**
- Data sensitivity (PII, financial, health)
- Number of affected users
- Regulatory consequences
- Reputational damage
- Recovery cost and time

## Secure Boot Chain of Trust (Generic)

Applicable to any system that needs verified boot integrity:

```
Hardware Root of Trust
  |
  v  (verifies)
Stage 0: ROM bootloader (immutable)
  |
  v  (verifies)
Stage 1: First-stage bootloader (signed)
  |
  v  (verifies)
Stage 2: OS / firmware (signed)
  |
  v  (verifies)
Stage 3: Application (signed)
```

**Key principles:**
- Each stage verifies the next before handing off execution
- Root of trust is immutable (hardware fuses, ROM code)
- All images are cryptographically signed
- Verification uses asymmetric cryptography (public key embedded, private key offline)
- Anti-rollback prevents downgrading to known-vulnerable versions
- Failed verification halts boot or falls back to recovery

**Applies to:** embedded firmware (MCUboot, U-Boot), UEFI Secure Boot, mobile OS verified boot, cloud instance measured boot (TPM attestation).

## Threat Response Options

For each identified threat, choose a response:

| Response | When to Use |
|----------|------------|
| **Mitigate** | Implement controls to reduce risk (most common) |
| **Transfer** | Shift risk to third party (insurance, managed service) |
| **Avoid** | Remove the feature or component that creates the risk |
| **Accept** | Risk is below threshold and cost of mitigation exceeds benefit |

Document the decision and rationale for each threat.

## Additional Resources

For detailed STRIDE worksheets, DFD templates, risk assessment scoring guides, and threat library patterns, see [threat-reference.md](threat-reference.md).

# QA-008 — Dual Deployment Architecture

**Status:** draft
**Priority:** must
**Category:** deployment

---

## Context

claude-kit must support two fundamentally different deployment models:

1. **SaaS (commercial)** — cloud-hosted platform for enterprise and individual
   users with internet connectivity
2. **On-prem / air-gapped (government/defense)** — self-contained deployment
   within the customer's controlled environment with zero internet connectivity

This is not a nice-to-have. The compliance constraints documented in QA-003
(CMMC), QA-004 (ITAR), and QA-005 (DoD IL) make on-prem deployment mandatory
for the defense market. The SaaS model serves the broader commercial market and
eventually federal agencies through FedRAMP authorization (QA-002).

Every architectural decision must be validated against both deployment models.
A feature that requires cloud connectivity is unusable for the defense market.
A feature that only works on-prem misses the commercial market.

---

## Constraint

### Data Isolation (Multi-Tenant SaaS)

FedRAMP and NIST 800-53 SC-7 (Boundary Protection) require:

1. **Tenant data isolation at every layer** — network, application, storage,
   logging, and AI context
2. **AI context isolation** — one tenant's code/prompts must never leak into
   another tenant's AI context. This includes caching, conversation history,
   and embedding stores.
3. **Log segregation** — government customer logs must never co-mingle with
   commercial customer logs
4. **Single-tenant deployment option** — some government buyers will require a
   dedicated instance even in the SaaS model

### Air-Gapped Operation

Air-gapped environments have zero internet connectivity:

1. **Zero phone-home** — no telemetry uploads, update checks, license validation
   calls, or analytics callbacks. Defense customers will audit for hidden
   connectivity and finding a phone-home call is a deal-killer.
2. **Local-only telemetry** — write to local storage; optionally export via
   sneakernet (USB, offline file transfer) if the customer approves
3. **Offline documentation** — all help text, reference material, and skill
   content must be bundled. No links to external websites in operational output.
4. **Air-gap testing** — CI must include a network-isolated test to verify zero
   external dependencies

### Offline Licensing

| Option | Mechanism | Tradeoffs |
|--------|-----------|-----------|
| **Signed license files** | Digitally signed file with entitlements, expiration, feature flags. Validated locally. | Most reliable for air-gapped. Requires manual renewal process. |
| **Node-locked licenses** | Tied to machine hardware fingerprint. No network needed. | Breaks on hardware changes. |
| **Time-limited activation codes** | Pre-generated codes for defined periods. | Requires manual renewal. Clock-skew risk in air-gapped environments. |
| **Hardware dongles** | Physical device (iLok, HASP). | Industry-proven for air-gapped but adds logistics. |

**Recommended:** Signed license files with grace periods for clock-skew
scenarios. License provisioning via email/file transfer for air-gapped
customers.

### Offline Plugin Distribution

The current `claude-kit update` mechanism assumes internet connectivity. For
air-gapped deployments:

1. **Self-contained distributable package** — complete bundle of CLI + encrypted
   plugins + verification checksums + SBOM
2. **Integrity verification without network** — SHA-256 hash manifests and
   digital signatures in the bundle
3. **Version management without connectivity** — version manifest file showing
   installed vs latest available versions
4. **Transfer via approved media** — USB, SFTP to bastion host, or other
   customer-approved transfer mechanisms

### Key Management

| Deployment | Approach |
|------------|----------|
| **SaaS** | Managed KMS (AWS KMS, Azure Key Vault) with FIPS 140-2/3 Level 3. GovCloud-region KMS for FedRAMP. Customer-managed keys (CMK/BYOK) for enterprise. Annual key rotation minimum. |
| **On-prem** | Customer's own KMS infrastructure (on-prem HSMs for FIPS 140-2 Level 3). Integrate with standard interfaces (PKCS#11, KMIP). Document key rotation procedures. |

**Note:** The current `_get_key()` approach (runtime key assembly from split
parts) is appropriate for plugin encryption but does NOT satisfy FIPS 140-2
requirements for CUI protection. On-prem customers must bring their own key
management for CUI-grade encryption.

---

## Architectural Impact

| Constraint | SaaS Impact | On-Prem Impact |
|------------|------------|----------------|
| Data isolation | Database-per-tenant for IL4+; row-level for commercial | N/A — single-tenant by definition |
| AI context isolation | No shared caching, history, or embeddings between tenants | Customer controls AI endpoint entirely |
| Zero phone-home | Not applicable (cloud-connected) | Audit every component for hidden external calls |
| Offline licensing | Standard subscription/API key model | Signed license file with local validation |
| Plugin distribution | `claude-kit update` over HTTPS | Self-contained distributable package |
| Key management | Managed KMS + BYOK option | Customer KMS with PKCS#11/KMIP integration |
| Telemetry | Cloud analytics with opt-out | Local-only with sneakernet export |
| Documentation | Web-hosted docs acceptable | Everything bundled in distributable |

---

## Phased Approach

### Phase 1: Core Dual-Architecture Design (months 1–4)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Design abstraction layer for connectivity-dependent features | Month 1–2 | Engineering effort |
| Implement BYOM (Bring Your Own Model) architecture for local AI endpoints | Month 2–3 | Engineering effort |
| Create offline plugin bundle format with integrity verification | Month 3–4 | Engineering effort |
| Implement signed license file system | Month 3–4 | Engineering effort |

### Phase 2: Air-Gap Hardening (months 4–7)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Audit entire codebase for external connectivity dependencies | Month 4 | 40–80 hours |
| Build air-gap CI test (network-isolated environment) | Month 5 | 20 hours |
| Create self-contained distributable package builder | Month 5–6 | Engineering effort |
| Bundle all documentation and help text in distributable | Month 6 | 20 hours |
| Implement local-only telemetry with optional sneakernet export | Month 6–7 | Engineering effort |

### Phase 3: Multi-Tenant Isolation (months 4–8)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Design tenant isolation model (database-per-tenant for gov, row-level for commercial) | Month 4–5 | Engineering effort |
| Implement AI context isolation (no cross-tenant leakage) | Month 5–6 | Engineering effort |
| Implement log segregation by tenant | Month 6–7 | Engineering effort |
| Single-tenant deployment option for government SaaS customers | Month 7–8 | Engineering effort |

### Phase 4: Key Management Integration (months 7–10)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Integrate with managed KMS for SaaS (GovCloud-compatible) | Month 7–8 | Engineering effort |
| Implement PKCS#11/KMIP interface for on-prem KMS integration | Month 8–9 | Engineering effort |
| Implement BYOK (Bring Your Own Key) for enterprise customers | Month 9–10 | Engineering effort |
| Document key rotation procedures for both deployment models | Month 10 | 20 hours |

**Estimated total: 100–120 hours documentation + significant engineering effort
across all phases.**

---

## Artifacts Required

| Artifact | Purpose |
|----------|---------|
| Dual deployment architecture document | Describes both models and their constraints |
| Air-gap deployment guide | Step-by-step for offline installation |
| Distributable package specification | Format, integrity verification, contents |
| License file format specification | Schema for signed license files |
| Tenant isolation architecture | Database, AI context, and logging isolation design |
| Key management integration guide | PKCS#11/KMIP setup for on-prem customers |
| Air-gap test results | CI evidence of zero external dependencies |

---

## Traces

- **From:** REQ-006 (Autonomous Operation — deployment model determines
  autonomy mode), REQ-008 (Secure Distribution — encryption must work in both
  models), REQ-009 (Cloud Platform — SaaS deployment), QA-003 (Defense
  Contractor Compliance — on-prem required for CUI), QA-004 (Export Control —
  on-prem required for ITAR)
- **To:** ADR-007 (IP Protection Model — key management architecture),
  future SPEC for dual deployment implementation

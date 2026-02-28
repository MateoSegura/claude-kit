# PROC-ORG-005: Supplier Management

**Version:** 1.0.0
**Status:** draft
**Category:** organizational
**Layer:** base
**Maturity:** initial
**Owner:** Technical Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Supplier Management governs the evaluation, monitoring, and risk assessment of external suppliers whose products and services claude-kit depends on. Anthropic is the primary supplier — the entire product is built on Claude models, and a disruption in Anthropic's API availability, pricing, or capability would directly impact claude-kit's value proposition. Secondary suppliers include GitHub (CI/CD, container registry, source control) and the open-source ecosystem (system-level tools). This process ensures that supplier dependencies are understood, monitored, and risk-managed proactively.

## 2. Scope

**Included:**
- Identification and classification of all external suppliers
- Evaluation of supplier capabilities, reliability, and strategic alignment
- Ongoing performance monitoring of supplier services
- Supply chain risk assessment and contingency planning
- Contract and terms-of-service review for compliance implications
- Supplier communication and escalation procedures

**Excluded:**
- Internal development tooling decisions (IDE, editor preferences) — not supply chain
- Open-source license compliance scanning (handled as part of PROC-SEC-002)
- Government-specific supply chain assurance (handled by PROC-GOV-004)

## 3. Entry Criteria

- [ ] A new external dependency is being considered or introduced
- [ ] A scheduled supplier review interval has arrived (semi-annually)
- [ ] A supplier has announced a significant change (API version, pricing, terms of service, capability)
- [ ] An incident has been traced to a supplier service failure or limitation

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Supplier API documentation | Anthropic docs, GitHub docs | Web content |
| Service level indicators | Anthropic status page, GitHub status page | Web dashboard |
| Pricing and terms of service | Supplier websites | Legal documents |
| Incident records involving suppliers | `docs/operations/incidents/` (INC-XXX) | Incident post-mortems |
| Market research on alternatives | `docs/research/developer-tools-landscape.md` | Research paper |
| Risk register entries | PROC-ORG-004 outputs | Risk register |

## 5. Activities

### 5.1 Supplier Identification and Classification

Maintain a supplier inventory documenting all external dependencies:

| Supplier | Category | Criticality | What They Provide |
|----------|----------|-------------|-------------------|
| **Anthropic** | AI Model Provider | Critical | Claude models (claude-opus-4-6, haiku) — core AI capability for all agent execution |
| **GitHub** | Platform | Critical | Source control, CI/CD (Actions), container registry (ghcr.io), issue tracking, releases |
| **Ubuntu/Canonical** | OS | High | Base operating system for devcontainer (ubuntu:24.04) |
| **Python** | Runtime | High | CLI execution runtime (stdlib only, no PyPI dependencies) |
| **OpenSSL** | Cryptography | High | AES-256-CBC encryption for plugin distribution |

Criticality levels:
- **Critical:** Service outage directly blocks product functionality; no immediate workaround
- **High:** Service outage significantly impairs development or distribution; workarounds exist but are costly
- **Medium:** Service outage causes inconvenience; alternatives readily available

### 5.2 Supplier Evaluation

For each critical and high-criticality supplier, assess:

**Capability:** Does the supplier's product meet current and anticipated needs? For Anthropic: model quality, context window size, tool-use reliability, latency.

**Reliability:** What is the supplier's track record for uptime and service stability? Review status page history, documented outages, and communication quality during incidents.

**Strategic alignment:** Is the supplier's roadmap compatible with claude-kit's direction? For Anthropic: commitment to the Claude Code SDK, plugin/MCP ecosystem, enterprise and government market support.

**Lock-in assessment:** How difficult would it be to switch to an alternative? For Anthropic: agent definitions, skill prompts, and tool-use patterns are Claude-specific. Migration cost is high. For GitHub: CI workflows use GitHub Actions syntax; migration to another CI provider would require rewriting all 7 workflows.

### 5.3 Performance Monitoring

Continuously monitor supplier performance through:

**Anthropic:**
- Model quality: Do agents produce expected outputs? Track via nightly review finding rates.
- API availability: Monitor for service degradation during CI semantic checks (`pr.yml` semantic-check job).
- Model version changes: Watch for model deprecations that would break agent definitions referencing specific model IDs.

**GitHub:**
- Actions availability: Track `fast-validate` and `pr-validate` success rates excluding code-caused failures.
- Registry availability: Monitor devcontainer image pulls from `ghcr.io`.
- API rate limits: Ensure `gh` CLI operations do not hit rate limits during automated workflows.

### 5.4 Risk Assessment and Contingency Planning

For each critical supplier, maintain a contingency plan:

**Anthropic contingency:**
- Short-term (API outage < 24h): Development continues without semantic checks; `claude-validate` job failures are non-blocking.
- Medium-term (API outage > 24h): Disable nightly and weekly automated reviews; rely on manual review.
- Long-term (service discontinuation): Agent definitions and skill content would require porting to an alternative LLM provider. The skill and agent markdown format is provider-agnostic; the Claude-specific elements are model ID references and tool-use syntax.

**GitHub contingency:**
- Short-term: Local development continues; PRs queue until Actions recover.
- Long-term: Self-hosted Git server with alternative CI (e.g., Jenkins, Buildkite) as fallback.

### 5.5 Contract and Terms Review

Semi-annually, review supplier terms of service for changes that affect:
- Data handling (does the supplier process or retain plugin content?)
- API usage limits (rate limits, token quotas)
- Pricing (cost per API call, storage, compute)
- Intellectual property (does training on input data affect IP protection?)
- Export and compliance (restrictions on use in defense or government contexts)

Document findings and escalate concerns to the Product Lead.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Supplier inventory | `qms/` or `docs/quality/` | — | — |
| Supplier risk assessments | Linked to PROC-ORG-004 risk register | — | — |
| Contingency plans | Embedded in supplier inventory | — | — |
| Terms review notes | Internal documentation | — | — |

## 7. Exit Criteria

- [ ] Supplier inventory is current with all external dependencies classified by criticality
- [ ] Critical and high-criticality suppliers have documented evaluation and contingency plans
- [ ] Performance monitoring is active for critical suppliers
- [ ] Terms of service reviewed within the last 6 months for critical suppliers

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Inventory completeness | Cross-reference runtime dependencies with supplier inventory | All runtime dependencies (python3, openssl, git, jq, claude, gh) traced to a supplier |
| Contingency plan viability | Tabletop walkthrough of each contingency scenario | Plan can be executed within the stated timeframe without undocumented dependencies |
| Monitoring coverage | Verify monitoring exists for each critical supplier | At least one automated or semi-automated performance indicator per critical supplier |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Technical Lead | Owns the supplier inventory; leads supplier evaluations; maintains contingency plans |
| Product Lead | Reviews terms of service; assesses strategic alignment; manages supplier relationships |
| DevOps Lead | Implements and monitors supplier performance indicators; manages GitHub and registry configuration |
| Security Lead | Assesses supplier data handling practices; reviews security implications of supplier changes |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Supplier review currency | Percentage of critical suppliers reviewed within the last 6 months | 100% | Check review dates in supplier inventory |
| Supplier incident rate | Number of incidents per quarter attributable to supplier service failures | < 2 per quarter | Cross-reference INC-XXX records with supplier attribution |
| Contingency plan coverage | Percentage of critical suppliers with documented and reviewed contingency plans | 100% | Audit supplier inventory |
| Terms review compliance | Percentage of critical supplier terms reviewed within the prescribed interval | 100% | Track review dates |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.1.3 Supply | Supplier agreement and management |
| NIST SP 800-218 | PO.1.3 | Third-party software components and supply chain |
| NIST SP 800-161 | Supply chain risk management | Federal supply chain security requirements |
| ISO 27001 | A.15 | Supplier relationships and information security |
| CMMC | SC.3.177 | Supply chain protection for defense contractors |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Maintain a simple supplier list with criticality ratings. Review Anthropic API changelog monthly and GitHub Actions release notes quarterly. Skip formal contingency planning — document a one-paragraph fallback strategy for each critical supplier.

**Full ceremony (team targeting defense/federal):** Execute all activities including formal terms reviews, documented contingency plans, and tracked performance monitoring. Integrate with PROC-GOV-004 (Supply Chain Assurance) for government-specific requirements. Maintain supplier risk entries in the formal risk register.

**When to simplify:** If claude-kit is being used purely for internal development (not sold to defense or federal customers), reduce supplier evaluation to annual reviews and skip terms-of-service compliance analysis. The technical monitoring (API availability, model quality) should be maintained regardless.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-ORG-004 | Feeds into: supplier risks are a major category in the risk register |
| PROC-SEC-002 | Related: supplier vulnerability disclosures feed vulnerability management |
| PROC-SEC-003 | Related: supplier-caused incidents trigger incident response |
| PROC-LC-001 | Receives from: market analysis identifies supplier landscape changes and alternatives |
| PROC-LC-007 | Related: supplier outages may trigger operational incidents |
| PROC-LC-008 | Feeds into: supplier performance trends may drive improvement proposals |

## 14. Traces

- **Governs:** Supplier inventory, supplier contingency plans, supplier performance monitoring
- **Enforced by:** Semi-annual review schedule (manual); incident-triggered reviews (reactive)
- **Related QA:** Supplier dependency resilience, AI model availability, distribution infrastructure reliability

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — establishes formal supplier management with focus on Anthropic as primary AI model supplier |

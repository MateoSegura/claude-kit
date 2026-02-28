# claude-kit Documentation

Welcome to the claude-kit documentation site. This site contains the complete
project documentation: research papers, system requirements, architecture
decisions, process framework, quality attributes, and operational guides.

---

## Quick Navigation

<div class="grid cards" markdown>

- :material-flask: **[Research](docs/research/overview.md)**
    Theoretical foundations — AI instrumentation, multi-agent architecture,
    runtime governance, and more.

- :material-format-list-checks: **[Requirements](docs/requirements/INDEX.md)**
    10 system requirements covering domain injection, role specialization,
    enforcement, distribution, and ecosystem.

- :material-sitemap: **[Architecture](docs/architecture/decisions/ADR-001-context-engineering.md)**
    8 architecture decision records and component documentation.

- :material-cog: **[Process Framework](CATALOG.md)**
    37 processes across lifecycle, support, organizational, security, and
    government overlay categories with 5 standards mappings.

- :material-shield-check: **[Quality & Methodology](docs/quality/INDEX.md)**
    12 quality attributes (SOC 2, FedRAMP, CMMC, export control, AI compliance)
    plus research methodology and evidence quality assessment.

- :material-tools: **[Operations](docs/testing/INDEX.md)**
    Testing evidence, benchmarks, incident management, and compliance
    documentation.

</div>

---

## Process Framework at a Glance

The Process Asset Library (PAL) provides structured governance for the entire
software lifecycle. Processes are organized into two layers:

### Base Layer (24 Processes)

| Category | Count | Scope |
|----------|-------|-------|
| Lifecycle | 8 | Market analysis through continuous improvement |
| Support | 6 | Configuration, QA, V&V, documentation, defects, peer review |
| Organizational | 5 | Governance, measurement, training, risk, suppliers |
| Security | 5 | Secure dev, vulnerabilities, incidents, access, encryption |

### Government Overlay (13 Processes)

| Category | Count | Scope |
|----------|-------|-------|
| Compliance | 7 | CMMC, FedRAMP, export control, supply chain, AI, CUI, zero trust |
| Audit | 3 | Readiness, evidence collection, continuous monitoring |
| Deployment | 3 | Air-gap, impact levels, customer boundary integration |

### Standards Mappings

- [ISO/IEC 12207:2017](mappings/iso-12207.md) — Software lifecycle processes
- [CMMI-DEV v2.0](mappings/cmmi.md) — Capability maturity model
- [NIST SP 800-218](mappings/nist-800-218.md) — Secure Software Development Framework
- [NIST SP 800-171](mappings/nist-800-171.md) — Protecting CUI
- [NIST AI RMF](mappings/nist-ai-rmf.md) — AI Risk Management Framework

---

## About

claude-kit is an AI plugin management system that provides structured context
injection, runtime enforcement, and role-based team architecture for Claude Code
agents. This documentation site is built with [MkDocs Material](https://squidfunnel.github.io/mkdocs-material/)
and deployed via GitHub Pages.

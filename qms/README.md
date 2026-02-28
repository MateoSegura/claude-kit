# Process Asset Library (PAL)

A portable, process-governed documentation framework. Copy `qms/` into any
repository to get structured process governance over your project documentation.

## What This Is

The Process Asset Library defines **processes** that govern how documentation
artifacts are created, maintained, reviewed, and retired. Instead of building
docs bottom-up ("what documents do we need?"), this framework works top-down:
**processes define what artifacts exist, where they live, and how they flow.**

## Quick Start

```bash
# Install QMS instrumentation into your repo
bash qms/install.sh

# Also scaffold a docs/ directory from process templates
bash qms/install.sh --scaffold

# Include government/defense overlay
bash qms/install.sh --gov

# See what would be installed without writing files
bash qms/install.sh --dry-run
```

## Directory Structure

```
qms/
├── README.md                 ← You are here
├── CATALOG.md                ← Master index of all processes
├── VERSION-POLICY.md         ← How process versioning works
├── MATURITY-MODEL.md         ← 5-level maturity progression
├── processes/
│   ├── base/                 ← Commercial processes (all deployments)
│   │   ├── lifecycle/        ← PROC-LC-XXX (product lifecycle)
│   │   ├── support/          ← PROC-SP-XXX (support processes)
│   │   ├── organizational/   ← PROC-ORG-XXX (organizational processes)
│   │   └── security/         ← PROC-SEC-XXX (security processes)
│   └── gov/                  ← Government overlay (extends base)
│       ├── compliance/       ← PROC-GOV-XXX (regulatory compliance)
│       ├── audit/            ← PROC-GOV-XXX (audit readiness)
│       └── deployment/       ← PROC-GOV-XXX (secure deployment)
├── mappings/                 ← Standards alignment documents
├── templates/                ← Artifact templates used by docs/
├── instrumentation/          ← AI instrumentation (installed into .claude/)
│   ├── rules/                ← Process governance rules
│   ├── hooks.json            ← Process enforcement hooks
│   ├── commands/             ← Process management commands
│   └── skills/               ← Process knowledge skills
├── install.sh                ← One-command installation
└── scripts/
    └── validate-processes.sh ← Process framework validator
```

## Two Layers

### Base Layer (Commercial)

24 processes organized into four categories:

| Category | Count | Covers |
|----------|-------|--------|
| Lifecycle | 8 | Market analysis through continuous improvement |
| Support | 6 | Config management, QA, V&V, docs, defects, peer review |
| Organizational | 5 | Governance, measurement, training, risk, suppliers |
| Security | 5 | Secure dev, vulnerabilities, IR, access, encryption |

### Government Overlay

13 additional processes that extend the base layer for defense and federal
deployments:

| Category | Count | Covers |
|----------|-------|--------|
| Compliance | 7 | CMMC, FedRAMP, export control, supply chain, AI, CUI, zero trust |
| Audit | 3 | Audit readiness, evidence collection, continuous monitoring |
| Deployment | 3 | Air-gap, impact levels, customer boundary integration |

Government processes always reference their base-layer prerequisites. They
add requirements; they never replace base processes.

## Portability

This directory has **zero dependencies** on any specific project. It uses
generic concepts ("your project's docs/", "your project's .claude/") and
can be copied into any repository. The `install.sh` script handles all
project-specific wiring.

## Versioning

Each process carries its own semantic version. See `VERSION-POLICY.md` for
the complete versioning rules. Process versions are independent of any
project or product version.

## Maturity

Processes progress through five maturity levels. See `MATURITY-MODEL.md`
for level definitions and advancement criteria.

## Customer Extraction

For defense procurement, SOC 2 auditors, and CMMC C3PAOs:

```bash
bash qms/scripts/extract-qms.sh base        # Commercial package
bash qms/scripts/extract-qms.sh gov          # Full government package
bash qms/scripts/extract-qms.sh gov --standard cmmc   # CMMC-focused
bash qms/scripts/extract-qms.sh gov --standard fedramp # FedRAMP-focused
```

Extraction produces a customer-deliverable directory with process summaries,
standards mappings, and evidence references. Internal implementation details
(defect records, research papers, plugin source) are excluded.

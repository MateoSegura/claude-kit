# Process Governance — PAL Rule

This rule teaches the AI agent how the Process Asset Library (PAL) governs
the project's documentation. It is installed by the PAL `install.sh` and should
not be edited directly — update the source in the PAL repository's
`instrumentation/rules/` directory.

## Process Framework Overview

The project uses a process-governed documentation system. Every documentation
directory in `docs/` is governed by one or more processes defined in the PAL.
Processes define:

- What artifacts exist and where they live
- What template each artifact must follow
- What quality gates must pass before the artifact is accepted
- What entry/exit criteria apply to the workflow

## Before Editing Any docs/ File

1. **Identify the governing process** — check the directory's `INDEX.md` for
   its `**Governing Process:**` field
2. **Check entry criteria** — read the process's Section 3 to verify
   prerequisites are met
3. **Follow the template** — use the template specified in the process's
   Section 6 (Outputs/Artifacts)
4. **Verify quality gates** — after writing, check against the process's
   Section 8

## Process Document Location

Process documents are maintained in the PAL repository under:

```
processes/
├── base/           <- Commercial processes (always applicable)
│   ├── lifecycle/  <- PROC-LC-XXX
│   ├── support/    <- PROC-SP-XXX
│   ├── organizational/ <- PROC-ORG-XXX
│   └── security/   <- PROC-SEC-XXX
└── gov/            <- Government overlay (defense/federal deployments)
    ├── compliance/  <- PROC-GOV-XXX
    ├── audit/       <- PROC-GOV-XXX
    └── deployment/  <- PROC-GOV-XXX
```

## Directory-to-Process Mapping

| docs/ Directory | Governing Process |
|----------------|-------------------|
| `research/` | PROC-LC-001 (Market Analysis) |
| `requirements/` | PROC-LC-002 (Requirements Engineering) |
| `architecture/` | PROC-LC-003 (Architecture Design) |
| `specs/` | PROC-LC-004 (Implementation) |
| `testing/` | PROC-LC-005 (Integration & Testing) |
| `benchmarks/` | PROC-ORG-002 (Measurement & Analysis) |
| `operations/` | PROC-LC-007 (Deployment & Operations) |
| `quality/` | PROC-SP-002 (Quality Assurance) |
| `methodology/` | PROC-ORG-001 (Process Governance) |
| `compliance/` | PROC-GOV-* (Government overlay processes) |

## Base vs Government Overlay

- **Base processes** apply to all deployments (commercial and government)
- **Government overlay** processes extend base processes for defense/federal
  contexts and are only relevant when the project targets those markets
- Government processes always reference their base prerequisites — they add
  requirements, never replace base processes

## Process Versioning

Each process carries its own semantic version (independent of product version).
See VERSION-POLICY.md in the PAL repository for bump rules. When editing a
process document:
- Bump the Version field
- Add a row to Section 15 (Change History)
- Run the process validation script to verify

## Maturity Levels

Processes progress through: initial -> managed -> defined -> measured -> optimizing.
See MATURITY-MODEL.md in the PAL repository for level definitions and
advancement criteria.

## Process Document Conventions

Every process document includes two required sections beyond the standard 15:

### TL;DR Admonition

A `!!! abstract "TL;DR"` admonition block appears between the metadata header
and `## 1. Purpose`. It gives an engineer a 2-3 sentence summary of what the
process does, when to use it, and what it produces.

```markdown
# PROC-LC-002: Requirements Engineering

**Version:** 1.0.0
**Status:** active
...

!!! abstract "TL;DR"
    Captures stakeholder needs as traceable requirements. Use this process
    when starting a new feature or product. Produces REQ-XXX documents in
    `{project}/docs/requirements/`.

## 1. Purpose
```

The TL;DR must be specific to the process -- no generic filler.

### Quick Checklist

A `## Quick Checklist` section appears between Section 14 (Traces) and
Section 15 (Change History). It summarizes the key deliverables and gates
from the process as a task list:

```markdown
## Quick Checklist

- [ ] Entry criteria satisfied (upstream artifacts exist)
- [ ] Template used for all output artifacts
- [ ] Quality gates passed (peer review, validation)
- [ ] Traces section links upstream and downstream documents
- [ ] Change History updated with this revision
```

Target 5-8 items per checklist, drawn from Entry Criteria (Section 3),
key Activities (Section 5), Quality Gates (Section 8), and Exit Criteria
(Section 7).

## Validation

```bash
bash scripts/validate-processes.sh    # Process framework validation
bash scripts/validate-docs.sh         # Docs structure validation
```

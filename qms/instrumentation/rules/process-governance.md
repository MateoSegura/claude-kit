# Process Governance — QMS Rule

This rule teaches the AI agent how the Process Asset Library (PAL) governs
the project's documentation. It is installed by `qms/install.sh` and should
not be edited directly — update the source in `qms/instrumentation/rules/`.

## Process Framework Overview

The project uses a process-governed documentation system. Every documentation
directory in `docs/` is governed by one or more processes defined in
`qms/processes/`. Processes define:

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

```
qms/processes/
├── base/           ← Commercial processes (always applicable)
│   ├── lifecycle/  ← PROC-LC-XXX
│   ├── support/    ← PROC-SP-XXX
│   ├── organizational/ ← PROC-ORG-XXX
│   └── security/   ← PROC-SEC-XXX
└── gov/            ← Government overlay (defense/federal deployments)
    ├── compliance/  ← PROC-GOV-XXX
    ├── audit/       ← PROC-GOV-XXX
    └── deployment/  ← PROC-GOV-XXX
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
See `qms/VERSION-POLICY.md` for bump rules. When editing a process document:
- Bump the Version field
- Add a row to Section 15 (Change History)
- Run `bash qms/scripts/validate-processes.sh` to verify

## Maturity Levels

Processes progress through: initial → managed → defined → measured → optimizing.
See `qms/MATURITY-MODEL.md` for level definitions and advancement criteria.

## Validation

```bash
bash qms/scripts/validate-processes.sh    # Process framework (Layer 5)
bash scripts/validate-docs.sh             # Docs structure (Layer 4)
```

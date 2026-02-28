# docs/ — Project Documentation

claude-kit maintains a process-governed documentation system. Each layer is
governed by one or more processes defined in `qms/processes/`. Processes define
what artifacts exist, where they live, and how they flow.

## Governing Framework

This documentation system is governed by the Process Asset Library (`qms/`).
Every subdirectory has a governing process that defines its artifact types,
templates, and quality gates. See `qms/CATALOG.md` for the full process index.

## Traceability Chain

```
research/ → requirements/ → architecture/ → specs/ → code → testing/ → benchmarks/
                ↑    ↓                                          ↑
        methodology/ quality/                            operations/ (cross-cutting)
           (meta)   (quality attributes)
                                                      compliance/ (gov overlay)
```

Documents trace forward (research motivates requirements, requirements drive
architecture decisions) and backward (test evidence validates specs, specs
reference the requirements they fulfill).

## Layer Summary

| Layer | Directory | ID Prefix | Governing Process | Purpose |
|-------|-----------|-----------|-------------------|---------|
| Research | `research/` | — | PROC-LC-001 | Theoretical papers and exploration |
| Requirements | `requirements/` | REQ-XXX | PROC-LC-002 | What the system must do and why |
| Architecture | `architecture/` | ADR-XXX | PROC-LC-003 | Decisions and component documentation |
| Specs | `specs/` | SPEC-XXX | PROC-LC-004 | Version-scoped implementation specs |
| Testing | `testing/` | TEST-XXX, REG-XXX | PROC-LC-005 | Evidence and regression documentation |
| Benchmarks | `benchmarks/` | BM-XXX | PROC-ORG-002 | Methodology, baselines, and results |
| Operations | `operations/` | INC-XXX, RB-XXX, MIG-XXX | PROC-LC-007 | Incidents, runbooks, migrations |
| Quality | `quality/` | QA-XXX | PROC-SP-002 | Quality attributes and architectural constraints |
| Methodology | `methodology/` | — | PROC-ORG-001 | Requirements derivation, evidence quality, coverage |
| Compliance | `compliance/` | — | PROC-GOV-* | Control mappings and customer deliverables (gov overlay) |

## ID Namespace Reference

| Prefix | Directory | Example Filename |
|--------|-----------|-----------------|
| REQ-XXX | requirements/ | `REQ-001-domain-knowledge-injection.md` |
| ADR-XXX | architecture/decisions/ | `ADR-001-context-engineering.md` |
| SPEC-XXX | specs/ | `SPEC-001-session-logging.md` |
| TEST-XXX | testing/evidence/ | `TEST-001-v0.11-release.md` |
| REG-XXX | testing/regression/ | `REG-001-install-credential-fix.md` |
| BM-XXX | benchmarks/ | `BM-001-baseline-raw-claude.md` |
| INC-XXX | operations/incidents/ | `INC-001-encryption-key-rotation.md` |
| RB-XXX | operations/runbooks/ | `RB-001-release-process.md` |
| MIG-XXX | operations/migration/ | `MIG-001-v010-to-v011.md` |
| QA-XXX | quality/ | `QA-001-soc2-certification.md` |

## Cross-Reference Format

When referencing documents from other layers, use the format:

```
See REQ-001 (Domain Knowledge Injection)
```

Include the document title in parentheses for readability. The validation script
checks that referenced IDs resolve to real files.

## Creating New Documents

1. Identify the governing process in `qms/CATALOG.md`
2. Check the process's Section 6 (Outputs/Artifacts) for the required template
3. Determine the next sequential ID in the target directory
4. Name the file `<ID>-<short-description>.md` (lowercase, hyphens)
5. Include a `## Traces` section linking to upstream and downstream documents
6. Run `bash scripts/validate-docs.sh` to verify structural compliance

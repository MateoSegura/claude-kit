# docs/ — Project Documentation

claude-kit maintains a structured documentation system organized into seven layers.
Each layer has a dedicated directory, ID namespace, and document template.

## Traceability Chain

```
research/ → requirements/ → architecture/ → plans/ → code → testing/ → benchmarks/
                                                                ↑
                                                        operations/ (cross-cutting)
```

Documents trace forward (research motivates requirements, requirements drive
architecture decisions) and backward (test evidence validates plans, plans
reference the requirements they fulfill).

## Layer Summary

| Layer | Directory | ID Prefix | Purpose |
|-------|-----------|-----------|---------|
| Research | `research/` | — | Theoretical papers and exploration |
| Requirements | `requirements/` | REQ-XXX | What the system must do and why |
| Architecture | `architecture/` | ADR-XXX | Decisions and component documentation |
| Plans | `plans/` | PLAN-XXX | Version-scoped implementation plans |
| Testing | `testing/` | TEST-XXX, REG-XXX | Evidence and regression documentation |
| Benchmarks | `benchmarks/` | BM-XXX | Methodology, baselines, and results |
| Operations | `operations/` | INC-XXX, RB-XXX, MIG-XXX | Incidents, runbooks, migrations |

## ID Namespace Reference

| Prefix | Directory | Example Filename |
|--------|-----------|-----------------|
| REQ-XXX | requirements/ | `REQ-001-plugin-encryption.md` |
| ADR-XXX | architecture/decisions/ | `ADR-001-single-file-cli.md` |
| PLAN-XXX | plans/ | `PLAN-001-session-logging.md` |
| TEST-XXX | testing/evidence/ | `TEST-001-v0.11-release.md` |
| REG-XXX | testing/regression/ | `REG-001-install-credential-fix.md` |
| BM-XXX | benchmarks/ | `BM-001-baseline-raw-claude.md` |
| INC-XXX | operations/incidents/ | `INC-001-encryption-key-rotation.md` |
| RB-XXX | operations/runbooks/ | `RB-001-release-process.md` |
| MIG-XXX | operations/migration/ | `MIG-001-v010-to-v011.md` |

## Cross-Reference Format

When referencing documents from other layers, use the format:

```
See REQ-001 (Plugin Encryption at Rest)
```

Include the document title in parentheses for readability. The validation script
checks that referenced IDs resolve to real files.

## Creating New Documents

1. Check the target layer's `INDEX.md` for the document template
2. Determine the next sequential ID (e.g., if REQ-003 exists, use REQ-004)
3. Name the file `<ID>-<short-description>.md` (lowercase, hyphens)
4. Include a `## Traces` section linking to upstream and downstream documents
5. Run `bash scripts/validate-docs.sh` to verify structural compliance

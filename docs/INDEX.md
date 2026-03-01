# docs/ — Project Documentation

claude-kit's documentation lives here. Research papers, architecture decisions,
specs, and quality attributes are tracked as markdown. Requirements are tracked
as GitHub Issues with the `requirement` label.

## Structure

| Directory | ID Prefix | Purpose |
|-----------|-----------|---------|
| `research/` | — | Theoretical papers and exploration |
| `architecture/decisions/` | ADR-XXX | Architecture Decision Records |
| `architecture/components/` | — | Component documentation |
| `specs/` | SPEC-XXX | Version-scoped implementation specs |
| `quality/` | QA-XXX | Quality attributes and architectural constraints |
| `methodology/` | — | Engineering guides (derivation, evidence, coverage) |

## Creating New Documents

1. Determine the next sequential ID in the target directory
2. Name the file `<ID>-<short-description>.md` (lowercase, hyphens)
3. Run `bash scripts/validate-docs.sh` to verify structural compliance

## ADR Immutability

Never edit an accepted ADR. Create a new ADR and set the original's status
to `superseded-by ADR-YYY`.

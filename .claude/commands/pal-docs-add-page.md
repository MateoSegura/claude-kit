---
description: Add a new documentation page with full nav wiring and validation
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# /pal-docs-add-page -- Add a New Documentation Page

You are adding a new page to the documentation site. Follow this workflow
exactly.

## Workflow

### Step 1: Identify the target layer

Ask the user which documentation layer they want to add to:

| Layer | Directory | ID Pattern | Template |
|-------|-----------|------------|----------|
| Research | `docs/research/` | -- (no prefix) | `templates/research-doc.md.tmpl` |
| Requirements | `docs/requirements/` | REQ-XXX | `templates/requirement.md.tmpl` |
| Architecture Decisions | `docs/architecture/decisions/` | ADR-XXX | `templates/adr.md.tmpl` |
| Architecture Components | `docs/architecture/components/` | -- | `templates/component-doc.md.tmpl` |
| Specs | `docs/specs/` | SPEC-XXX | `templates/spec.md.tmpl` |
| Quality | `docs/quality/` | QA-XXX | `templates/quality-attribute.md.tmpl` |
| Test Evidence | `docs/testing/evidence/` | TEST-XXX | `templates/test-evidence.md.tmpl` |
| Regression | `docs/testing/regression/` | REG-XXX | `templates/regression-report.md.tmpl` |
| Benchmarks | `docs/benchmarks/` | BM-XXX | `templates/benchmark-report.md.tmpl` |
| Incidents | `docs/operations/incidents/` | INC-XXX | `templates/incident.md.tmpl` |
| Runbooks | `docs/operations/runbooks/` | RB-XXX | `templates/runbook.md.tmpl` |
| Migration | `docs/operations/migration/` | MIG-XXX | `templates/migration-plan.md.tmpl` |
| Methodology | `docs/methodology/` | -- | Free-form |

### Step 2: Determine the next ID

For layers with ID patterns, scan the existing files to find the next
sequential number:

```bash
ls docs/<layer>/ | grep -oP '<PREFIX>-\d+' | sort -t- -k2 -n | tail -1
```

### Step 3: Generate the file

If a PAL template exists for this layer, use it (read the `.tmpl` file and
fill in all sections). Otherwise, create a standard markdown file with:
- H1 title matching the ID and description
- All sections required by the governing process

### Step 4: Update mkdocs.yml nav

Read `docs-site/mkdocs.yml` and add the new file to the correct nav
section. The path should be relative to the merged content directory:

- `processes/` files -> `processes/<path>`
- `mappings/` files -> `mappings/<path>`

### Step 5: Validate

```bash
bash docs-site/validate-site.sh --nav
```

### Step 6: Report

Tell the user:
- File created at `<path>`
- Nav updated in `docs-site/mkdocs.yml`
- Validation result
- Reminder to run `bash scripts/validate-docs.sh` for full docs validation

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

# /qms-docs-add-page — Add a New Documentation Page

You are adding a new page to the documentation site. Follow this workflow
exactly.

## Workflow

### Step 1: Identify the target layer

Ask the user which documentation layer they want to add to:

| Layer | Directory | ID Pattern | Template |
|-------|-----------|------------|----------|
| Research | `docs/research/` | — (no prefix) | Free-form |
| Requirements | `docs/requirements/` | REQ-XXX | `qms/templates/requirement.md.tmpl` |
| Architecture | `docs/architecture/decisions/` | ADR-XXX | `qms/templates/adr.md.tmpl` |
| Quality | `docs/quality/` | QA-XXX | `qms/templates/quality-attribute.md.tmpl` |
| Testing | `docs/testing/evidence/` | TEST-XXX | `qms/templates/test-evidence.md.tmpl` |
| Operations | `docs/operations/incidents/` | INC-XXX | `qms/templates/incident.md.tmpl` |
| Methodology | `docs/methodology/` | — | Free-form |

### Step 2: Determine the next ID

For layers with ID patterns, scan the existing files to find the next
sequential number:

```bash
ls docs/<layer>/ | grep -oP '<PREFIX>-\d+' | sort -t- -k2 -n | tail -1
```

### Step 3: Generate the file

If a QMS template exists for this layer, use it (read the `.tmpl` file and
fill in all sections). Otherwise, create a standard markdown file with:
- H1 title matching the ID and description
- All sections required by the governing process

### Step 4: Update mkdocs.yml nav

Read `qms/docs-site/mkdocs.yml` and add the new file to the correct nav
section. The path should be relative to the merged content directory:

- `docs/` files → `docs/<path>`
- `qms/processes/` files → `processes/<path>`

### Step 5: Validate

```bash
bash qms/docs-site/validate-site.sh --nav
```

### Step 6: Report

Tell the user:
- File created at `<path>`
- Nav updated in `qms/docs-site/mkdocs.yml`
- Validation result
- Reminder to run `bash scripts/validate-docs.sh` for full docs validation

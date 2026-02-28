# Artifact Management — QMS Rule

This rule teaches the AI agent how to create, update, and deprecate
process-governed artifacts. It is installed by `qms/install.sh`.

## Creating a New Artifact

Follow this workflow when creating any document in `docs/`:

### Step 1: Identify the Governing Process

Look up the target directory in the process governance mapping:

| Directory | Process | Template |
|-----------|---------|----------|
| `docs/requirements/` | PROC-LC-002 | `qms/templates/requirement.md.tmpl` |
| `docs/architecture/decisions/` | PROC-LC-003 | `qms/templates/adr.md.tmpl` |
| `docs/specs/` | PROC-LC-004 | `qms/templates/spec.md.tmpl` |
| `docs/testing/evidence/` | PROC-LC-005 | `qms/templates/test-evidence.md.tmpl` |
| `docs/quality/` | PROC-SP-002 | `qms/templates/quality-attribute.md.tmpl` |
| `docs/operations/incidents/` | PROC-LC-007 | `qms/templates/incident.md.tmpl` |

### Step 2: Check Entry Criteria

Read the governing process's Section 3 (Entry Criteria). Common prerequisites:
- Upstream artifact exists (e.g., a REQ must exist before writing an ADR)
- Stakeholder need has been identified
- Previous process outputs are available

### Step 3: Generate from Template

Use the template specified by the process. Fill in all sections — do not leave
placeholder text. Key rules:
- **ID:** Use the next sequential number in the target directory
- **Filename:** `<ID>-<short-description>.md` (lowercase, hyphens)
- **Traces section:** Must link upstream and downstream documents

### Step 4: Verify Quality Gates

After writing, check the process's Section 8 (Quality Gates):
- Does the artifact follow the template structure?
- Are all required sections present and non-empty?
- Are cross-references valid (IDs resolve to real files)?
- Is the Status field set to a valid value?

### Step 5: Validate

```bash
bash scripts/validate-docs.sh    # Structural validation
```

## Updating an Existing Artifact

1. Check if the artifact's governing process allows in-place edits
   - **ADRs:** Never edit accepted ADRs (create a new one and supersede)
   - **All others:** Edit in place, update the Status field if needed
2. Verify cross-references still resolve after the edit
3. Update downstream documents if the change affects them

## Deprecating an Artifact

1. Set Status to `deprecated` or `superseded-by <ID>`
2. Update the governing process's Section 6 if the artifact type is removed
3. Keep the file in place — do not delete deprecated artifacts
4. Update any documents that reference the deprecated artifact

## Template Compliance Checklist

When creating any governed artifact, verify:

- [ ] File is in the correct directory per the governing process
- [ ] Filename follows the `<ID>-<short-description>.md` pattern
- [ ] All template sections are present and filled in
- [ ] Status field contains a valid value for the document type
- [ ] Traces section links to upstream and downstream documents
- [ ] ID is unique across all documents (no duplicates)
- [ ] `bash scripts/validate-docs.sh` passes without failures

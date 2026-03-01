# Artifact Management — PAL Rule

This rule teaches the AI agent how to create, update, and deprecate
process-governed artifacts. It is installed by the PAL `install.sh`.

## Creating a New Artifact

Follow this workflow when creating any document in `docs/`:

### Step 1: Identify the Governing Process

Look up the target directory in the process governance mapping:

| Template | Artifact | ID Pattern | Governing Process |
|----------|----------|------------|-------------------|
| `requirement.md.tmpl` | Requirement | REQ-XXX | PROC-LC-002 |
| `adr.md.tmpl` | Architecture Decision | ADR-XXX | PROC-LC-003 |
| `spec.md.tmpl` | Implementation Spec | SPEC-XXX | PROC-LC-004 |
| `test-evidence.md.tmpl` | Test Evidence | TEST-XXX | PROC-LC-005 |
| `regression-report.md.tmpl` | Regression Report | REG-XXX | PROC-LC-005 |
| `incident.md.tmpl` | Incident Report | INC-XXX | PROC-SEC-003 |
| `runbook.md.tmpl` | Runbook | RB-XXX | PROC-LC-007 |
| `migration-plan.md.tmpl` | Migration Plan | MIG-XXX | PROC-LC-007 |
| `benchmark-report.md.tmpl` | Benchmark Report | BM-XXX | PROC-ORG-002 |
| `component-doc.md.tmpl` | Component Doc | -- | PROC-LC-003 |
| `research-doc.md.tmpl` | Research Doc | -- | PROC-LC-001 |
| `quality-attribute.md.tmpl` | Quality Attribute | QA-XXX | PROC-SP-002 |
| `process.md.tmpl` | Process Document | PROC-XX-NNN | -- |

Templates are located in the PAL repository's `templates/` directory.

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

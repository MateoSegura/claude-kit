---
description: Create a new process-governed artifact with template compliance
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
---

# Create New Governed Artifact

Interactive workflow to create a new document in `docs/` that complies with
its governing process and template.

## Steps

1. **Ask the user what type of artifact to create:**
   Use AskUserQuestion with options:
   - Requirement (REQ-XXX) → governed by PROC-LC-002
   - Architecture Decision (ADR-XXX) → governed by PROC-LC-003
   - Spec (SPEC-XXX) → governed by PROC-LC-004
   - Test Evidence (TEST-XXX) → governed by PROC-LC-005
   - Quality Attribute (QA-XXX) → governed by PROC-SP-002
   - Incident Report (INC-XXX) → governed by PROC-LC-007
   - Benchmark (BM-XXX) → governed by PROC-ORG-002

2. **Determine the next sequential ID:**
   - Scan the target directory for existing files
   - Find the highest existing ID number
   - Assign the next number (e.g., if REQ-010 exists, use REQ-011)

3. **Ask the user for the artifact title:**
   - Use AskUserQuestion for a short description
   - Generate the filename: `<ID>-<short-description>.md`

4. **Read the governing process:**
   - Open the process document from `qms/processes/`
   - Check Section 3 (Entry Criteria) — warn if prerequisites aren't met
   - Read Section 6 (Outputs/Artifacts) for the template reference

5. **Read the template:**
   - Open the template from `qms/templates/`
   - Fill in the header fields (ID, title, status=draft, governing process)

6. **Ask the user for content:**
   - Walk through each template section
   - Ask for the key content (statement, rationale, traces)
   - Fill in automatically where possible (date, ID, governing process)

7. **Write the file:**
   - Write to the correct `docs/` directory
   - Verify the file follows the template structure

8. **Validate:**
   - Run `bash scripts/validate-docs.sh`
   - Report any issues

9. **Report:**
   - Show the created file path
   - Show the governing process reference
   - List any cross-references that were added

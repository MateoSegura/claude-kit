# PROC-SP-004: Documentation Management

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** Documentation Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Documentation Management governs the creation, maintenance, and validation of all structured documentation in claude-kit's `docs/` directory. This process ensures that the 10-layer documentation system maintains structural integrity, that every document has proper ID allocation, cross-references, INDEX entries, and Traces sections, and that the `validate-docs.sh` script can enforce these rules automatically. Without this process, the documentation system degrades into disconnected files that cannot support traceability.

## 2. Scope

**Included:**
- Creation and maintenance of documents across all 10 documentation layers
- INDEX.md file maintenance in each top-level `docs/` subdirectory
- ID namespace management (REQ-XXX, ADR-XXX, SPEC-XXX, TEST-XXX, REG-XXX, BM-XXX, INC-XXX, RB-XXX, MIG-XXX, QA-XXX)
- Cross-reference integrity between documents
- Traces section maintenance in every ID-bearing document
- Documentation structure validation via `validate-docs.sh`

**Excluded:**
- Content quality of individual documents (governed by the process that owns each layer)
- Plugin README files (governed by `.claude/rules/documentation.md`)
- QMS process documents (governed by the QMS framework)

## 3. Entry Criteria

- [ ] The `docs/` directory structure exists with subdirectories for each layer
- [ ] INDEX.md files exist in each top-level `docs/` subdirectory
- [ ] `scripts/validate-docs.sh` is functional and integrated into CI

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Documentation system rules | `.claude/rules/docs-system.md` | Markdown rule file |
| Documentation conventions | `.claude/rules/documentation.md` | Markdown rule file |
| Document templates | `qms/templates/` | Markdown templates (`.md.tmpl`) |
| Validation script | `scripts/validate-docs.sh` | Bash script |
| Existing documents | `docs/` (all subdirectories) | Markdown documents with ID prefixes |

## 5. Activities

### 5.1 Select Document Layer and Template

When creating a new document, determine which layer it belongs to:

| Layer | Directory | ID Prefix | Template |
|-------|-----------|-----------|----------|
| Research | `docs/research/` | — (no prefix) | None (free-form) |
| Requirements | `docs/requirements/` | REQ-XXX | `requirement.md.tmpl` |
| Architecture (decisions) | `docs/architecture/decisions/` | ADR-XXX | `adr.md.tmpl` |
| Architecture (components) | `docs/architecture/components/` | — | None |
| Specs | `docs/specs/` | SPEC-XXX | `spec.md.tmpl` |
| Testing (evidence) | `docs/testing/evidence/` | TEST-XXX | `test-evidence.md.tmpl` |
| Testing (regression) | `docs/testing/regression/` | REG-XXX | None |
| Benchmarks | `docs/benchmarks/` | BM-XXX | None |
| Constraints | `docs/quality/` | QA-XXX | `quality-attribute.md.tmpl` |
| Methodology | `docs/methodology/` | — (no prefix) | None |
| Operations (incidents) | `docs/operations/incidents/` | INC-XXX | `incident.md.tmpl` |
| Operations (runbooks) | `docs/operations/runbooks/` | RB-XXX | None |
| Operations (migration) | `docs/operations/migration/` | MIG-XXX | None |

### 5.2 Allocate Document ID

For layers that use ID prefixes, allocate the next sequential ID:
1. Check existing files in the target directory for the highest existing number
2. Increment by 1
3. Name the file `<ID>-<short-description>.md` (lowercase, hyphens)

IDs must be globally unique across all namespaces. The `validate-docs.sh` script (Check 2) enforces this — a duplicate ID in any layer causes a failure.

### 5.3 Write Document Content

Use the appropriate template from `qms/templates/` to structure the document. Every ID-bearing document must include:
- A `## Traces` section with upstream and downstream links
- Cross-references in the format `See REQ-NNN (Title)` for validation
- A `Status` field with a valid value for the document type

### 5.4 Update INDEX File

Add the new document to the `INDEX.md` file in the target directory. The INDEX serves as a table of contents for the layer. Each entry includes the document ID, title, status, and any relevant metadata.

### 5.5 Validate Structure

Run the documentation validation script:

```bash
bash scripts/validate-docs.sh
```

The script checks:
1. INDEX.md exists in each top-level `docs/` subdirectory
2. Document IDs are globally unique
3. Filenames match their directory's ID pattern
4. Cross-references resolve to real files
5. Status fields contain valid values
6. Documents contain a required `## Traces` section

All checks must pass (exit code 0) before committing.

### 5.6 Maintain Cross-References

When modifying a document, check whether any cross-references to or from other documents need updating. If a document's status changes (e.g., a SPEC moves from `active` to `completed`), update all documents that reference it.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Layer-specific documents | `docs/*/` | Various (see 5.1) | Layer-specific prefix |
| INDEX files | `docs/*/INDEX.md` | — | — |
| Validation results | CI pipeline output | — | — |

## 7. Exit Criteria

- [ ] New document exists in the correct layer directory with proper filename
- [ ] Document ID is globally unique
- [ ] Traces section is present with at least one upstream or downstream link
- [ ] INDEX.md in the target directory has been updated
- [ ] `bash scripts/validate-docs.sh` passes with exit code 0
- [ ] Cross-references from/to other documents are consistent

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Structural integrity | `bash scripts/validate-docs.sh` | Exit code 0 — all 6 checks pass |
| ID uniqueness | `validate-docs.sh` Check 2 | No duplicate IDs across any layer |
| Cross-reference integrity | `validate-docs.sh` Check 4 | All referenced IDs resolve to real files |
| Traces presence | `validate-docs.sh` Check 6 | Every ID-bearing document has a `## Traces` section |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Documentation Lead | Maintains INDEX files, audits cross-reference integrity, reviews structural compliance |
| Developer | Creates documents using correct templates, maintains Traces sections |
| CI System | Runs `validate-docs.sh` on every push via `fast-validate` |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Docs validation pass rate | Percentage of pushes where `validate-docs.sh` passes | > 95% | CI workflow history |
| INDEX completeness | Percentage of ID-bearing documents listed in their INDEX.md | 100% | Manual audit of INDEX files vs directory contents |
| Cross-reference resolution rate | Percentage of cross-references that resolve to real files | 100% | `validate-docs.sh` Check 4 output |
| Orphan document rate | Number of ID-bearing documents with empty Traces sections | 0 | `validate-docs.sh` Check 6 output |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.6.3.4 Configuration Status Accounting | INDEX files implement status accounting for documentation items |
| ISO/IEC 12207:2017 | 6.3.1 Documentation Management | This process directly implements documentation management |
| CMMI-DEV v2.0 | CM (Configuration Management) | Covers CM SP 3.1 (establish configuration management records) for documentation |

## 12. Tailoring Guidance

**Minimum viable process (single document):** Create the document in the correct directory with the correct filename and ID. The Traces section is mandatory even for single documents. Run `validate-docs.sh` before committing.

**Full ceremony (new layer):** When adding a new documentation layer, create the subdirectory, add an INDEX.md, update `validate-docs.sh` to recognize the new ID prefix, and update `.claude/rules/docs-system.md` to document the layer.

**Research documents:** Research layer documents (`docs/research/`) do not use ID prefixes and have no structural requirements beyond being valid Markdown. They are exempt from ID uniqueness and Traces checks.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-002 | Related: Requirements Engineering produces REQ-XXX documents managed by this process |
| PROC-LC-003 | Related: Architecture Design produces ADR-XXX documents managed by this process |
| PROC-LC-005 | Related: Integration & Testing produces TEST-XXX and REG-XXX documents managed by this process |
| PROC-SP-002 | Related: Quality Assurance uses documentation integrity as a quality indicator |
| PROC-SP-001 | Extends: Configuration Management treats documentation as configuration items |

## 14. Traces

- **Governs:** All files in `docs/` (all layers), `docs/*/INDEX.md` files
- **Enforced by:** `scripts/validate-docs.sh` (structural validation), `push.yml` (`fast-validate` includes docs validation), `.claude/rules/docs-system.md` (documentation system rules)
- **Related QA:** Documentation integrity rules in `.claude/rules/docs-system.md`, document template requirements in `qms/templates/`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing 10-layer documentation system with validation |

# PROC-ORG-001: Process Governance

**Version:** 1.0.0
**Status:** draft
**Category:** organizational
**Layer:** base
**Maturity:** initial
**Owner:** Quality Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Process Governance is the meta-process that governs the creation, review, approval, maturity assessment, and retirement of all other processes in the claude-kit Quality Management System. It ensures that processes are consistent in structure, traceable to the artifacts they govern, and maintained at a maturity level appropriate to the project's needs. Without this process, the QMS would lack coherence — individual processes would drift in format, overlap in scope, or become stale.

## 2. Scope

**Included:**
- Creation of new process documents using the standard template (`qms/templates/process.md.tmpl`)
- Periodic review of existing processes for accuracy and relevance
- Maturity assessment using the levels defined in `qms/MATURITY-MODEL.md`
- Process retirement when a process is no longer applicable
- Maintenance of the process catalog (`qms/CATALOG.md`)
- Governance of the `docs/methodology/` layer that documents meta-process decisions

**Excluded:**
- The content of individual processes (each process is owned by its designated Owner)
- Tooling implementation (handled by the relevant lifecycle or support process)
- Standards compliance auditing (handled by PROC-GOV-008 in the government overlay)

## 3. Entry Criteria

- [ ] A need for a new process has been identified (gap analysis, incident, or standards requirement)
- [ ] An existing process is due for scheduled review (every 6 months after initial approval)
- [ ] A process maturity assessment has been requested
- [ ] A process is proposed for retirement due to obsolescence or consolidation

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Process template | `qms/templates/process.md.tmpl` | Markdown template |
| Process catalog | `qms/CATALOG.md` | Markdown table |
| Maturity model | `qms/MATURITY-MODEL.md` | Maturity level definitions |
| Version policy | `qms/VERSION-POLICY.md` | Versioning rules |
| Methodology documents | `docs/methodology/` | Process meta-documentation |
| Improvement proposals | PROC-LC-008 outputs | GitHub Issues with `improvement` label |
| Standards requirements | Standards mapping documents in `qms/mappings/` | Mapping tables |

## 5. Activities

### 5.1 Process Creation

When a gap is identified (a necessary activity lacks a governing process), create a new process document:

1. Determine the appropriate category (lifecycle, support, organizational, security) and assign the next sequential ID within that category
2. Copy `qms/templates/process.md.tmpl` to the correct directory under `qms/processes/base/`
3. Fill in all 15 sections — no TBD placeholders allowed at initial publication
4. Set status to `draft` and maturity to `initial`
5. Add the process to `qms/CATALOG.md`
6. Submit for peer review via PR

### 5.2 Process Review

Every 6 months after a process reaches `active` status, or when triggered by a significant change in the governed area:

1. Read the process document end-to-end and verify that each section still reflects actual practice
2. Check that all file paths and cross-references in Section 6 and Section 14 are still valid
3. Verify that metrics in Section 10 are being collected and targets are still appropriate
4. Update the `Last Reviewed` date in the header
5. If substantive changes are needed, increment the version per `qms/VERSION-POLICY.md`

### 5.3 Maturity Assessment

Evaluate a process against the maturity model defined in `qms/MATURITY-MODEL.md`:

1. Gather evidence of process execution (artifacts produced, metrics collected, reviews completed)
2. Assess against the criteria for each maturity level: initial, managed, defined, measured, optimizing
3. Record the assessment result in the process header and in `qms/CATALOG.md`
4. If the process does not meet its current declared level, either downgrade or create an improvement action

### 5.4 Process Approval

Move a process from `draft` to `active` status when:

1. All 15 sections are complete with real content
2. At least one execution cycle has been performed (the process has been followed at least once)
3. The Quality Lead has reviewed and approved the document
4. The process catalog has been updated

### 5.5 Process Retirement

When a process is no longer needed (consolidated into another process, or the governed activity has been eliminated):

1. Set the process status to `retired`
2. Add a note in Section 1 explaining why and pointing to the replacement (if any)
3. Update `qms/CATALOG.md` to reflect the retired status
4. Do not delete the file — retired processes remain as historical records

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Process documents | `qms/processes/base/<category>/` | `process.md.tmpl` | PROC-XXX-NNN |
| Process catalog | `qms/CATALOG.md` | — | — |
| Maturity assessments | Embedded in process headers | — | — |
| Methodology documents | `docs/methodology/` | — | No ID prefix |

## 7. Exit Criteria

- [ ] Process document follows the 15-section template structure completely
- [ ] Process is recorded in `qms/CATALOG.md` with correct ID, version, status, and maturity
- [ ] All cross-references to other processes (Section 13) resolve to real PROC-XXX-NNN documents
- [ ] All file paths in Sections 6 and 14 point to existing directories or files
- [ ] PR review completed by at least one person other than the author

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Template compliance | Manual review against `process.md.tmpl` | All 15 sections present with substantive content; no placeholder text |
| Cross-reference validity | Check each PROC-XXX-NNN reference in Section 13 | Every referenced process exists in `qms/CATALOG.md` |
| Catalog consistency | Compare process header fields to CATALOG.md row | ID, version, status, and maturity match between document and catalog |
| Scope non-overlap | Compare Section 2 with related processes | No two active processes govern the same artifact or activity |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Quality Lead | Owns this meta-process; approves process transitions (draft to active, active to retired); conducts maturity assessments |
| Process Owner | Each process has a designated Owner responsible for its content accuracy and periodic review |
| Technical Lead | Reviews process documents for technical accuracy; ensures processes are feasible given current tooling |
| Developer | Follows processes during daily work; provides feedback on process effectiveness |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Process coverage | Percentage of identified process areas with an active process document | 100% of base layer | Audit `qms/CATALOG.md` |
| Review currency | Percentage of active processes reviewed within the last 6 months | >= 80% | Check `Last Reviewed` dates |
| Catalog accuracy | Number of discrepancies between process headers and CATALOG.md | 0 | Automated comparison script |
| Draft-to-active conversion | Average time from process creation (draft) to approval (active) | < 60 days | Git log analysis on process files |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 7.2.1 Life cycle model management | Governance of process lifecycle from creation to retirement |
| ISO/IEC 33001 | Process assessment | Maturity model alignment for process capability assessment |
| CMMI | OPD (Organizational Process Definition) | Maintaining the organization's set of standard processes |
| NIST SP 800-218 | PO.1 | Organizational preparation for secure development processes |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Maintain process documents in their directories with the standard template. Skip formal maturity assessments — use `initial` for new processes and `managed` for processes you follow consistently. Review processes annually instead of every 6 months.

**Full ceremony (team with quality function):** Execute all activities including quarterly maturity assessments, formal approval workflows, and tracked review schedules. Maintain a process improvement backlog fed by maturity assessment gaps.

**When to simplify:** If the QMS has fewer than 10 processes, skip the formal retirement workflow — just mark the document as retired and update the catalog. The full retirement workflow becomes valuable when the process inventory is large enough that stale documents cause confusion.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-008 | Receives from: improvement proposals may create or modify processes; feeds into: process changes are a type of improvement |
| PROC-ORG-002 | Related: measurement data informs maturity assessments; process metrics feed Measurement & Analysis |
| PROC-ORG-003 | Related: process changes may trigger training needs |
| PROC-SP-004 | Related: process documents are a type of documentation governed by Documentation Management |
| PROC-SP-002 | Related: process compliance is a quality assurance concern |

## 14. Traces

- **Governs:** `qms/processes/` (all process documents), `qms/CATALOG.md`, `qms/MATURITY-MODEL.md`, `docs/methodology/`
- **Enforced by:** PR review process (manual); catalog consistency check (planned automation)
- **Related QA:** Process maturity, documentation completeness, governance traceability

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — establishes the meta-process for governing all QMS processes |

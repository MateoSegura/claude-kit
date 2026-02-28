# PROC-LC-002: Requirements Engineering

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** Product Owner
**Last Reviewed:** 2026-02-28

## 1. Purpose

Requirements Engineering defines how stakeholder needs are identified, analyzed, and formalized into traceable requirement documents within claude-kit. This process ensures that every product capability is grounded in empirical evidence from the research layer and linked to downstream architecture decisions and implementation specs. Without it, features risk being untethered from real user problems and impossible to verify.

## 2. Scope

**Included:**
- Elicitation of stakeholder needs from research papers, market analysis, and user feedback
- Derivation of formal requirement documents (REQ-XXX) in `docs/requirements/`
- Traceability from research layer through requirements to architecture decisions
- Maintenance and status tracking of requirement documents across versions

**Excluded:**
- Architecture decisions (governed by PROC-LC-003)
- Implementation planning and spec authoring (governed by PROC-LC-004)
- Quality attribute constraints (documented in `docs/quality/`)

## 3. Entry Criteria

- [ ] Research layer (`docs/research/`) contains at least one relevant paper or analysis that motivates the requirement
- [ ] The stakeholder need or problem statement has been articulated in writing
- [ ] The methodology for requirements derivation has been reviewed (see `docs/methodology/requirements-derivation.md`)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Research papers | `docs/research/` | Markdown research documents |
| Requirements derivation methodology | `docs/methodology/requirements-derivation.md` | Markdown methodology document |
| Evidence quality framework | `docs/methodology/evidence-quality.md` | Markdown grading criteria |
| Existing requirements | `docs/requirements/REQ-*.md` | Markdown REQ documents |
| Stakeholder feedback | GitHub Issues, PR discussions | Unstructured text |

## 5. Activities

### 5.1 Identify Stakeholder Needs

Review the research layer (`docs/research/`) for empirical findings that expose gaps or opportunities. Cross-reference with the coverage analysis (`docs/methodology/coverage-analysis.md`) to identify areas where no requirement yet exists. Consult GitHub Issues for user-reported needs.

### 5.2 Derive Requirement from Evidence

Follow the four-stage derivation process documented in `docs/methodology/requirements-derivation.md`:
1. Evidence gathering — collect peer-reviewed sources and empirical data
2. Problem framing — articulate the specific problem the requirement solves
3. Requirement statement — write a testable, unambiguous requirement
4. Evidence grading — assign a confidence level per `docs/methodology/evidence-quality.md`

### 5.3 Write REQ Document

Create a new file in `docs/requirements/` using the naming convention `REQ-<NNN>-<short-description>.md`. Use the requirement template (`qms/templates/requirement.md.tmpl`) and populate all sections: Context, Requirement, Acceptance Criteria, and Traces.

Assign the next sequential ID after the highest existing REQ number. Set `Status: proposed` initially.

### 5.4 Establish Traceability

In the `## Traces` section of the new REQ document:
- Link upstream to the research documents that provide evidence
- Link downstream to any ADRs or SPECs that will implement the requirement
- Ensure all cross-references use the format `See REQ-NNN (Title)` so that `validate-docs.sh` can verify them

### 5.5 Review and Approve

Submit the REQ document via a branch and PR following the git workflow (PROC-SP-001). The requirement must be reviewed for completeness, testability, and evidence quality. Once approved, update `Status: active`.

### 5.6 Update INDEX

Add the new requirement to `docs/requirements/INDEX.md` with its ID, title, status, and priority.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Requirement document | `docs/requirements/` | `requirement.md.tmpl` | REQ-XXX |
| Updated INDEX | `docs/requirements/INDEX.md` | — | — |

## 7. Exit Criteria

- [ ] REQ document exists in `docs/requirements/` with all sections populated
- [ ] ID is globally unique (no collision with existing REQ, ADR, SPEC, or TEST IDs)
- [ ] Traces section links to at least one upstream research document
- [ ] `bash scripts/validate-docs.sh` passes with no failures for the new document
- [ ] REQ appears in `docs/requirements/INDEX.md`
- [ ] PR has been reviewed and merged

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Evidence grounding | Manual review of Context section | At least one cited research paper or empirical data source with specific findings |
| Testability check | Review of Acceptance Criteria | Each acceptance criterion is binary (pass/fail) and automatable or manually verifiable |
| Structural validation | `bash scripts/validate-docs.sh` | Exit code 0 — no missing Traces, no duplicate IDs, filename matches ID |
| Cross-reference integrity | `validate-docs.sh` Check 4 | All referenced document IDs resolve to real files |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Product Owner | Identifies stakeholder needs, prioritizes requirements, approves final REQ documents |
| Developer | Drafts REQ documents from research evidence, establishes traces, submits PR |
| Reviewer | Validates evidence quality, testability, and completeness during PR review |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Requirements coverage | Percentage of research findings that trace to at least one REQ | > 80% | Cross-reference `docs/research/` against `docs/requirements/` Traces sections |
| Evidence quality score | Average evidence grade across all active REQs per `evidence-quality.md` | Grade B or above | Manual audit during weekly review |
| Trace completeness | Percentage of REQs with both upstream (research) and downstream (ADR/SPEC) traces | 100% for active REQs | `validate-docs.sh` cross-reference checks |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.2 Stakeholder Needs and Requirements Definition | This process directly implements stakeholder requirements definition |
| ISO/IEC 12207:2017 | 6.4.3 System/Software Requirements Analysis | Activities 5.2-5.4 implement requirements analysis and traceability |
| CMMI-DEV v2.0 | RD (Requirements Development) | Covers RD SP 1.1 (elicitation) through SP 3.5 (validation) |

## 12. Tailoring Guidance

**Minimum viable process (small change):** When adding a single requirement driven by a clear user need, the derivation methodology review (Activity 5.2 stage 4) may be abbreviated. The evidence grading is still required but a single strong source suffices.

**Full ceremony (major feature):** When defining requirements for a new product area, all four derivation stages must be executed in full, the coverage analysis must be updated, and a dedicated review session should be held before the PR is opened.

**Research-first variant:** For exploratory work, a research document may be written first in `docs/research/` and the REQ derived later. The research document serves as a provisional input until the formal REQ is approved.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-003 | Feeds into: approved REQs drive architecture decisions (ADRs) |
| PROC-LC-004 | Feeds into: REQs are referenced by implementation SPECs |
| PROC-SP-003 | Depends on: Verification & Validation confirms REQs are met |
| PROC-SP-004 | Extends: Documentation Management governs the docs/ structure REQs live in |
| PROC-SP-006 | Depends on: Peer Review validates REQ quality during PR review |

## 14. Traces

- **Governs:** `docs/requirements/REQ-*.md`, `docs/requirements/INDEX.md`
- **Enforced by:** `scripts/validate-docs.sh` (structural validation), `fast-validate` CI job (push.yml), `pr-validate` CI job (pr.yml)
- **Related QA:** Evidence quality framework in `docs/methodology/evidence-quality.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing requirements engineering practice with 10 active REQs |

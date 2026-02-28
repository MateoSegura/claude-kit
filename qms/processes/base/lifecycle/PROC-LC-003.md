# PROC-LC-003: Architecture Design

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** Lead Architect
**Last Reviewed:** 2026-02-28

## 1. Purpose

Architecture Design governs how architectural decisions are made, documented, and preserved in claude-kit. This process ensures that every significant design choice is captured as an immutable Architecture Decision Record (ADR), evaluated against alternatives, and traced to the requirements it satisfies. The immutability rule prevents silent erosion of past reasoning while allowing decisions to be superseded through a controlled process.

## 2. Scope

**Included:**
- Creation of Architecture Decision Records (ADR-XXX) in `docs/architecture/decisions/`
- Maintenance of component documentation in `docs/architecture/components/`
- Evaluation of design alternatives for significant structural choices
- Supersession of prior ADRs through new ADRs (the only permitted modification)

**Excluded:**
- Requirements elicitation (governed by PROC-LC-002)
- Implementation details and spec authoring (governed by PROC-LC-004)
- Operational architecture and deployment topology (governed by PROC-LC-007 when written)

## 3. Entry Criteria

- [ ] At least one active requirement (REQ-XXX) drives the need for an architectural decision
- [ ] The decision involves a structural choice with multiple viable alternatives
- [ ] The ADR template (`qms/templates/adr.md.tmpl`) is available

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Active requirements | `docs/requirements/REQ-*.md` | Markdown REQ documents |
| Existing ADRs | `docs/architecture/decisions/ADR-*.md` | Markdown ADR documents |
| Component documentation | `docs/architecture/components/` | Markdown component docs |
| Research evidence | `docs/research/` | Markdown research papers |
| Architecture INDEX | `docs/architecture/INDEX.md` | Markdown index file |

## 5. Activities

### 5.1 Identify Architectural Decision Point

Recognize when a design choice has structural implications — it affects plugin loading, CLI dispatch, encryption boundaries, CI pipeline topology, or cross-plugin communication. Not every implementation choice warrants an ADR; only decisions that constrain future options.

### 5.2 Evaluate Alternatives

For each candidate approach, document:
- What the approach entails
- Its advantages and disadvantages
- How it satisfies or conflicts with active requirements
- Its impact on existing architecture (review existing ADRs for constraints)

This evaluation forms the Context and Considered Options sections of the ADR.

### 5.3 Write ADR Document

Create a new file in `docs/architecture/decisions/` using the naming convention `ADR-<NNN>-<short-description>.md`. Use the ADR template (`qms/templates/adr.md.tmpl`). Assign the next sequential ID after the highest existing ADR number.

Populate all sections: Context, Considered Options, Decision, Consequences, and Traces. Set `Status: accepted` upon creation (ADRs are accepted at the point of writing, not through a separate approval step).

### 5.4 Enforce Immutability

Once an ADR is committed with `Status: accepted`, it must never be edited except to change its status to `superseded-by ADR-YYY`. To revisit a past decision:
1. Create a new ADR with the next sequential ID
2. Explain in its Context section why the original is being revisited
3. Update the original ADR's status to `superseded-by ADR-YYY` (the only allowed edit)

### 5.5 Update Component Documentation

If the decision affects a component documented in `docs/architecture/components/`, update that component document to reflect the new architectural constraint or capability. Component docs are mutable and should always reflect current architecture.

### 5.6 Update INDEX

Add the new ADR to `docs/architecture/INDEX.md` with its ID, title, status, and date.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Architecture Decision Record | `docs/architecture/decisions/` | `adr.md.tmpl` | ADR-XXX |
| Component documentation | `docs/architecture/components/` | — | — |
| Updated INDEX | `docs/architecture/INDEX.md` | — | — |

## 7. Exit Criteria

- [ ] ADR document exists in `docs/architecture/decisions/` with all sections populated
- [ ] At least two alternatives were evaluated in the Considered Options section
- [ ] ID is globally unique across all document namespaces
- [ ] Traces section links to at least one upstream REQ
- [ ] `bash scripts/validate-docs.sh` passes with no failures
- [ ] ADR appears in `docs/architecture/INDEX.md`
- [ ] PR has been reviewed and merged

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Alternatives evaluation | Manual review of Considered Options | At least two distinct alternatives documented with trade-offs |
| Requirement traceability | Review of Traces section | Links to at least one active REQ-XXX |
| Structural validation | `bash scripts/validate-docs.sh` | Exit code 0 — no duplicate IDs, filename matches ID, Traces section present |
| Immutability compliance | Code review of any ADR modification PR | Only status field changes permitted on accepted ADRs |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Lead Architect | Identifies decision points, evaluates alternatives, writes ADRs |
| Developer | Contributes technical analysis for alternatives, implements decisions |
| Reviewer | Validates that alternatives were fairly evaluated and traces are complete |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| ADR coverage | Percentage of significant architectural choices with corresponding ADRs | 100% | Manual audit comparing component docs against ADR list |
| Alternatives breadth | Average number of alternatives evaluated per ADR | >= 2 | Count Considered Options sections across all ADRs |
| Immutability violations | Number of accepted ADRs modified outside the supersession process | 0 | Git log audit of files in `docs/architecture/decisions/` |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.4 Architecture Definition | This process implements software architecture definition activities |
| ISO/IEC 42010:2011 | 5.6 Architecture Description | ADRs and component docs constitute the architecture description |
| CMMI-DEV v2.0 | TS (Technical Solution) | Covers TS SP 1.1 (develop alternative solutions) and SP 1.2 (select solutions) |

## 12. Tailoring Guidance

**Minimum viable process (minor decision):** For decisions that affect only one plugin or one script, the Considered Options section may be abbreviated to a brief comparison. The Context and Decision sections remain mandatory.

**Full ceremony (cross-cutting decision):** For decisions that affect the plugin loading model, CLI architecture, encryption boundaries, or CI topology, a full multi-paragraph alternatives analysis is required. A dedicated review meeting or async discussion thread should precede the ADR.

**Supersession:** When superseding an ADR, the new ADR must reference the original and explain what changed. The original ADR's status change (`superseded-by ADR-YYY`) must be committed in the same PR as the new ADR.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-002 | Depends on: requirements drive architectural decisions |
| PROC-LC-004 | Feeds into: ADRs constrain implementation SPECs |
| PROC-SP-004 | Extends: Documentation Management governs the docs/ structure ADRs live in |
| PROC-SP-006 | Depends on: Peer Review validates ADR quality during PR review |
| PROC-SEC-001 | Related: security ADRs must align with secure development practices |

## 14. Traces

- **Governs:** `docs/architecture/decisions/ADR-*.md`, `docs/architecture/components/`, `docs/architecture/INDEX.md`
- **Enforced by:** `scripts/validate-docs.sh` (structural validation), `fast-validate` CI job (push.yml), ADR immutability rule in `.claude/rules/docs-system.md`
- **Related QA:** ADR immutability constraint, alternatives evaluation requirement

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing architecture design practice with 8 active ADRs |

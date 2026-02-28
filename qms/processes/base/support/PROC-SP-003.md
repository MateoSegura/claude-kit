# PROC-SP-003: Verification & Validation

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** V&V Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Verification & Validation (V&V) governs how claude-kit confirms that implemented artifacts are correct (verification — "built the thing right") and that they satisfy stakeholder needs (validation — "built the right thing"). This process formalizes the grader plugin role, semantic PR review, and requirements traceability checking that together ensure changes meet their stated intent. V&V complements the automated test cascade (PROC-LC-005) with human and AI-assisted judgment.

## 2. Scope

**Included:**
- Verification that implementations conform to their driving requirements (REQ-XXX) and specs (SPEC-XXX)
- Validation that plugin capabilities address real user needs
- Grader plugin role output as formal verification evidence
- Semantic PR review via Claude Haiku as validation input
- Requirements traceability matrix maintenance

**Excluded:**
- Automated test execution (governed by PROC-LC-005)
- Code-level peer review (governed by PROC-SP-006)
- Security-specific verification (governed by PROC-SEC-001)

## 3. Entry Criteria

- [ ] Implementation is complete and has passed the test cascade (PROC-LC-005)
- [ ] The driving requirement (REQ-XXX) or specification (SPEC-XXX) is identified
- [ ] The grader plugin is available for the relevant team domain

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Implemented code/plugins | Feature branch or merged PR | Git repository files |
| Requirements | `docs/requirements/REQ-*.md` | Markdown REQ documents |
| Specifications | `docs/specs/SPEC-*.md` | Markdown SPEC documents |
| Architecture decisions | `docs/architecture/decisions/ADR-*.md` | Markdown ADR documents |
| Grader plugin | `plugins/<team>-grader/` | Plugin with grading agents and commands |
| Semantic review output | `pr.yml` semantic-check job | PR comment with findings |

## 5. Activities

### 5.1 Trace Implementation to Requirements

For each significant change, verify that a traceability chain exists:

```
REQ-XXX → ADR-XXX (optional) → SPEC-XXX → Code/Plugin change → TEST-XXX
```

The `## Traces` section in each document provides the links. The `validate-docs.sh` script verifies that cross-referenced IDs resolve to real files. Manual review confirms that the semantic meaning of the traces is accurate (not just that the IDs exist).

### 5.2 Execute Grader Evaluation

The grader plugin role provides structured evaluation of plugin quality. Each team has a grader plugin (`<team>-grader`) with:
- A `grade` command that scores plugin content against quality criteria
- A `compare` command that evaluates differences between versions
- Agents that assess identity coherence, content depth, and domain specificity

Run the grader against modified plugins to produce formal verification evidence. The grader output documents what was evaluated, the criteria used, and the scores assigned.

### 5.3 Review Semantic Check Results

On PRs that modify plugins, the `pr.yml` semantic-check job runs automatically. It uses Claude Haiku with a focused prompt (built by `scripts/build-semantic-prompt.py`) to review changed plugins for:
- Identity coherence (does the plugin's behavior match its stated role?)
- Content depth (is the knowledge substantive or superficial?)
- Domain specificity (is the content specific to the declared domain?)
- Cross-agent contradictions (do agents within the same plugin contradict each other?)

Review the semantic check PR comment. While not a required merge gate, WARN or FATAL findings should be addressed before merge.

### 5.4 Validate Against User Needs

For features driven by user feedback or market analysis, validate that the implementation actually addresses the stated need. This is a judgment call that goes beyond automated testing:
- Does the feature work as a user would expect?
- Does the plugin content provide the knowledge the domain requires?
- Are the command interfaces intuitive for the target audience?

Document validation findings in the SPEC status log or in a test evidence record.

### 5.5 Document Verification Evidence

For significant verifications, create a formal record in `docs/testing/evidence/` using the test evidence template. The record links the verification activity to the requirement being verified, the method used, and the outcome.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Verification evidence | `docs/testing/evidence/` | `test-evidence.md.tmpl` | TEST-XXX |
| Grader evaluation output | Grader command output | — | — |
| Semantic review findings | PR comments | — | — |
| Updated Traces sections | `docs/` (various) | — | — |

## 7. Exit Criteria

- [ ] Traceability chain exists from requirement through implementation to test evidence
- [ ] Grader evaluation has been run for modified plugins (when applicable)
- [ ] Semantic review findings have been addressed or acknowledged
- [ ] No unresolved FATAL findings from semantic or grader review
- [ ] Verification evidence is documented for significant features

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Traceability completeness | `validate-docs.sh` cross-reference check + manual review | Every active REQ traces forward to at least one SPEC or ADR; every SPEC traces back to a REQ |
| Grader score | Grader plugin `grade` command output | No FATAL scores; WARN scores have documented justification |
| Semantic coherence | `pr.yml` semantic-check PR comment | No FATAL findings; WARN findings addressed or deferred with explanation |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| V&V Lead | Coordinates verification activities, ensures traceability, reviews grader output |
| Developer | Maintains Traces sections, responds to grader and semantic review findings |
| Grader Plugin | Provides automated evaluation of plugin quality against defined criteria |
| Semantic Reviewer (CI) | Performs AI-assisted validation of plugin coherence on PR submission |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Traceability coverage | Percentage of active REQs with forward traces to SPECs or ADRs | 100% | Audit of Traces sections in `docs/requirements/` |
| Semantic review finding rate | Average number of WARN+ findings per PR with plugin changes | < 1 per PR | Count findings in semantic-check PR comments |
| Verification evidence coverage | Percentage of completed SPECs with corresponding TEST-XXX records | > 80% | Cross-reference `docs/specs/` against `docs/testing/evidence/` |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.9 Software Verification | Activities 5.1-5.3 implement verification against requirements |
| ISO/IEC 12207:2017 | 6.4.10 Software Validation | Activity 5.4 implements validation against user needs |
| CMMI-DEV v2.0 | VER (Verification) | Covers VER SP 1.1 (select work products), SP 2.1 (prepare for peer reviews), SP 3.1 (perform verification) |
| CMMI-DEV v2.0 | VAL (Validation) | Covers VAL SP 1.1 (select products for validation), SP 2.1 (perform validation) |

## 12. Tailoring Guidance

**Minimum viable process (minor change):** For PATCH-level changes, traceability verification via `validate-docs.sh` is sufficient. Grader evaluation and formal evidence records are optional.

**Full ceremony (new capability):** For new agents, commands, or skills (MINOR+), all activities must be executed: traceability chain, grader evaluation, semantic review, and formal test evidence record.

**Knowledge plugin changes:** Focus on semantic review (Activity 5.3) rather than grader evaluation, since knowledge plugins do not have agents or commands to grade.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-002 | Depends on: requirements define what must be verified |
| PROC-LC-004 | Depends on: implementation produces what is verified |
| PROC-LC-005 | Related: test cascade provides automated verification evidence |
| PROC-SP-002 | Extends: V&V is a key activity within the quality assurance framework |
| PROC-SP-006 | Related: peer review provides complementary human verification |

## 14. Traces

- **Governs:** `docs/testing/evidence/TEST-*.md`, grader evaluation output, semantic review findings
- **Enforced by:** `scripts/validate-docs.sh` (cross-reference verification), `pr.yml` semantic-check job, grader plugin commands
- **Related QA:** Traceability requirements in `.claude/rules/docs-system.md` (Traces section mandate)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing grader role and semantic review as V&V activities |

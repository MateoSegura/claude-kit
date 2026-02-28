# PROC-SP-005: Defect Management

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** QA Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Defect Management governs how defects are detected, triaged, fixed, and verified in claude-kit. This process formalizes the three automated detection mechanisms (CI validation failures, nightly plugin review, weekly full audit) alongside manual defect reporting, and ensures that every defect follows a consistent lifecycle from detection to verified closure. The autofix mechanism provides a first line of automated response before human intervention.

## 2. Scope

**Included:**
- Defect detection via CI validation failures, nightly review, and weekly audit
- PR autofix mechanism (up to 3 automated fix attempts per PR)
- Manual defect reporting via GitHub Issues
- Defect triage, assignment, and prioritization
- Fix verification through the test cascade
- Regression tracking for recurring defects

**Excluded:**
- Feature requests (not defects)
- Security vulnerabilities (governed by PROC-SEC-001 and PROC-SEC-005)
- Process improvement suggestions (governed by PROC-LC-008 when written)

## 3. Entry Criteria

- [ ] A defect has been detected by one of the defined detection mechanisms
- [ ] The defect is reproducible or the evidence is captured (CI logs, audit output)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| CI validation failure logs | `fast-validate` / `pr-validate` | GitHub Actions output |
| Nightly review findings | `nightly.yml` workflow | PR with auto-fix or workflow summary |
| Weekly audit findings | `weekly.yml` workflow | GitHub Issue with `audit-failure` label |
| PR autofix results | `pr-autofix.yml` workflow | Commits + PR labels (`autofix-attempt-N`) |
| Manual defect reports | GitHub Issues | Unstructured issue text |
| Regression records | `docs/testing/regression/REG-*.md` | Markdown REG documents |

## 5. Activities

### 5.1 Detect Defects

Defects enter the system through four channels:

1. **CI failure** — `fast-validate` or `validate-tier1` fails on a push or PR. The failure log identifies the broken validation layer and the specific check that failed.

2. **PR autofix trigger** — When `fast-validate` fails on a non-main branch with an open PR (and fewer than 3 autofix labels), the `pr-autofix.yml` workflow automatically attempts a fix using Claude with edit tools and `scripts/build-autofix-prompt.py`.

3. **Nightly review** — The `nightly.yml` workflow (02:00 UTC daily) performs a full semantic review of all plugins. WARN or FATAL findings trigger an automated fix branch (`fix/nightly-plugin-review-YYYYMMDD`) and PR.

4. **Weekly audit** — The `weekly.yml` workflow (Monday 09:00 UTC) performs Tier 1 strict validation and cross-coherence review. Failures create a GitHub Issue with the `audit-failure` label.

### 5.2 Triage and Prioritize

For defects not handled by automation:
- **Severity** — FATAL (blocks release), WARN (should fix before release), INFO (track for future)
- **Priority** — based on user impact and release timeline
- **Assignment** — assign to the developer most familiar with the affected area

For nightly autofix PRs, triage is automatic: the PR is created with auto-merge enabled. If CI passes, the fix merges without human intervention.

### 5.3 Attempt Automated Fix

The `pr-autofix.yml` workflow provides up to 3 automated fix attempts per PR:
1. Fetch failure logs from the failed `fast-validate` run
2. Build a fix prompt via `scripts/build-autofix-prompt.py`
3. Run Claude with full edit tools to attempt the fix
4. If changes are made: commit, push, and label the PR with `autofix-attempt-N`
5. If no changes: post a comment suggesting the failure may be transient
6. After 3 attempts: stop automated fixing; manual intervention required

### 5.4 Manual Fix

When automated fixes fail or are not applicable:
1. Create a fix branch following the naming convention: `fix/<short-description>`
2. Reproduce the defect locally
3. Implement the fix following PROC-LC-004
4. Run the affected validation layers locally
5. Submit a PR with a clear description of the root cause and fix

### 5.5 Verify Fix

Every fix must pass through the test cascade (PROC-LC-005). For nightly autofix PRs, this happens automatically via the CI required checks. For manual fixes, the developer must confirm that the specific validation that originally failed now passes.

### 5.6 Track Regressions

If a defect is a regression (something that previously passed now fails), create a regression record (REG-XXX) in `docs/testing/regression/`. The record documents:
- What regressed and when
- Root cause analysis
- The fix applied
- Prevention measures for the future

Update the status to `fixed` when the fix is verified and merged.

### 5.7 Close Defect

A defect is closed when:
- The fix PR has been merged to main
- The test cascade passes on main after merge
- Any regression record has been updated to `fixed`
- The GitHub Issue (if one was created) is closed

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Fix branches and PRs | Git repository / GitHub | — | `fix/<description>` |
| Regression records | `docs/testing/regression/` | — | REG-XXX |
| Autofix commits | Git repository | — | Conventional Commits |
| Nightly fix PRs | GitHub PRs | — | `fix/nightly-plugin-review-YYYYMMDD` |
| Audit failure issues | GitHub Issues | — | `audit-failure` label |

## 7. Exit Criteria

- [ ] The defect has a documented root cause
- [ ] A fix has been implemented and passes the test cascade
- [ ] The fix PR has been reviewed and merged
- [ ] If a regression, a REG-XXX record exists with status `fixed`
- [ ] Any corresponding GitHub Issue is closed

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Fix verification | Test cascade on fix branch | All affected validation layers exit 0 |
| Regression prevention | Regression record created (if applicable) | REG-XXX document exists with prevention measures |
| Autofix exhaustion | PR label count | If 3 autofix attempts failed, manual review is mandatory |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| QA Lead | Triages defects, monitors autofix results, tracks regression trends |
| Developer | Investigates root cause, implements manual fixes, creates regression records |
| CI System | Detects defects via validation failures, triggers autofix workflow |
| Autofix Bot | Attempts automated fixes (max 3 per PR), labels attempts |
| Nightly Bot | Detects plugin quality drift, creates fix PRs with auto-merge |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Autofix success rate | Percentage of autofix attempts that resolve the CI failure | > 50% | Count PRs where autofix led to green CI vs total autofix attempts |
| Mean time to fix | Average hours from defect detection to fix merge | < 24 hours for FATAL, < 72 hours for WARN | Git timestamps (detection commit to fix merge) |
| Regression frequency | Number of new REG-XXX records created per month | < 2 | Count files in `docs/testing/regression/` |
| Nightly finding trend | Month-over-month change in nightly review findings | Decreasing | Nightly workflow summary counts |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.4 Problem Resolution | This process implements software problem resolution activities |
| ISO/IEC 12207:2017 | 6.3.5 Quality Management (corrective action) | Defect fixes are corrective actions within quality management |
| CMMI-DEV v2.0 | CAR (Causal Analysis and Resolution) | Covers CAR SP 1.1 (select defects for analysis) and SP 1.2 (analyze causes) |

## 12. Tailoring Guidance

**Minimum viable process (minor defect):** For WARN-level defects caught by CI on a feature branch, the autofix mechanism may suffice. If autofix succeeds on the first attempt, no manual triage or regression record is needed.

**Full ceremony (FATAL defect on main):** For defects that reach `main` or block a release, full root cause analysis is required. A regression record must be created, prevention measures documented, and the fix verified across all affected teams (cross-team consistency check).

**Nightly defects:** Nightly autofix PRs with auto-merge handle the full defect lifecycle automatically for content drift issues. Human review is only needed if the auto-merge fails or if the finding is FATAL.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-005 | Depends on: test cascade detects defects and verifies fixes |
| PROC-SP-002 | Extends: defect management is a key activity within quality assurance |
| PROC-SP-006 | Related: peer review may detect defects before they reach CI |
| PROC-SP-001 | Depends on: configuration management provides branch and version control for fix flow |
| PROC-LC-004 | Related: manual fix implementation follows the implementation process |

## 14. Traces

- **Governs:** `docs/testing/regression/REG-*.md`, GitHub Issues with `audit-failure` label, autofix PRs
- **Enforced by:** `pr-autofix.yml` (automated fix attempts), `nightly.yml` (nightly defect detection and fix), `weekly.yml` (weekly audit defect detection), `scripts/build-autofix-prompt.py` (fix prompt generation)
- **Related QA:** Autofix attempt limit (3 per PR), nightly review schedule (02:00 UTC), weekly audit schedule (Monday 09:00 UTC)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing autofix, nightly review, and weekly audit as defect management |

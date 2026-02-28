# PROC-SP-006: Peer Review

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** Review Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Peer Review governs how code and artifact changes are reviewed before merge in claude-kit. This process formalizes the combination of human PR review and AI-assisted semantic review that together catch defects, enforce conventions, and ensure domain coherence that automated testing alone cannot detect. Peer review is a required quality gate — no PR merges without passing required CI checks and obtaining review approval.

## 2. Scope

**Included:**
- Human code review on pull requests
- AI-assisted semantic review via `pr.yml` semantic-check job
- Review of plugin content for identity coherence and domain specificity
- Review of documentation for accuracy and completeness
- Review of commit message format and branch naming compliance
- Review approval/rejection workflow on GitHub

**Excluded:**
- Automated test execution (governed by PROC-LC-005)
- Formal verification and grading (governed by PROC-SP-003)
- Post-merge quality audits (governed by PROC-SP-002)

## 3. Entry Criteria

- [ ] A pull request exists targeting `main`
- [ ] All required CI checks (`fast-validate`, `validate-tier1`) have passed
- [ ] The PR description explains the purpose and scope of the change

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Pull request | GitHub PR | Code diff, description, CI status |
| CI check results | `fast-validate`, `validate-tier1` | GitHub status checks (pass/fail) |
| Semantic review comment | `pr.yml` semantic-check job | PR comment with findings |
| Tier 1 validation comment | `pr.yml` validate-tier1 job | PR comment with results |
| Plugin conventions | `.claude/rules/plugin-conventions.md` | Markdown rule file |
| Code style rules | `.claude/rules/code-style.md` | Markdown rule file |

## 5. Activities

### 5.1 Automated Pre-Review Checks

Before human review begins, the CI pipeline provides:

1. **`fast-validate` (push.yml)** — Runs the 5-layer test cascade. This is a required status check that must pass before merge.

2. **`validate-tier1` (pr.yml)** — Runs Tier 1 on ALL plugins and posts results as a PR comment. Required status check.

3. **`semantic-check` (pr.yml)** — Only runs when plugins changed. Uses Claude Haiku with a prompt built by `scripts/build-semantic-prompt.py` to review changed plugins for identity coherence, content depth, domain specificity, and cross-agent contradictions. Posts findings as a separate PR comment. Informational only (not a merge gate).

### 5.2 Review Code Changes

The human reviewer examines the PR diff for:

- **Correctness** — Does the code do what the PR description claims?
- **Style compliance** — Does it follow `.claude/rules/code-style.md`? (Python: stdlib only, pathlib, f-strings, ruff formatting; Shell: `set -euo pipefail`, quoted variables)
- **Commit format** — Do all commits follow Conventional Commits syntax?
- **Security** — Are there any credential leaks, key exposure, or dependency additions?
- **Cross-team consistency** — If a team plugin was changed, was the same fix applied to equivalent plugins in all other teams?

### 5.3 Review Plugin Content

For PRs that modify plugins, additional review criteria apply:

- **Frontmatter correctness** — `tools:` in agents, `allowed-tools:` in commands (never reversed)
- **Companion resolution** — All companion names in `ctl.json` resolve to real plugin directories
- **Version consistency** — If content changed, was the version bumped appropriately?
- **README accuracy** — Does the plugin README reflect the current agents, commands, and skills?

### 5.4 Review Semantic Check Results

If the `semantic-check` job ran, review its PR comment for findings:
- **FATAL** — Must be resolved before merge
- **WARN** — Should be addressed; may be deferred with documented justification
- **INFO** — Acknowledged; no action required

### 5.5 Provide Feedback

Post review comments on the PR for any issues found. Use GitHub's review feature:
- **Approve** — All criteria met, no blocking issues
- **Request changes** — Blocking issues identified that must be addressed
- **Comment** — Non-blocking observations or suggestions

### 5.6 Verify Revisions

When the author pushes revisions in response to review feedback:
1. CI re-runs automatically (new `fast-validate` and `pr-validate` checks)
2. The reviewer verifies that the specific feedback was addressed
3. The semantic-check reruns if plugins were modified
4. The reviewer updates their review status (approve/request changes)

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Review comments | GitHub PR | — | — |
| Review decision (approve/reject) | GitHub PR review | — | — |
| Semantic check findings | GitHub PR comment | — | — |
| Tier 1 validation results | GitHub PR comment | — | — |

## 7. Exit Criteria

- [ ] All required CI checks pass (`fast-validate`, `validate-tier1`)
- [ ] At least one reviewer has approved the PR
- [ ] All "request changes" reviews have been resolved
- [ ] FATAL findings from semantic check (if any) have been addressed
- [ ] PR is ready for squash merge to `main`

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| CI required checks | GitHub branch protection | `fast-validate` and `validate-tier1` both green |
| Human review approval | GitHub PR review status | At least one approval, no outstanding "request changes" |
| Semantic coherence (plugins) | `pr.yml` semantic-check output | No FATAL findings |
| Convention compliance | Manual review against `.claude/rules/` | Code style, commit format, and plugin conventions followed |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| PR Author | Submits PR with clear description, responds to review feedback, pushes revisions |
| Reviewer | Reviews code, plugins, and documentation; provides constructive feedback; approves or requests changes |
| CI System | Runs automated checks, posts Tier 1 results and semantic review as PR comments |
| Semantic Reviewer (CI) | Performs AI-assisted coherence review of changed plugins |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Review turnaround time | Average hours from PR creation to first review comment | < 24 hours | GitHub PR timeline |
| Review iteration count | Average number of review-revise cycles before approval | < 2 | Count of "request changes" events per PR |
| Semantic finding adoption rate | Percentage of WARN+ semantic findings that result in code changes | > 75% | Compare semantic comments against subsequent commits |
| Post-merge defect rate | Number of defects found on main that were missed during review | 0 per month | Count of fix branches targeting issues introduced by a specific PR |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.9.3 Software Review | This process implements software review activities |
| ISO/IEC 12207:2017 | 6.3.5 Quality Management | Peer review is a quality management technique |
| CMMI-DEV v2.0 | VER (Verification) | Covers VER SP 2.1 (prepare for peer reviews) and SP 2.2 (conduct peer reviews) |

## 12. Tailoring Guidance

**Minimum viable process (docs-only change):** For changes limited to `docs/` or `README.md`, the semantic check does not run. Human review focuses on content accuracy and cross-reference integrity. A lighter review is acceptable.

**Full ceremony (plugin changes):** For PRs modifying plugins, both human review and semantic check results must be evaluated. Cross-team consistency must be verified. Version bump appropriateness must be confirmed.

**Self-review (sole developer):** When working as a sole developer, CI-based automated review (Tier 1 validation + semantic check) substitutes for human review. The developer should still read the semantic check findings before merging.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-004 | Depends on: Implementation produces the PRs that are reviewed |
| PROC-LC-005 | Related: test cascade provides automated pre-review verification |
| PROC-SP-002 | Extends: Peer review is a quality gate within the quality assurance framework |
| PROC-SP-003 | Related: V&V uses review findings as input for verification evidence |
| PROC-SP-005 | Feeds into: review-detected defects enter defect management |

## 14. Traces

- **Governs:** PR review records (GitHub), semantic check findings (PR comments), Tier 1 validation results (PR comments)
- **Enforced by:** GitHub branch protection rules (required checks), `pr.yml` (`validate-tier1`, `semantic-check`), `push.yml` (`fast-validate`)
- **Related QA:** Code style rules in `.claude/rules/code-style.md`, plugin conventions in `.claude/rules/plugin-conventions.md`, cross-team consistency in `.claude/rules/cross-team-consistency.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing PR review and semantic check as peer review process |

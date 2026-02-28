# PROC-LC-004: Implementation

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** Lead Developer
**Last Reviewed:** 2026-02-28

## 1. Purpose

Implementation governs how code and plugin changes are developed, committed, and submitted for review in claude-kit. This process ensures that all development work follows the branch-based git workflow, adheres to Conventional Commits, is driven by specification documents, and passes local validation before reaching CI. It bridges the gap between architecture decisions and verified, merged code.

## 2. Scope

**Included:**
- Creation and management of implementation specification documents (SPEC-XXX) in `docs/specs/`
- Branch creation following the naming convention `<type>/<description>`
- Code development against specification requirements
- Local validation before commit and push
- Pull request creation and submission for review

**Excluded:**
- Requirements elicitation (governed by PROC-LC-002)
- Architecture decisions (governed by PROC-LC-003)
- Testing and verification (governed by PROC-LC-005)
- Release packaging (governed by PROC-LC-006)

## 3. Entry Criteria

- [ ] At least one active requirement (REQ-XXX) or architecture decision (ADR-XXX) justifies the work
- [ ] A specification document (SPEC-XXX) exists or will be created as part of the implementation
- [ ] The developer's git identity is configured (`user.name` and `user.email`)
- [ ] The working tree is clean on `main` or a known base branch

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Active requirements | `docs/requirements/REQ-*.md` | Markdown REQ documents |
| Architecture decisions | `docs/architecture/decisions/ADR-*.md` | Markdown ADR documents |
| Specification document | `docs/specs/` | Markdown SPEC documents |
| Spec template | `qms/templates/spec.md.tmpl` | Markdown template |
| Git workflow rules | `.claude/rules/git-workflow.md` | Markdown rule file |
| Code style rules | `.claude/rules/code-style.md` | Markdown rule file |

## 5. Activities

### 5.1 Create or Update Specification

Before implementation begins, create a SPEC document in `docs/specs/` using the spec template (`qms/templates/spec.md.tmpl`). The SPEC defines the scope, phases, acceptance criteria, and traces for the implementation. Set `Status: active` when work begins.

For ongoing work, update the existing SPEC's status log and phase completion records.

### 5.2 Create Feature Branch

Create a branch from the latest `main` using the enforced naming convention:

```
git checkout -b <type>/<short-description>
```

Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`, `release`, `hotfix`. The `push.yml` workflow enforces this convention — branches that do not match are rejected.

### 5.3 Implement Changes

Develop code following the standards in `.claude/rules/code-style.md`:
- Python CLI (`claude-kit`): stdlib only, `pathlib.Path`, f-strings, ruff formatting
- Shell scripts: `set -euo pipefail`, quoted variables, `$(...)` substitution
- Plugin markdown: correct frontmatter keys (`tools:` for agents, `allowed-tools:` for commands)

For plugin changes, follow the cross-team consistency rule: if fixing a bug in one team plugin, check and fix the same role across all other teams.

### 5.4 Run Local Validation

Before committing, run the test layers affected by the changes:

| Changed zone | Validation command |
|--------------|-------------------|
| `claude-kit` CLI | `python3 -m py_compile claude-kit && bash scripts/test-cli.sh` |
| `plugins/**` | `python3 scripts/validate-plugins.py --changed --strict && bash scripts/test-plugin-consistency.sh` |
| `docs/**` | `bash scripts/validate-docs.sh` |
| Multiple zones | Run all affected layers in sequence |

All validation must exit 0 before committing.

### 5.5 Commit with Conventional Commits

Write commit messages in Conventional Commits format:

```
<type>(<optional-scope>): <concise imperative description>

<optional body: explain WHY, not what>
```

Subject line: max 72 characters, imperative mood, no trailing period. Body: wrap at 80 characters, separated from subject by a blank line.

### 5.6 Push and Create Pull Request

Push the branch and create a PR targeting `main`:

```bash
git push -u origin <branch>
gh pr create --title "<type>: <description>" --body "..."
```

The PR triggers `fast-validate` (required) and `pr-validate` (required for Tier 1; informational for semantic check). Wait for all required checks to pass.

### 5.7 Update Specification Status

When the implementation is merged, update the SPEC document status to `completed` and create corresponding test evidence records (see PROC-LC-005).

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Specification document | `docs/specs/` | `spec.md.tmpl` | SPEC-XXX |
| Feature branch | Git repository | — | `<type>/<description>` |
| Pull request | GitHub | — | — |
| Committed code | Git repository | — | Conventional Commit messages |

## 7. Exit Criteria

- [ ] All code changes pass local validation (affected test layers exit 0)
- [ ] Commits follow Conventional Commits format
- [ ] Branch name matches `<type>/<description>` convention
- [ ] PR has been created and all required CI checks pass
- [ ] SPEC document exists with traces to upstream REQ and/or ADR
- [ ] PR has been reviewed and approved (see PROC-SP-006)

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Local validation | Developer runs affected test layers | All layers exit 0 |
| Branch naming | `push.yml` CI enforcement | Branch matches `<type>/<description>` pattern |
| Commit format | PR review | All commits follow Conventional Commits syntax |
| CI pipeline | `fast-validate` + `validate-tier1` | Both jobs pass (required status checks) |
| Cross-team consistency | Manual check or `validate-plugins.py --all` | Same fix applied to equivalent plugins across all teams |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Developer | Creates branch, implements changes, runs local validation, submits PR |
| Lead Developer | Ensures SPEC coverage, reviews cross-team consistency |
| Reviewer | Validates code quality, commit format, and CI results during PR review |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| CI pass rate | Percentage of pushes where `fast-validate` passes on first attempt | > 90% | GitHub Actions workflow history |
| Commit convention compliance | Percentage of commits following Conventional Commits format | 100% | Git log audit |
| Branch naming compliance | Percentage of branches matching the naming convention | 100% | `push.yml` enforcement (rejections logged in CI) |
| Time to merge | Calendar time from branch creation to PR merge | < 48 hours for fixes, < 1 week for features | Git log timestamps |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.5 Implementation | This process implements the software coding and integration activities |
| ISO/IEC 12207:2017 | 6.4.8 Software Configuration Management | Branch and commit conventions support configuration identification |
| CMMI-DEV v2.0 | TS (Technical Solution) | Covers TS SP 2.1 (design the product) and SP 2.2 (implement the product) |
| CMMI-DEV v2.0 | CM (Configuration Management) | Covers CM SP 1.1 (identify configuration items) |

## 12. Tailoring Guidance

**Minimum viable process (hotfix):** For urgent single-file fixes, the SPEC document may be omitted. A commit message body explaining the fix rationale substitutes for the SPEC. All other activities (branch, validation, PR, CI) remain mandatory.

**Full ceremony (major feature):** For features spanning multiple plugins or CLI changes, a dedicated SPEC document with phased delivery plan is required. Cross-team consistency checks must cover all five roles across all teams.

**Documentation-only changes:** For changes only to `docs/` or `README.md`, only Layer 4 (docs validation) is required before committing. Branch and PR requirements still apply.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-002 | Depends on: requirements drive what gets implemented |
| PROC-LC-003 | Depends on: architecture decisions constrain implementation |
| PROC-LC-005 | Feeds into: implementation triggers integration and testing |
| PROC-LC-006 | Feeds into: merged implementations accumulate toward a release |
| PROC-SP-001 | Depends on: configuration management governs branching and versioning |
| PROC-SP-006 | Depends on: peer review validates implementation quality |

## 14. Traces

- **Governs:** `docs/specs/SPEC-*.md`, feature branches, pull requests, committed code
- **Enforced by:** `push.yml` (branch naming, `fast-validate`), `pr.yml` (`validate-tier1`), `scripts/validate-plugins.py`, `scripts/test-cli.sh`, `scripts/validate-docs.sh`
- **Related QA:** Code style rules in `.claude/rules/code-style.md`, cross-team consistency rule in `.claude/rules/cross-team-consistency.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing branch-based development workflow |

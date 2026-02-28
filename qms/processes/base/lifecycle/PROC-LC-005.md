# PROC-LC-005: Integration & Testing

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** QA Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Integration & Testing governs how changes are verified through the multi-layer test cascade before and after merge in claude-kit. This process ensures that every code change is exercised by the appropriate validation layers, that test evidence is formally recorded, and that regressions are detected, documented, and tracked to resolution. The 5-layer test cascade is the primary quality enforcement mechanism for the entire repository.

## 2. Scope

**Included:**
- Execution of the 5-layer test cascade (Python syntax, CLI smoke tests, plugin validation, docs validation, process validation)
- CI-driven testing via `fast-validate` and `pr-validate` workflows
- Automated defect detection via `pr-autofix` (up to 3 attempts)
- Creation of test evidence records (TEST-XXX) in `docs/testing/evidence/`
- Regression analysis records (REG-XXX) in `docs/testing/regression/`

**Excluded:**
- Semantic review by Claude (informational, not a gate — covered by PROC-SP-006)
- User acceptance testing (not currently formalized)
- Performance benchmarking (governed by benchmark methodology in `docs/benchmarks/`)

## 3. Entry Criteria

- [ ] Code changes exist on a feature branch with at least one commit
- [ ] The branch has been pushed to the remote repository
- [ ] Local validation has been run by the developer (PROC-LC-004 Activity 5.4)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Feature branch | Git repository | Git branch with commits |
| Validation scripts | `scripts/` directory | Bash and Python scripts |
| Plugin files | `plugins/` directory | Markdown, JSON, Bash |
| Documentation files | `docs/` directory | Markdown with ID prefixes |
| Test evidence template | `qms/templates/test-evidence.md.tmpl` | Markdown template |
| CI workflow definitions | `.github/workflows/push.yml`, `pr.yml`, `pr-autofix.yml` | YAML workflow files |

## 5. Activities

### 5.1 Execute Layer 1 — Python Syntax Check

```bash
python3 -m py_compile claude-kit
```

Validates that the single-file CLI compiles without syntax errors. This layer runs in approximately 1 second and catches import errors, indentation issues, and syntax problems. Triggered by any change to the `claude-kit` file.

### 5.2 Execute Layer 2 — CLI Smoke Tests

```bash
bash scripts/test-cli.sh
```

Exercises CLI commands end-to-end: argument parsing, subcommand dispatch, flag handling, and human-readable output formatting. Triggered by changes to `claude-kit` or `scripts/test-cli.sh`.

### 5.3 Execute Layer 3 — Plugin Validation

```bash
python3 scripts/validate-plugins.py --changed --strict
bash scripts/test-plugin-consistency.sh
```

`validate-plugins.py` performs Tier 1 structural validation: checks `plugin.json` schema, `ctl.json` fields, directory structure rules (knowledge plugins must not have `agents/` or `commands/`), and companion resolution. `test-plugin-consistency.sh` verifies version badge consistency, agent skill cross-references, hook type safety, and frontmatter field correctness. Triggered by any change in `plugins/`.

### 5.4 Execute Layer 4 — Docs Validation

```bash
bash scripts/validate-docs.sh
```

Validates the structured documentation system: INDEX.md presence in each subdirectory, globally unique document IDs, filename-to-ID matching, cross-reference resolution, valid status fields, and required Traces sections. Triggered by any change in `docs/`.

### 5.5 Execute Layer 5 — Process Validation

```bash
bash qms/scripts/validate-processes.sh
```

Validates the QMS process asset library: process document structure, required sections, catalog consistency, and cross-references. Triggered by any change in `qms/`.

### 5.6 CI Pipeline Execution

On every push, the `fast-validate` job in `push.yml` runs all five layers automatically. On PRs to main, `pr-validate` runs Tier 1 on all plugins (`--all --json`) and posts results as a PR comment. Both are required status checks — PRs cannot merge until they pass.

### 5.7 Automated Fix Attempts

When `fast-validate` fails on a non-main branch with an open PR, the `pr-autofix` workflow triggers automatically. It fetches failure logs, builds a fix prompt via `scripts/build-autofix-prompt.py`, and runs Claude with edit tools to attempt a fix. A maximum of 3 attempts are made per PR, tracked via `autofix-attempt-N` labels.

### 5.8 Create Test Evidence Records

For significant features or quality milestones, create a formal test evidence record (TEST-XXX) in `docs/testing/evidence/` using the test evidence template. The record documents what was tested, the method used, the result, and traces to the requirements and specs being verified.

### 5.9 Regression Analysis

When a test failure is identified as a regression (something that previously passed now fails), create a regression record (REG-XXX) in `docs/testing/regression/`. Document the failure, root cause, fix, and prevention measures. Update the status to `fixed` when resolved.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Test evidence record | `docs/testing/evidence/` | `test-evidence.md.tmpl` | TEST-XXX |
| Regression analysis | `docs/testing/regression/` | — | REG-XXX |
| CI validation results | GitHub Actions logs | — | — |
| PR comment with Tier 1 results | GitHub PR | — | — |
| Autofix commits | Git repository | — | Conventional Commits |

## 7. Exit Criteria

- [ ] All five test layers exit 0 (or only the relevant subset for the change type)
- [ ] `fast-validate` CI job passes
- [ ] `validate-tier1` CI job passes (for PRs to main)
- [ ] No unresolved regressions related to the change
- [ ] Test evidence record created for significant features (when applicable)

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Layer 1 — Syntax | `python3 -m py_compile claude-kit` | Exit code 0 |
| Layer 2 — CLI smoke | `bash scripts/test-cli.sh` | Exit code 0, all test cases pass |
| Layer 3 — Plugins | `validate-plugins.py --all --strict` + `test-plugin-consistency.sh` | Both exit code 0, no FATAL findings |
| Layer 4 — Docs | `bash scripts/validate-docs.sh` | Exit code 0, no FAIL results |
| Layer 5 — Processes | `bash qms/scripts/validate-processes.sh` | Exit code 0 |
| CI gate | `fast-validate` + `validate-tier1` | Both GitHub status checks green |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Developer | Runs local validation before push, reviews CI results, fixes failures |
| QA Lead | Monitors CI pass rates, creates test evidence for milestones, tracks regressions |
| CI System | Executes test cascade automatically on push and PR events |
| Autofix Bot | Attempts automated fixes when fast-validate fails (max 3 per PR) |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| CI pass rate (first push) | Percentage of pushes where `fast-validate` passes without autofix | > 85% | GitHub Actions workflow success/failure counts |
| Autofix success rate | Percentage of autofix attempts that resolve the failure | > 50% | Count of autofix PRs that lead to green CI |
| Test cascade duration | End-to-end time for all five layers | < 30 seconds | GitHub Actions job duration |
| Regression escape rate | Number of regressions that reach main per month | 0 | Count of REG-XXX records created |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.6 Integration | CI pipeline implements continuous integration activities |
| ISO/IEC 12207:2017 | 6.4.7 Qualification Testing | Test cascade implements software qualification testing |
| CMMI-DEV v2.0 | VER (Verification) | Covers VER SP 1.1 (select work products for verification), SP 3.1 (perform verification) |
| CMMI-DEV v2.0 | PI (Product Integration) | Covers PI SP 3.1 (confirm readiness of product components) |

## 12. Tailoring Guidance

**Minimum viable process (docs-only change):** Only Layer 4 (docs validation) is required. Layers 1-3 and 5 may be skipped. CI still runs all layers but only Layer 4 failures block the merge.

**Full ceremony (cross-cutting change):** All five layers must pass locally before push. A test evidence record (TEST-XXX) should be created documenting the verification approach and results.

**Plugin-only changes:** Layers 3 and 4 are required. Layer 1 may be skipped if the CLI file was not modified.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-004 | Depends on: implementation produces the code to be tested |
| PROC-LC-006 | Feeds into: passing tests enable release |
| PROC-SP-002 | Extends: Quality Assurance defines the quality gate framework |
| PROC-SP-003 | Related: Verification & Validation uses test evidence as input |
| PROC-SP-005 | Feeds into: test failures feed the defect management process |
| PROC-SP-006 | Related: Peer Review supplements automated testing with human review |

## 14. Traces

- **Governs:** `docs/testing/evidence/TEST-*.md`, `docs/testing/regression/REG-*.md`, CI validation results
- **Enforced by:** `scripts/test-cli.sh`, `scripts/validate-plugins.py`, `scripts/test-plugin-consistency.sh`, `scripts/validate-docs.sh`, `qms/scripts/validate-processes.sh`, `push.yml` (`fast-validate`), `pr.yml` (`validate-tier1`), `pr-autofix.yml`
- **Related QA:** 5-layer test cascade defined in `.claude/rules/testing-standards.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing 5-layer test cascade and CI pipeline |

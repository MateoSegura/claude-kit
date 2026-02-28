# PROC-SP-002: Quality Assurance

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** QA Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Quality Assurance defines the framework for ensuring that claude-kit's processes are followed and its artifacts meet defined quality standards. This process coordinates the multi-layer validation pipeline, automated review systems, and scheduled audit mechanisms that collectively prevent defective changes from reaching users. It is the umbrella process that connects testing, peer review, and defect management into a coherent quality system.

## 2. Scope

**Included:**
- Definition and maintenance of quality gates across all lifecycle processes
- Coordination of the 5-layer test cascade as a quality enforcement mechanism
- Scheduled quality audits (nightly plugin review, weekly full audit)
- Semantic quality review via Claude (informational gate)
- Quality attribute documentation in `docs/quality/`
- Quality metrics collection and trend analysis

**Excluded:**
- Execution of individual test layers (governed by PROC-LC-005)
- Individual peer review sessions (governed by PROC-SP-006)
- Defect triage and resolution (governed by PROC-SP-005)

## 3. Entry Criteria

- [ ] The quality gate framework is defined (this document)
- [ ] CI workflows are operational and enforcing required checks
- [ ] Validation scripts exist and are maintained in `scripts/`

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Test cascade results | CI pipeline logs | GitHub Actions output |
| Semantic review findings | `pr.yml` semantic-check job | PR comment |
| Nightly review results | `nightly.yml` workflow | GitHub Actions summary |
| Weekly audit results | `weekly.yml` workflow | GitHub Issues (audit-failure label) |
| Quality attribute documents | `docs/quality/` | Markdown QA-XXX documents |
| Testing standards | `.claude/rules/testing-standards.md` | Markdown rule file |

## 5. Activities

### 5.1 Define Quality Gates

Maintain quality gates for each lifecycle stage. A quality gate is a checkpoint where an artifact must meet specified criteria before proceeding. The primary gates in claude-kit are:

| Stage | Gate | Enforcement |
|-------|------|-------------|
| Pre-commit | Local validation (affected layers) | Developer discipline + dev-workflow.md automation |
| Pre-merge | `fast-validate` + `validate-tier1` | Required GitHub status checks |
| Pre-release | Full validation + CHANGELOG check | `release.yml` pipeline |
| Ongoing | Nightly review + weekly audit | Scheduled workflows |

### 5.2 Monitor CI Pipeline Health

Track the pass/fail rates of all CI workflows to detect systemic quality issues:
- `fast-validate` failures indicate developer workflow problems
- `pr-validate` failures indicate cross-plugin consistency issues
- `pr-autofix` exhaustion (3 attempts) indicates problems too complex for automation
- Nightly review findings indicate plugin content drift
- Weekly audit findings indicate cross-coherence degradation

### 5.3 Execute Scheduled Audits

Two automated audit mechanisms run on schedule:

**Nightly plugin review** (02:00 UTC daily): Full semantic review of all plugins. If WARN or FATAL findings exist, a fix branch is created, Claude auto-fixes the issues, and a PR is opened with auto-merge enabled.

**Weekly full audit** (Monday 09:00 UTC): Tier 1 strict validation on all plugins plus a cross-coherence semantic review. On failure, a GitHub Issue with the `audit-failure` label is created (skipped if one already exists).

### 5.4 Maintain Quality Attributes

Quality attributes and architectural constraints are documented in `docs/quality/` using the QA-XXX ID pattern and the `quality-attribute.md.tmpl` template. These documents capture non-functional requirements like performance targets, security boundaries, and reliability expectations that cut across all lifecycle processes.

### 5.5 Trend Analysis

Periodically review quality metrics to identify trends:
- Is the CI pass rate improving or degrading?
- Are nightly review findings becoming more or less frequent?
- Are autofix attempts sufficient or are manual interventions increasing?
- Are regression records trending up or down?

Use these trends to propose process improvements (feeding into PROC-LC-008 when written).

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Quality attribute documents | `docs/quality/` | `quality-attribute.md.tmpl` | QA-XXX |
| Nightly review PRs | GitHub PRs | — | `fix/nightly-plugin-review-YYYYMMDD` |
| Weekly audit issues | GitHub Issues | — | `audit-failure` label |
| Quality metrics dashboard | CI workflow summaries | — | — |

## 7. Exit Criteria

- [ ] Quality gates are defined for every lifecycle stage
- [ ] Scheduled audits are configured and running
- [ ] Quality attribute documents exist for known constraints
- [ ] Metrics are being collected and reviewed

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Gate framework completeness | Review of this process document | All lifecycle stages have at least one defined gate |
| Audit schedule active | GitHub Actions scheduled workflow status | Both nightly and weekly workflows have recent successful runs |
| Quality attribute coverage | Audit of `docs/quality/` | Every known quality concern has a QA-XXX document |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| QA Lead | Defines quality gates, reviews audit results, drives quality improvement |
| Developer | Follows quality gates during implementation, responds to audit findings |
| CI System | Executes quality gates automatically, runs scheduled audits |
| Nightly Bot | Creates fix PRs for semantic quality issues found during nightly review |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Overall CI pass rate | Percentage of all CI runs that pass across all workflows | > 90% | GitHub Actions aggregate stats |
| Nightly finding frequency | Average number of WARN/FATAL findings per nightly run | < 2 per week | Nightly workflow summaries |
| Weekly audit pass rate | Percentage of weekly audits that pass without creating an issue | > 75% | Count of `audit-failure` issues created per month |
| Mean time to quality issue resolution | Average hours from audit finding to fix merge | < 48 hours | Git timestamps on nightly fix PRs |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.5 Quality Management | This process implements quality management activities |
| ISO/IEC 12207:2017 | 6.3.5.3 Quality Assurance | Quality gates and audits implement assurance activities |
| CMMI-DEV v2.0 | PPQA (Process and Product Quality Assurance) | Covers PPQA SP 1.1 (objectively evaluate processes) and SP 1.2 (objectively evaluate work products) |

## 12. Tailoring Guidance

**Minimum viable process (small project):** At minimum, the CI-enforced quality gates (fast-validate, validate-tier1) must remain active. Scheduled audits may be reduced to weekly only. Quality attribute documentation is recommended but not mandatory for projects under 5 plugins.

**Full ceremony (compliance-driven):** All scheduled audits run at their defined frequency. Quality attribute documents cover all architectural constraints. Trend analysis is performed monthly with findings documented. Quality gate pass/fail data is archived for audit evidence.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-005 | Depends on: Integration & Testing executes the quality gates defined here |
| PROC-SP-003 | Related: Verification & Validation provides formal verification evidence |
| PROC-SP-005 | Feeds into: Quality audit findings feed defect management |
| PROC-SP-006 | Related: Peer Review is a quality gate within the PR process |
| PROC-SEC-001 | Related: Secure Development quality attributes are managed here |

## 14. Traces

- **Governs:** `docs/quality/QA-*.md`, nightly review workflow output, weekly audit workflow output
- **Enforced by:** `push.yml` (`fast-validate`), `pr.yml` (`validate-tier1`, `semantic-check`), `nightly.yml` (scheduled nightly review), `weekly.yml` (scheduled weekly audit)
- **Related QA:** Testing standards in `.claude/rules/testing-standards.md`, quality gate definitions in this document

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing quality gate framework and scheduled audit mechanisms |

# PROC-ORG-002: Measurement & Analysis

**Version:** 1.0.0
**Status:** draft
**Category:** organizational
**Layer:** base
**Maturity:** initial
**Owner:** Technical Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Measurement & Analysis establishes a disciplined approach to defining metrics, collecting data, analyzing trends, and reporting findings that inform decision-making across the claude-kit project. Currently, CI timing data and validation pass rates are implicitly available in GitHub Actions logs but are not formally collected or analyzed. This process transforms ad hoc observations into a structured measurement program that supports continuous improvement and maturity assessment.

## 2. Scope

**Included:**
- Definition of project-level and process-level metrics
- Data collection from CI/CD pipelines, GitHub repository statistics, and process execution records
- Trend analysis over time (weekly, monthly, quarterly)
- Reporting findings via benchmark documents in `docs/benchmarks/`
- Providing measurement inputs to other processes (PROC-LC-008, PROC-ORG-001, PROC-ORG-004)

**Excluded:**
- Business metrics (revenue, customer count) — those are outside the QMS scope
- Individual performance measurement — metrics are process-oriented, not people-oriented
- Metric target-setting for external compliance (handled by PROC-GOV-009)

## 3. Entry Criteria

- [ ] A new process has been created that requires performance tracking
- [ ] A scheduled measurement collection interval has arrived (weekly, monthly, or quarterly)
- [ ] An improvement proposal (PROC-LC-008) requires baseline data to evaluate effectiveness

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| CI workflow run data | GitHub Actions API | JSON via `gh api` |
| Validation results | `fast-validate` and `pr-validate` workflow logs | Structured output (JSON/text) |
| Process metrics definitions | Each process document Section 10 | Markdown tables |
| Nightly review summaries | `nightly.yml` workflow | Workflow step summary |
| Weekly audit results | `weekly.yml` workflow | GitHub Issues |
| Plugin validation counts | `scripts/validate-plugins.py --all --json` | JSON output |
| Git repository statistics | Git log, GitHub API | Commit counts, PR stats |

## 5. Activities

### 5.1 Metric Definition

For each process in the QMS, review Section 10 (Metrics) and ensure each metric has:
- A clear, unambiguous description of what is measured
- A specific collection method that can be executed repeatably
- A target value or trend direction
- A designated collection frequency (per-push, daily, weekly, monthly, quarterly)

Maintain a consolidated metric registry as a section in the relevant benchmark document. Metrics should be SMART: Specific, Measurable, Achievable, Relevant, Time-bound.

### 5.2 Data Collection

Execute data collection at the prescribed intervals:

**Per-push (automated):** CI pipeline timing, validation pass/fail counts, and test layer execution times are captured automatically by GitHub Actions. No manual collection needed.

**Weekly:** Extract the following from GitHub Actions and repository data:
- `fast-validate` pass rate across all pushes in the past week
- Number of PR autofix attempts and their success rate
- Number of nightly review findings
- Plugin validation error counts by category

**Monthly:** Aggregate weekly data into monthly summaries. Add:
- PR merge cycle time (open to merge)
- Documentation coverage changes (new docs created vs. gaps identified)
- Process execution counts (how many times each process was invoked)

**Quarterly:** Compile trend analysis across monthly summaries. Add:
- Process maturity progression
- Year-over-year comparisons (when data spans are sufficient)

### 5.3 Trend Analysis

Analyze collected data for patterns:
- **Improving trends:** Validate that improvements implemented via PROC-LC-008 are having the expected effect
- **Degrading trends:** Flag areas where metrics are moving in the wrong direction; create improvement signals
- **Flat trends:** Assess whether targets need adjustment or whether the current level is acceptable
- **Anomalies:** Investigate sudden spikes or drops; determine if they are one-time events or indicate systemic changes

### 5.4 Reporting

Create or update benchmark documents in `docs/benchmarks/` with BM-XXX identifiers. Each report should contain:
- The metric definitions and collection methodology
- Raw data tables or summaries
- Trend charts (described in text for markdown compatibility)
- Analysis and recommended actions
- Links to relevant process documents and improvement items

### 5.5 Metric Review

Quarterly, review the metric set itself:
- Are all metrics still relevant? Remove metrics that no one acts on.
- Are targets still appropriate? Adjust based on achieved performance.
- Are there gaps? Add metrics for newly created processes.
- Is collection sustainable? Simplify metrics that require disproportionate effort to collect.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Benchmark reports | `docs/benchmarks/` | — | BM-XXX |
| Benchmark index | `docs/benchmarks/INDEX.md` | — | — |
| Metric registry | Embedded in benchmark documents | — | — |
| Trend analysis | Embedded in benchmark documents | — | — |

## 7. Exit Criteria

- [ ] Data collected for all metrics at the prescribed frequency
- [ ] Trend analysis completed and documented in `docs/benchmarks/`
- [ ] Degrading trends flagged as improvement signals to PROC-LC-008
- [ ] `bash scripts/validate-docs.sh` passes with new or updated benchmark documents

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Collection completeness | Audit metric registry against collected data | All metrics with a collection date within their prescribed interval |
| Data accuracy | Spot-check collected values against source data | No discrepancies greater than 5% between reported and actual values |
| Actionability | Review trend analysis | At least one actionable recommendation per quarterly report |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Technical Lead | Owns the measurement program; defines and reviews metrics; approves benchmark reports |
| DevOps Lead | Automates data collection from CI/CD pipelines; maintains collection scripts |
| Quality Lead | Ensures metrics align with process maturity requirements; uses measurement data in maturity assessments |
| Developer | Provides context for anomalies; acts on improvement recommendations |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Metric coverage | Percentage of active processes with at least one collected metric | 100% | Cross-reference process catalog with collection records |
| Collection timeliness | Percentage of metrics collected within their prescribed interval | >= 90% | Audit collection timestamps |
| Report currency | Time since last benchmark report update | < 30 days for monthly metrics | Check `docs/benchmarks/` modification dates |
| Action conversion rate | Percentage of trend analysis recommendations that result in tracked actions | >= 50% | Cross-reference reports with improvement backlog |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 7.2.7 Measurement | Systematic measurement of software processes and products |
| ISO/IEC 15939 | Measurement process | Defines the information model for software measurement |
| CMMI | MA (Measurement and Analysis) | Organizational measurement capability |
| NIST SP 800-218 | PO.4 | Monitoring and measuring secure development practices |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Collect only automated metrics (CI pass rate, pipeline timing) and review them monthly. Skip formal benchmark documents — a simple markdown table in `docs/benchmarks/` updated monthly suffices. Focus on 3-5 key metrics rather than comprehensive coverage.

**Full ceremony (team):** Execute all activities. Automate weekly collection via a scheduled GitHub Action or script. Produce monthly benchmark reports and quarterly trend analyses. Maintain a living metric dashboard.

**When to simplify:** During early project phases (pre-v1.0), focus measurement on development velocity metrics (PR cycle time, validation pass rate) rather than operational metrics. Add operational metrics as the product matures and deployment frequency increases.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-008 | Feeds into: trend data and degrading metrics create improvement signals; receives from: improvement effectiveness data |
| PROC-ORG-001 | Feeds into: measurement data supports process maturity assessments |
| PROC-ORG-004 | Feeds into: metric trends inform risk likelihood assessments |
| PROC-SP-002 | Related: quality assurance metrics are part of the measurement program |
| PROC-LC-007 | Receives from: MTTR and deployment success rate as operational metrics |
| PROC-SP-005 | Receives from: defect density and resolution time as quality metrics |

## 14. Traces

- **Governs:** `docs/benchmarks/` (BM-XXX reports, methodology, baselines, results)
- **Enforced by:** `scripts/validate-docs.sh` (benchmark document structure); CI pipeline (automated data source)
- **Related QA:** Measurement capability, data-driven decision making, process maturity evidence

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes implicit CI data collection into a governed measurement program |

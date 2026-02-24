# coding-embedded-zephyr-grader

> **Role:** Grader · **Version:** 0.1.0

Objective, blind, quantitative code grading agent for embedded Zephyr RTOS applications. Produces numerical scorecards across 9 weighted dimensions using automated tools (cppcheck, clang-tidy, lizard, west build, checkpatch, arm-zephyr-eabi-size) and structured rubrics. Supports single-submission grading and A/B blind comparison modes.

```bash
claude-kit --kit coding-embedded-zephyr-grader
# or load the full team:
claude-kit --kit coding-embedded-zephyr
```

**Companion auto-loaded:** `coding-embedded-zephyr-knowledge` (Zephyr domain reference for review context)

---

## Agents

| Agent | Description |
|-------|-------------|
| `submission-intake` | Validates Zephyr submission directory structure, strips identifying metadata, creates isolated build directories, and outputs a normalized submission descriptor JSON. Use when a new submission path needs to be ingested and validated before grading begins. |
| `metrics-collector` | Collects code metrics (cyclomatic complexity, NLOC, comment density) and style violations using lizard, cloc, and checkpatch.pl. Produces separate code_metrics_score and style_score. |
| `resource-analyzer` | Analyzes flash and RAM usage of compiled Zephyr submissions using arm-zephyr-eabi-size, ram_report, and rom_report. Computes resource efficiency against board capacity. Supports A/B comparison mode with Bloaty diffs. |
| `compilability-checker` | Builds Zephyr submissions against the project-specified hardware target board(s), captures exit codes and warning counts per board, and scores compilability. |
| `completeness-checker` | Checks submission completeness (required files, test structure, documentation quality) and produces separate completeness and documentation scores. |
| `static-analyzer` | Runs cppcheck and clang-tidy on Zephyr submissions, parses findings, applies weighted deduplication, normalizes defect density per KLOC, and produces a static analysis score. |
| `style-checker` | Runs checkpatch.pl on Zephyr submissions to assess coding style compliance, parses violations by type and severity, normalizes per KLOC, and produces a style score. |
| `zephyr-reviewer` | Evaluates Zephyr RTOS correctness patterns including kernel object initialization, thread safety, ISR safety, devicetree bindings, Kconfig dependencies, and 20+ other domain-specific checks. |
| `architecture-reviewer` | Evaluates software architecture quality of Zephyr submissions including module separation, header organization, abstraction layers, callback patterns, configurability, testability, and error propagation. |
| `diff-analyzer` | Performs deep source-level differential analysis between two Zephyr submissions, comparing algorithmic approaches, design patterns, API usage, and architecture choices. |
| `comparison-analyzer` | Analyzes two independently graded Zephyr submissions side-by-side, computing per-dimension deltas, identifying winner per dimension, ranking largest advantages, and producing a structured comparison analysis. |
| `comparison-report-generator` | Generates formatted A/B comparison reports in Markdown, JSON, and HTML from comparison analysis data. Produces side-by-side tables, delta visualizations, winner analysis, and individual scorecards. |
| `score-aggregator` | Aggregates scores from all grading dimension agents, applies configurable weights, handles N/A redistribution, and computes the final weighted score. Supports A/B comparison mode with per-dimension deltas. |
| `report-generator` | Generates grading reports in Markdown, JSON, and HTML formats from the aggregated scorecard. Includes per-dimension drill-downs, visual score bars, findings summaries, and A/B comparison tables. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-embedded-zephyr-grader:grade` | Single submission grading orchestrator. Validates submission structure, runs the full automated tool pipeline across 9 weighted dimensions, and produces a comprehensive scorecard. |
| `/coding-embedded-zephyr-grader:compare` | A/B comparison grading. Strips identifying metadata, grades both submissions independently with blind randomization, then produces a side-by-side delta report with per-dimension winner analysis. |

---

## Grading Dimensions

9 weighted dimensions: compilability, resource usage, code metrics, static analysis, style, Zephyr patterns, architecture, completeness, testing.

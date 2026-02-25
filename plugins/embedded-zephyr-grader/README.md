# embedded-zephyr-grader

> **Role:** Grader · **Version:** 0.2.2

Objective, blind, quantitative code grading agent for embedded Zephyr RTOS applications. Produces numerical scorecards across 9 weighted dimensions using automated tools (cppcheck, clang-tidy, lizard, west build, checkpatch, arm-zephyr-eabi-size) and structured rubrics. Supports single-submission grading and A/B blind comparison modes.

```bash
claude-kit --kit embedded-zephyr-grader
# or load the full team:
claude-kit --kit embedded-zephyr
```

**Companion auto-loaded:** `embedded-zephyr-knowledge` (Zephyr domain reference for review context)

---

## Agents

| Agent | Description |
|-------|-------------|
| `submission-intake` | Validates Zephyr submission directory structure, strips identifying metadata, creates isolated build directories, detects target board(s) from build configuration files, and outputs a normalized submission descriptor JSON. Use when a new submission path needs to be ingested and validated before grading begins. |
| `metrics-collector` | Collects code metrics (cyclomatic complexity, NLOC, comment density) and style violations using lizard, cloc, and checkpatch.pl. Produces separate code_metrics_score and style_score. Use when you need quantitative code complexity and style compliance data. |
| `resource-analyzer` | Analyzes flash and RAM usage of compiled Zephyr submissions using arm-zephyr-eabi-size, ram_report, and rom_report. Computes resource efficiency against board capacity. Supports A/B comparison mode with Bloaty diffs. Use when you need to evaluate how efficiently a submission uses memory resources. |
| `compilability-checker` | Builds Zephyr submissions against project-specified hardware target(s), captures exit codes and warning counts, and scores compilability. Use when you need to determine whether a submission compiles and how cleanly it builds. |
| `completeness-checker` | Checks submission completeness (required files, test structure, documentation quality) and produces separate completeness and documentation scores. Use when you need to evaluate whether a submission includes all expected deliverables and adequate documentation. |
| `static-analyzer` | Runs cppcheck and clang-tidy on Zephyr submissions, parses findings, applies weighted deduplication, normalizes defect density per KLOC, and produces a static analysis score. Use when you need automated defect detection and code quality metrics from static analysis tools. |
| `style-checker` | Runs checkpatch.pl on Zephyr submissions to assess coding style compliance, parses violations by type and severity, normalizes per KLOC, and produces a style score. Use when you need automated style and formatting analysis. |
| `zephyr-reviewer` | Evaluates Zephyr RTOS correctness patterns including kernel object initialization, thread safety, ISR safety, devicetree bindings, Kconfig dependencies, and 20+ other domain-specific checks. Use when you need expert assessment of whether code correctly uses Zephyr APIs and follows RTOS best practices. |
| `architecture-reviewer` | Evaluates software architecture quality of Zephyr submissions including module separation, header organization, abstraction layers, callback patterns, configurability, testability, and error propagation. Use when you need expert assessment of code structure and design quality beyond correctness. |
| `diff-analyzer` | Performs deep source-level differential analysis between two Zephyr submissions, comparing algorithmic approaches, design patterns, API usage, and architecture choices. Use when users request explanation of score differences or detailed code-level comparison. |
| `comparison-analyzer` | Analyzes two independently graded Zephyr submissions side-by-side, computing per-dimension deltas, identifying winner per dimension, ranking largest advantages, and producing a structured comparison analysis. Use after both submissions have been graded. |
| `comparison-report-generator` | Generates formatted A/B comparison reports in Markdown, JSON, and HTML from comparison analysis data. Produces side-by-side tables, delta visualizations, winner analysis, and individual scorecards. Use after comparison-analyzer completes. |
| `score-aggregator` | Aggregates scores from all grading dimension agents, applies configurable weights, handles N/A redistribution, and computes the final weighted score. Supports A/B comparison mode with per-dimension deltas. Use when all dimension scores are collected and need to be combined into a final grade. |
| `report-generator` | Generates grading reports in Markdown, JSON, and HTML formats from the aggregated scorecard. Includes per-dimension drill-downs, visual score bars, findings summaries, and A/B comparison tables. Use when grading is complete and formatted output needs to be written to the output directory. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/embedded-zephyr-grader:grade` | Single submission grading orchestrator. Validates submission structure, runs the full automated tool pipeline across 9 weighted dimensions, and produces a comprehensive scorecard. |
| `/embedded-zephyr-grader:compare` | A/B comparison grading. Strips identifying metadata, grades both submissions independently with blind randomization, then produces a side-by-side delta report with per-dimension winner analysis. |

---

## Grading Dimensions

9 weighted dimensions: compilability, resource usage, code metrics, static analysis, style, Zephyr patterns, architecture, completeness, testing.

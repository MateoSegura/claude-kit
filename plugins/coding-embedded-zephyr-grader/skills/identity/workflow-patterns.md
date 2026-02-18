# Workflow Patterns: Step-by-Step Grading Procedures

This document contains detailed, step-by-step workflows for the grading agent's primary operations. Each workflow includes decision points, exact commands, and error handling.

## Workflow 1: Single Submission Grading (`/grade`)

### Step 1: Submission Intake

```
1.1  Validate submission directory exists and contains at least one .c file
1.2  Check for CMakeLists.txt at the root — if missing, log WARNING (Completeness impact)
1.3  Check for prj.conf at the root — if missing, log WARNING
1.4  Strip metadata: remove .git/ directory, sanitize file headers (strip author names, emails)
1.5  Run `cloc --include-lang=C --json <submission_dir>/src/` to measure SLOC
1.6  Record SLOC count. If SLOC = 0, ABORT grading with error: "No C source lines found."
1.7  Create isolated working directory: /tmp/grading-<uuid>/
1.8  Copy sanitized submission into working directory
```

### Step 2: Compilability Gate

```
2.1  For each target board in [qemu_cortex_m3, native_sim]:
     a. Run: west build -b <board> -d build_<board> <work_dir> -- -DCONF_FILE=prj.conf
     b. Capture stdout + stderr to build_<board>.log
     c. Record: board, exit_code, wall_time, warning_count, error_count
2.2  Score per board: exit_code == 0 ? 100.0 : 0.0
2.3  Compilability score = average of all board scores
2.4  DECISION POINT:
     - If ALL boards fail: mark Resource Efficiency as N/A (no binary)
     - If SOME boards pass: proceed with binaries from passing boards only
     - If ALL boards pass: proceed normally
2.5  Extract warning count from build logs (grep -c "warning:" build_<board>.log)
     Warnings are recorded but do not affect Compilability score (they affect Static Analysis)
```

### Step 3: Parallel Tool Execution

Launch all tools in parallel. Each tool operates independently.

```
3.1  [PARALLEL] cppcheck on src/ files
3.2  [PARALLEL] clang-tidy on src/ files (requires successful build for compile_commands.json)
3.3  [PARALLEL] lizard on src/ files
3.4  [PARALLEL] checkpatch.pl on each .c and .h file
3.5  [PARALLEL] arm-zephyr-eabi-size on each successful build artifact
3.6  [PARALLEL] bloaty on each successful build artifact
3.7  Collect all tool outputs. For each tool:
     a. If tool succeeded: parse output per coding-standards.md
     b. If tool not found: mark dependent dimension as N/A with reason "Tool <name> not available"
     c. If tool crashed/timed out: mark as N/A with reason "Tool <name> failed: <error>"
```

### Step 4: LLM Rubric Evaluation

Run for each LLM-evaluated dimension. If `llm_passes > 1`, run each pass independently.

```
4.1  Zephyr Correctness rubric (25+ pattern checks):
     - Evaluate against the Zephyr patterns checklist
     - Score each pattern: 0 / 0.5 / 1.0
     - Cite file:line for each finding
4.2  Architecture rubric:
     - Module separation (single-file vs multi-file, header/source split)
     - Layering (hardware abstraction, application logic separation)
     - Coupling (direct HW register access vs API usage)
     - Cohesion (function grouping, file purpose clarity)
     - Cite file:line for each observation
4.3  Documentation rubric:
     - Doxygen on public functions: present / absent / partial
     - Inline comments at decision points: present / absent
     - README quality: build instructions, description, usage
     - Cite specific functions or sections
4.4  If llm_passes > 1:
     a. Run each pass without visibility of other pass results
     b. Collect all pass scores per dimension
     c. Compute median, standard deviation
     d. If stddev > 15.0, flag dimension as "high variance"
```

### Step 5: Score Aggregation

```
5.1  For each tool-measured dimension:
     a. Apply weighted deduplication to findings
     b. Compute per-KLOC defect density
     c. Convert density to 0-100 score per coding-standards.md formulas
5.2  For each LLM-evaluated dimension:
     a. Use median score if llm_passes > 1, else use single pass score
5.3  Identify N/A dimensions, compute weight redistribution
5.4  Compute final score: sum(score_i * adjusted_weight_i)
5.5  Round final score to 1 decimal place
```

### Step 6: Report Generation

```
6.1  Generate Markdown report:
     - Header (date, mode, boards, SLOC, tool versions, LLM passes)
     - Score summary table (dimension, score, weight, adjusted weight, label)
     - Final score in bold
     - Per-dimension evidence sections with findings tables
     - Tool command log (exact commands used)
6.2  Generate JSON report:
     - Same data as Markdown in structured format
     - Schema: { metadata: {}, dimensions: [{name, score, weight, adjusted_weight, label, evidence: []}], final_score, na_dimensions: [] }
6.3  Generate HTML report:
     - Convert Markdown to HTML
     - Add collapsible <details> sections for per-dimension evidence
     - Inline CSS for table styling (no external dependencies)
6.4  Write all three files to output directory
```

## Workflow 2: A/B Blind Comparison (`/compare`)

### Step 1: Dual Intake

```
1.1  Receive two submission paths
1.2  Label them "Submission A" and "Submission B" (based on argument order, nothing else)
1.3  Run intake (Workflow 1, Step 1) on each independently
1.4  Verify both have SLOC > 0
```

### Step 2: Randomize Evaluation Order

```
2.1  Generate random boolean using system entropy: eval_A_first = (random bit == 1)
2.2  Record evaluation order in internal state (NOT in the report)
2.3  Set evaluation_order = [A, B] if eval_A_first else [B, A]
```

### Step 3: Independent Grading

```
3.1  Grade evaluation_order[0] using full Workflow 1 (Steps 2-5)
3.2  CRITICAL: Clear all intermediate state, tool caches, and context
3.3  Grade evaluation_order[1] using full Workflow 1 (Steps 2-5)
3.4  At no point during grading of the second submission may scores or findings
     from the first submission be visible or referenced
```

### Step 4: Comparison Report

```
4.1  Generate side-by-side comparison table:
     | Dimension | Sub A Score | Sub B Score | Delta (A-B) | Winner |
4.2  Winner per dimension: higher score wins. If |delta| < 1.0, mark "Tie"
4.3  Overall winner: higher final score. If |delta| < 2.0, mark "Tie"
4.4  DO NOT include editorial commentary on why one is "better"
4.5  Include full individual reports for each submission as appendices
4.6  Generate all three formats (Markdown, JSON, HTML)
```

## Workflow 3: Handling Non-Compiling Submissions

When `west build` fails for ALL target boards:

```
1.  Compilability score = 0.0
2.  Mark as N/A with justification:
    - Resource Efficiency: "No compiled binary available"
3.  Proceed with all other dimensions:
    - Static Analysis: Run cppcheck (does not require compilation)
                       clang-tidy requires compile_commands.json -- if unavailable, run
                       cppcheck only and note clang-tidy as "requires successful build"
    - Code Metrics: lizard operates on source files (no build required)
    - Style: checkpatch.pl operates on source files (no build required)
    - Architecture: LLM rubric on source (no build required)
    - Zephyr Correctness: LLM rubric on source (no build required)
    - Completeness: checklist evaluation (no build required)
    - Documentation: LLM rubric on source (no build required)
4.  Redistribute Resource Efficiency weight (15%) across remaining 8 dimensions
5.  In the report, prominently note: "Submission did not compile on any target board.
    Resource Efficiency could not be measured. Weight redistributed."
```

When `west build` fails for SOME (not all) boards:

```
1.  Compilability score = (passing_boards / total_boards) * 100.0
2.  Resource Efficiency: measured only on passing board builds
3.  All other dimensions: proceed normally (source-level analysis is board-independent)
4.  Note in report which boards passed and which failed, with build log excerpts
```

## Workflow 4: Handling Missing Tools (Graceful Degradation)

Before starting any grading run, verify tool availability:

```
1.  For each required tool in [west, cppcheck, clang-tidy, lizard, checkpatch.pl,
    arm-zephyr-eabi-size, bloaty, cloc]:
    a. Run: which <tool> or <tool> --version
    b. Record: tool_name, available (bool), version_string
2.  Report tool availability in the report header
3.  For each missing tool:
    a. Identify affected dimension(s)
    b. Check if alternative measurement exists:
       - cppcheck missing + clang-tidy available: Static Analysis scored by clang-tidy only
       - clang-tidy missing + cppcheck available: Static Analysis scored by cppcheck only
       - Both missing: Static Analysis = N/A
       - lizard missing: Code Metrics = N/A
       - checkpatch.pl missing: Style = N/A
       - size/bloaty missing: Resource Efficiency = N/A
       - cloc missing: use fallback line counting (grep-based)
       - west missing: ABORT — cannot grade without build system
    c. Mark affected dimensions as N/A with reason
    d. Apply weight redistribution
4.  If more than 3 dimensions are N/A, emit a WARNING:
    "Grading reliability is degraded. X of 9 dimensions could not be measured.
    Consider installing missing tools: [list]"
```

## Workflow 5: Multi-Board Compilation Check

For validating across additional boards beyond the defaults:

```
1.  Accept board list from user configuration or command arguments
    Default: [qemu_cortex_m3, native_sim]
    Extended example: [qemu_cortex_m3, native_sim, nrf52840dk/nrf52840, nucleo_f401re]
2.  For each board in the list:
    a. Verify board is known: west boards | grep <board>
       If unknown, skip with WARNING: "Board <board> not recognized by west"
    b. Run: west build -b <board> -d build_<board_safe_name> <work_dir>
       (board_safe_name = board name with / replaced by _)
    c. Capture full build log
    d. Record: board, pass/fail, ROM size, RAM size (if pass), warning count
3.  Compilability score = (passing_boards / total_boards) * 100.0
4.  Resource Efficiency: average ROM/RAM metrics across all passing boards
5.  Report per-board results table:
    | Board | Result | ROM (B) | RAM (B) | Warnings | Build Time |
6.  If a board-specific overlay exists (<submission>/boards/<board>.overlay),
    note it was used. If no overlay exists for a board and it fails,
    note "No board-specific overlay provided" in the failure reason.
```

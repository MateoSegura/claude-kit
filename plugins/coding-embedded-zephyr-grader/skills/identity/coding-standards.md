# Coding Standards: Tool Invocation, Parsing, and Score Computation

This document defines the exact procedures for invoking tools, parsing their output, computing normalized scores, and formatting results. Every subagent that handles tool output or score computation MUST follow these standards.

## Tool Invocation Reference

### west build (Compilability)

```bash
# For each target board:
west build -b qemu_cortex_m3 -d build_qemu <submission_dir> -- -DCONF_FILE=prj.conf
west build -b native_sim -d build_native <submission_dir> -- -DCONF_FILE=prj.conf
```

- Capture BOTH stdout and stderr. Build warnings appear in stderr.
- Exit code 0 = pass. Any non-zero = fail.
- Score per board: 100.0 (pass) or 0.0 (fail). No partial credit.
- Dimension score = average across all target boards.
- Example: 2 boards, 1 passes, 1 fails = `(100.0 + 0.0) / 2 = 50.0`

### cppcheck (Static Analysis)

```bash
cppcheck --enable=all --std=c99 \
  --template='{file}:{line}:{severity}:{id}:{message}' \
  --suppress=missingIncludeSystem \
  --suppress=unmatchedSuppression \
  -I <submission_dir>/include \
  <submission_dir>/src/
```

- Parse each output line into: `file`, `line`, `severity`, `rule_id`, `message`
- Valid severities: `error`, `warning`, `style`, `performance`, `portability`, `information`

### clang-tidy (Static Analysis)

```bash
clang-tidy -p build/ \
  --checks='-*,bugprone-*,cert-*,clang-analyzer-*,performance-*,portability-*' \
  <submission_dir>/src/*.c 2>&1
```

- Parse output lines matching: `file:line:col: severity: message [check-name]`
- Map clang-tidy severities: `error` -> error, `warning` -> warning, `note` -> note

### lizard (Code Metrics)

```bash
lizard --CCN 15 --length 100 -w <submission_dir>/src/ --csv
```

- CSV columns: NLOC, CCN, Token, Param, Length, Location, File, Function
- CCN = cyclomatic complexity number. Threshold: 15 (flagged by `-w`).
- Function length threshold: 100 lines.
- Violations = functions exceeding either threshold.

### checkpatch.pl (Style)

```bash
${ZEPHYR_BASE}/scripts/checkpatch.pl --no-tree --terse -f <file>
```

- Run per-file. Parse output for `ERROR:`, `WARNING:`, `CHECK:` prefixes.
- Map: `ERROR` -> error, `WARNING` -> warning, `CHECK` -> note

### arm-zephyr-eabi-size (Resource Efficiency)

```bash
arm-zephyr-eabi-size build_qemu/zephyr/zephyr.elf
```

- Output columns: `text`, `data`, `bss`, `dec`, `hex`, `filename`
- Extract: `text` (ROM code), `data` (initialized data in ROM+RAM), `bss` (zero-init RAM)
- Total ROM = text + data. Total RAM = data + bss.

### bloaty (Resource Efficiency)

```bash
bloaty build_qemu/zephyr/zephyr.elf -d sections -n 0 --csv
```

- CSV columns: `sections`, `vmsize`, `filesize`
- Use for detailed section breakdown in evidence. Not directly scored -- supplements `size` output.

### cloc (Line Counting)

```bash
cloc --include-lang=C --json <submission_dir>/src/
```

- Extract `SUM.code` from JSON output. This is the SLOC count for normalization.
- If cloc is unavailable, count non-blank non-comment lines with: `grep -cvP '^\s*(//|/\*|\*|$)' src/*.c`

## Severity Weight Table

All tool findings are scored by severity using these weights:

| Severity | Weight | Examples |
|----------|--------|----------|
| error | 10 | cppcheck error, clang-tidy error, checkpatch ERROR |
| warning | 3 | cppcheck warning/performance/portability, clang-tidy warning, checkpatch WARNING |
| note | 1 | cppcheck style/information, clang-tidy note, checkpatch CHECK |

## Per-KLOC Normalization

All finding-based scores use defect density, not raw counts.

```
sloc = <SLOC from cloc>
kloc = sloc / 1000.0
# Minimum kloc floor to prevent division instability on tiny submissions:
kloc = max(kloc, 0.1)

raw_weighted_findings = sum(severity_weight * deduplicated_count_per_severity)
defect_density = raw_weighted_findings / kloc
```

## Weighted Deduplication Algorithm

Before scoring, deduplicate findings from each tool independently:

```
1. Group findings by (tool, rule_id)
2. For each group:
   a. Sort by file:line (deterministic ordering)
   b. First finding: multiplier = 1.0
   c. Each subsequent finding: multiplier = 0.1
   d. Effective count = 1.0 + (N-1) * 0.1  where N = total findings in group
3. Apply severity weight to effective count
```

Example: 8 identical `cppcheck` `nullPointer` warnings:
- Effective count = 1.0 + 7 * 0.1 = 1.7
- Weighted = 1.7 * 3 (warning weight) = 5.1
- Without dedup: 8 * 3 = 24.0

## Score Computation: Finding-Based Dimensions

For Static Analysis, Code Metrics, and Style, convert defect density to a 0-100 score:

```
# Thresholds define the density range that maps to 0-100
# These are calibrated for Zephyr embedded C code
max_acceptable_density = {
  "static_analysis": 50.0,   # findings-weighted per KLOC
  "code_metrics":    30.0,   # violations-weighted per KLOC
  "style":           80.0    # checkpatch findings-weighted per KLOC
}

score = max(0.0, 100.0 - (defect_density / max_acceptable_density * 100.0))
score = round(score, 1)  # 1 decimal place
```

If defect density exceeds max_acceptable_density, score floors at 0.0.

## Score Computation: Resource Efficiency

```
# Reference baselines for a minimal Zephyr application on qemu_cortex_m3:
baseline_rom = 32768   # 32 KB
baseline_ram = 8192    # 8 KB

# Actual from size output:
actual_rom = text + data
actual_ram = data + bss

# Efficiency ratio (lower is better):
rom_ratio = actual_rom / baseline_rom
ram_ratio = actual_ram / baseline_ram

# Score: 100 at baseline, decreasing linearly, floor at 0
# Applications up to 4x baseline score above 0
rom_score = max(0.0, 100.0 - (rom_ratio - 1.0) * 33.3)
ram_score = max(0.0, 100.0 - (ram_ratio - 1.0) * 33.3)

resource_score = round((rom_score * 0.5 + ram_score * 0.5), 1)
```

For non-compiling submissions, Resource Efficiency = N/A (no binary to measure).

## N/A Weight Redistribution

When dimension `j` is N/A:

```
remaining_weight = 1.0 - sum(weight_i for all N/A dimensions)
For each scored dimension i:
  adjusted_weight_i = original_weight_i / remaining_weight
```

Example: Resource Efficiency (15%) is N/A.
- Remaining weight = 1.0 - 0.15 = 0.85
- Compilability adjusted: 0.20 / 0.85 = 0.2353
- Static Analysis adjusted: 0.15 / 0.85 = 0.1765
- (and so on for all scored dimensions)

Always show both original and adjusted weights in the report.

## Score Formatting Rules

- All scores: 0-100 scale, exactly 1 decimal place. Use `72.3` not `72` or `72.30`.
- Weights: show as percentages with 1 decimal place after redistribution (e.g., `23.5%`).
- Deltas in A/B mode: show with sign. `+4.2` or `-11.7`. Zero delta = `0.0`.
- Finding counts: always show both raw and deduplicated effective counts.
- Per-KLOC densities: 2 decimal places (e.g., `12.47 per KLOC`).
- Resource sizes: show in bytes and human-readable (e.g., `24576 B (24.0 KB)`).

## Report Header Template

Every report MUST begin with:

```markdown
# Code Grading Report
- **Date**: YYYY-MM-DD HH:MM:SS UTC
- **Mode**: Single | A/B Comparison
- **Target Boards**: qemu_cortex_m3, native_sim
- **SLOC**: <count> (measured by cloc)
- **Tool Versions**: cppcheck <ver>, clang-tidy <ver>, lizard <ver>, west <ver>
- **LLM Passes**: <count> (for subjective dimensions)
```

## MISRA Compliance (Optional)

MISRA checks are disabled by default. When enabled via configuration:

```bash
cppcheck --enable=all --std=c99 --addon=misra.json \
  --template='{file}:{line}:{severity}:{id}:{message}' \
  <submission_dir>/src/
```

MISRA findings are scored separately and reported as an addendum. They do NOT affect the main 9-dimension score unless the user explicitly configures MISRA as a replacement for the Style dimension.

## LLM Rubric Evaluation Standards

For Architecture, Zephyr Correctness, and Documentation dimensions:

- Each rubric is a checklist of specific, testable criteria
- Each criterion is scored: 0 (absent/violated), 0.5 (partial), 1.0 (fully met)
- Dimension score = (sum of criterion scores / number of criteria) * 100.0
- Every criterion score MUST cite at least one `file:line` reference or the explicit absence of expected content
- When `llm_passes > 1`, run each pass with a fresh context (no prior pass results visible)

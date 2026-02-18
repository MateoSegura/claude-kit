---
name: coding-embedded-zephyr-grader:tool-pipeline
description: "Tool execution pipeline for Zephyr grading including west build, cppcheck, clang-tidy, lizard, cloc, checkpatch, size analysis, ram/rom reports, and bloaty with execution order, parallelism strategy, and availability detection."
---

# Tool Pipeline

Reference for the static analysis and metrics collection tools used in automated grading.

## Pipeline Overview

```
1. Intake → Parse submission, detect board
2. Compilability Gate → west build (BLOCKING)
    ├─ Success: Continue to parallel tools
    └─ Failure: Skip resource tools, continue with source-only tools

3. Parallel Execution (if compiled):
    ├─ Static Analysis: cppcheck + clang-tidy
    ├─ Code Metrics: lizard + cloc
    ├─ Style: checkpatch.pl
    └─ Resource Analysis: size + ram_report + rom_report + bloaty

4. Parallel Execution (if NOT compiled):
    ├─ Static Analysis: cppcheck (best-effort) + clang-tidy (best-effort)
    ├─ Code Metrics: lizard + cloc (work on source)
    └─ Style: checkpatch.pl (works on source)

5. Aggregation → Collect all results
```

## Execution Order and Parallelism

### Phase 1: Sequential (Blocking)
1. **west build** — MUST complete first, determines what tools can run

### Phase 2: Parallel (if build succeeded)
Run all tools simultaneously:
- cppcheck (2-10s)
- clang-tidy (5-30s)
- lizard (1-3s)
- cloc (1-2s)
- checkpatch (2-5s)
- arm-zephyr-eabi-size (instant)
- west build -t ram_report (2-5s)
- west build -t rom_report (2-5s)
- bloaty (1-3s)

Total parallel time: ~30s (vs ~60s sequential)

### Phase 3: Parallel (if build failed)
Run source-only tools:
- cppcheck --force (best-effort)
- clang-tidy (may fail)
- lizard
- cloc
- checkpatch

## Tool Availability Detection

Before running pipeline, detect available tools:

```bash
# Check each tool
command -v west >/dev/null 2>&1 || echo "west: MISSING"
command -v cppcheck >/dev/null 2>&1 || echo "cppcheck: MISSING"
command -v clang-tidy >/dev/null 2>&1 || echo "clang-tidy: MISSING"
command -v lizard >/dev/null 2>&1 || echo "lizard: MISSING"
command -v cloc >/dev/null 2>&1 || echo "cloc: MISSING"
command -v checkpatch.pl >/dev/null 2>&1 || echo "checkpatch: MISSING"
command -v arm-zephyr-eabi-size >/dev/null 2>&1 || echo "size: MISSING"
command -v bloaty >/dev/null 2>&1 || echo "bloaty: MISSING"
```

**Fallback strategy:**
- If both cppcheck and clang-tidy missing → Static Analysis = N/A
- If lizard missing → Use cloc only, mark CCN = N/A
- If checkpatch missing → Style = N/A
- If bloaty missing → Use size only for resource analysis

## Quick Reference: Tool Commands

| Tool | Command Template | Output Format |
|------|------------------|---------------|
| west build | `west build -b <board> -p always <path>` | Build log (text) |
| cppcheck | `cppcheck --xml --xml-version=2 --enable=all <path> 2>out.xml` | XML |
| clang-tidy | `clang-tidy -p build --checks='*' <files>` | Text |
| lizard | `lizard --csv -Ecpre <path> > out.csv` | CSV |
| cloc | `cloc --json --by-file <path> > out.json` | JSON |
| checkpatch | `checkpatch.pl --no-tree --terse -f <file>` | Text |
| size | `arm-zephyr-eabi-size build/zephyr/zephyr.elf` | Text (table) |
| ram_report | `west build -t ram_report > ram.txt` | Text (table) |
| rom_report | `west build -t rom_report > rom.txt` | Text (table) |
| bloaty | `bloaty --csv -d sections build/zephyr/zephyr.elf > out.csv` | CSV |

## Additional Resources

For detailed command syntax, exact flags, and output parsing templates:

- [tool-reference.md](tool-reference.md) — Each tool fully specified with command syntax, all flags explained, version-specific notes, troubleshooting, and example invocations
- [output-parsing.md](output-parsing.md) — Parsing templates for each tool's output format including regex patterns, jq queries for JSON, XML parsing, CSV parsing, and complete example raw outputs with annotations

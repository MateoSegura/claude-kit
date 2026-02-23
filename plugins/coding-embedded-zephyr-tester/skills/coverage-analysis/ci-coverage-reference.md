# CI Coverage Integration Reference

## GitHub Actions Coverage Workflow

```yaml
name: Coverage

on:
  pull_request:
    paths: ['src/**', 'tests/**']

jobs:
  coverage:
    runs-on: ubuntu-latest
    container: ghcr.io/zephyrproject-rtos/ci:v0.26.13

    steps:
      - uses: actions/checkout@v4

      - name: Initialize west workspace
        run: |
          west init -l .
          west update --narrow

      - name: Run tests with coverage
        run: |
          west twister -p native_sim -T tests/ \
            --coverage --coverage-tool gcovr \
            --coverage-formats json html \
            -O twister-out

      - name: Check coverage thresholds
        run: |
          LINE_COV=$(jq '.line_percent' twister-out/coverage/coverage.json)
          BRANCH_COV=$(jq '.branch_percent' twister-out/coverage/coverage.json)
          echo "Line: ${LINE_COV}%, Branch: ${BRANCH_COV}%"
          if (( $(echo "$LINE_COV < 80" | bc -l) )); then
            echo "::error::Line coverage ${LINE_COV}% below 80% threshold"
            exit 1
          fi
          if (( $(echo "$BRANCH_COV < 70" | bc -l) )); then
            echo "::error::Branch coverage ${BRANCH_COV}% below 70% threshold"
            exit 1
          fi

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: twister-out/coverage/

      - name: Post coverage summary to PR
        if: github.event_name == 'pull_request'
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: coverage
          message: |
            ## Coverage Report
            - Line: ${{ env.LINE_COV }}%
            - Branch: ${{ env.BRANCH_COV }}%
            [Full Report](link-to-artifact)
```

## Threshold Checking Script

```bash
#!/bin/bash
# check-coverage-threshold.sh
# Exit codes: 0 = pass, 1 = below threshold
set -euo pipefail

COVERAGE_FILE="${1:-twister-out/coverage/coverage.info}"
THRESHOLD_LINE="${COVERAGE_THRESHOLD_LINE:-80}"
THRESHOLD_BRANCH="${COVERAGE_THRESHOLD_BRANCH:-70}"
THRESHOLD_FUNCTION="${COVERAGE_THRESHOLD_FUNCTION:-95}"

if [ ! -f "$COVERAGE_FILE" ]; then
    echo "ERROR: Coverage file not found: $COVERAGE_FILE"
    exit 1
fi

LINE_COV=$(lcov --summary "$COVERAGE_FILE" 2>&1 | grep "lines" | grep -oP '[\d.]+%' | head -1 | tr -d '%')
BRANCH_COV=$(lcov --summary "$COVERAGE_FILE" 2>&1 | grep "branches" | grep -oP '[\d.]+%' | head -1 | tr -d '%')
FUNC_COV=$(lcov --summary "$COVERAGE_FILE" 2>&1 | grep "functions" | grep -oP '[\d.]+%' | head -1 | tr -d '%')

FAILED=0

echo "=== Coverage Summary ==="
echo "  Line:     ${LINE_COV}% (threshold: ${THRESHOLD_LINE}%)"
echo "  Branch:   ${BRANCH_COV}% (threshold: ${THRESHOLD_BRANCH}%)"
echo "  Function: ${FUNC_COV}% (threshold: ${THRESHOLD_FUNCTION}%)"
echo ""

if (( $(echo "$LINE_COV < $THRESHOLD_LINE" | bc -l) )); then
    echo "FAIL: Line coverage ${LINE_COV}% below threshold ${THRESHOLD_LINE}%"
    FAILED=1
fi

if (( $(echo "$BRANCH_COV < $THRESHOLD_BRANCH" | bc -l) )); then
    echo "FAIL: Branch coverage ${BRANCH_COV}% below threshold ${THRESHOLD_BRANCH}%"
    FAILED=1
fi

if (( $(echo "$FUNC_COV < $THRESHOLD_FUNCTION" | bc -l) )); then
    echo "FAIL: Function coverage ${FUNC_COV}% below threshold ${THRESHOLD_FUNCTION}%"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo "PASS: All coverage thresholds met"
fi

exit $FAILED
```

## Coverage Trend Tracking

### Per-Commit Coverage Storage

Store coverage metrics in a JSON file committed alongside code:

```bash
# Extract and append coverage data
DATE=$(date +%Y-%m-%d)
COMMIT=$(git rev-parse --short HEAD)
jq -n --arg d "$DATE" --arg c "$COMMIT" \
   --argjson l "$LINE_COV" --argjson b "$BRANCH_COV" --argjson f "$FUNC_COV" \
   '{date: $d, commit: $c, line: $l, branch: $b, function: $f}' \
   >> coverage-history.jsonl
```

### Trend Analysis Patterns

```
Coverage increase after commit → new tests added (good)
Coverage decrease after commit → new code without tests (flag for review)
Coverage unchanged after commit → acceptable if no code changes
Coverage decrease > 5% → block the PR
```

### Module-Level Granularity

Track coverage per module for targeted improvement:

```bash
# Extract per-directory coverage
lcov --summary coverage.info --list-full-path 2>&1 | \
  grep 'src/' | \
  awk '{print $1, $2}' | \
  sort -t'%' -k1 -n
```

## Coverage Report Filtering

### Filter to Application Code Only

```bash
# Remove Zephyr kernel, drivers, and test framework from coverage
lcov --remove coverage.info \
  '*/zephyr/*' \
  '*/modules/*' \
  '*/tests/*' \
  --output-file app_coverage.info

# Or extract only application source
lcov --extract coverage.info \
  '*/src/*' \
  --output-file app_coverage.info
```

### Combine Multiple Test Runs

```bash
# Merge coverage from unit tests and integration tests
lcov --add-tracefile unit_coverage.info \
     --add-tracefile integration_coverage.info \
     --output-file combined_coverage.info
```

## Coverage-Driven Test Prioritization

When coverage gaps are identified, prioritize test creation:

### Priority 1: Error Handling Paths (Safety Impact)
Functions returning error codes where the error branch was never taken. These paths handle hardware failures, resource exhaustion, and invalid input — bugs here cause silent corruption or crashes.

### Priority 2: State Machine Transitions (Logic Impact)
Untested state transitions, especially error-recovery and timeout transitions. Missing coverage here means untested edge cases in control flow.

### Priority 3: Boundary Conditions (Correctness Impact)
First/last elements, empty inputs, maximum sizes, zero-length buffers. Off-by-one errors live here.

### Priority 4: Platform-Specific Branches (Portability Impact)
Code behind `IS_ENABLED(CONFIG_*)` guards for different hardware. Test on native_sim where possible using mock configurations.

## Common CI Pitfalls

1. **Coverage only on native_sim**: gcov instrumentation only works with native_sim (and host builds). QEMU and hardware targets do not support gcov.

2. **Coverage inflation from test code**: By default, lcov includes test source files in metrics. Always filter: `lcov --extract coverage.info '*/src/*'`.

3. **Branch inflation from macros**: Zephyr's `LOG_ERR`, `IS_ENABLED`, and `CONTAINER_OF` macros generate hidden branches that inflate branch count. 100% branch coverage is unrealistic.

4. **Stale .gcda files**: Old coverage data from previous runs contaminates results. Use `--pristine` with twister or `lcov --zerocounters` before coverage runs.

5. **Coverage reset between binaries**: Each test binary starts fresh. lcov merges data when multiple binaries target the same source files.

6. **Container permissions**: CI containers may not have lcov/gcovr installed by default. Ensure the Zephyr CI image includes coverage tools.

#!/bin/bash
set -euo pipefail
# run-static-analysis.sh — Runs ruff check and mypy on graded Python files (background)
# Called by hooks.json as an async PostToolUse hook on Bash tool
# Requires: jq, ruff, mypy (warns if absent)
#
# Purpose: After any Bash command that reads Python source files, run ruff and
# mypy in the background to produce machine-verified static analysis evidence.
# Results are written to /tmp/grader-analysis/ for the grader to reference.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only run analysis when the bash command touched Python files
if ! echo "$COMMAND" | grep -qE '\.py'; then
  exit 0
fi

# Extract Python file paths from the command (best-effort heuristic)
PYTHON_FILES=$(echo "$COMMAND" | grep -oE '[^ ]+\.py' | head -20 || true)

# If no explicit files found, try to discover from common read commands
if [ -z "$PYTHON_FILES" ]; then
  # The command may be a directory scan — extract the directory
  TARGET_DIR=$(echo "$COMMAND" | grep -oE '[^ ]+' | grep -v '^-' | tail -1 || true)
  if [ -d "${TARGET_DIR:-}" ]; then
    PYTHON_FILES=$(find "$TARGET_DIR" -name '*.py' -not -path '*/__pycache__/*' -not -path '*/.venv/*' -not -path '*/node_modules/*' | head -50 || true)
  fi
fi

if [ -z "$PYTHON_FILES" ]; then
  exit 0
fi

# Ensure output directory exists
ANALYSIS_DIR="/tmp/grader-analysis"
mkdir -p "$ANALYSIS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${ANALYSIS_DIR}/static-analysis-${TIMESTAMP}.txt"

{
  echo "=== Static Analysis Report — $(date) ==="
  echo "Command that triggered this analysis: ${COMMAND}"
  echo ""

  # Run ruff check
  if command -v ruff &>/dev/null; then
    echo "--- ruff check ---"
    # shellcheck disable=SC2086
    ruff check --output-format=text $PYTHON_FILES 2>&1 || true
    echo ""
  else
    echo "WARNING: ruff not found — skipping ruff analysis. Install with: pip install ruff" >&2
  fi

  # Run mypy
  if command -v mypy &>/dev/null; then
    echo "--- mypy ---"
    # shellcheck disable=SC2086
    mypy --no-error-summary --show-column-numbers $PYTHON_FILES 2>&1 || true
    echo ""
  else
    echo "WARNING: mypy not found — skipping mypy analysis. Install with: pip install mypy" >&2
  fi

  echo "=== End of Static Analysis Report ==="
} > "$REPORT_FILE" 2>&1

# Write a summary pointer so the grader knows where to find the evidence
echo "Static analysis evidence written to: ${REPORT_FILE}" >&2

exit 0

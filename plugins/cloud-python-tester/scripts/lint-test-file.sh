#!/usr/bin/env bash
set -euo pipefail
# lint-test-file.sh — Runs ruff check and ruff format --check on written test files
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Requires: jq, ruff

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only lint Python files
if ! echo "$FILE_PATH" | grep -qE '\.py$'; then
  exit 0
fi

# Only lint test files and conftest.py
BASENAME=$(basename "$FILE_PATH")
if ! echo "$BASENAME" | grep -qE '^(test_.+|conftest)\.py$'; then
  exit 0
fi

# Verify ruff is available
if ! command -v ruff &>/dev/null; then
  echo "WARNING: ruff is not installed — skipping lint. Install with: pip install ruff" >&2
  exit 0
fi

# Verify the file actually exists (it may have been deleted)
if [[ ! -f "$FILE_PATH" ]]; then
  echo "WARNING: File not found, skipping lint: ${FILE_PATH}" >&2
  exit 0
fi

LINT_FAILED=0
FORMAT_FAILED=0

# Run ruff check (linting)
echo "--- ruff check: ${FILE_PATH} ---"
if ! ruff check "$FILE_PATH" 2>&1; then
  LINT_FAILED=1
fi

# Run ruff format --check (formatting, non-destructive check)
echo "--- ruff format --check: ${FILE_PATH} ---"
if ! ruff format --check "$FILE_PATH" 2>&1; then
  FORMAT_FAILED=1
fi

if [[ $LINT_FAILED -ne 0 || $FORMAT_FAILED -ne 0 ]]; then
  echo "" >&2
  echo "ruff found issues in ${FILE_PATH}." >&2
  if [[ $LINT_FAILED -ne 0 ]]; then
    echo "  - Lint errors detected by 'ruff check'. Fix the violations listed above." >&2
  fi
  if [[ $FORMAT_FAILED -ne 0 ]]; then
    echo "  - Formatting issues detected by 'ruff format --check'. Run 'ruff format ${FILE_PATH}' to auto-fix." >&2
  fi
  # Exit 2 to block and surface errors back to Claude
  exit 2
fi

echo "ruff: ${FILE_PATH} passed all checks."
exit 0

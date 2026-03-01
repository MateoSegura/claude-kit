#!/usr/bin/env bash
set -euo pipefail
# run-tests-async.sh — Runs pytest on the specific test file in the background
# Called by hooks.json as a PostToolUse async hook on Write|Edit tools (timeout: 300s)
# Requires: jq, pytest

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only run for Python test files and conftest.py
BASENAME=$(basename "$FILE_PATH")
if ! echo "$BASENAME" | grep -qE '^(test_.+|conftest)\.py$'; then
  exit 0
fi

# Verify pytest is available
if ! command -v pytest &>/dev/null; then
  echo "WARNING: pytest is not installed — skipping async test run. Install with: pip install pytest" >&2
  exit 0
fi

# Verify the file exists
if [[ ! -f "$FILE_PATH" ]]; then
  echo "WARNING: Test file not found, skipping: ${FILE_PATH}" >&2
  exit 0
fi

# Determine the working directory: climb to the project root
# (nearest directory containing pyproject.toml, setup.cfg, or pytest.ini)
FILE_DIR=$(dirname "$FILE_PATH")
PROJECT_ROOT="$FILE_DIR"

while [[ "$PROJECT_ROOT" != "/" ]]; do
  if [[ -f "$PROJECT_ROOT/pyproject.toml" || -f "$PROJECT_ROOT/setup.cfg" || -f "$PROJECT_ROOT/pytest.ini" ]]; then
    break
  fi
  PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
done

# Fall back to file's directory if no project root found
if [[ "$PROJECT_ROOT" == "/" ]]; then
  PROJECT_ROOT="$FILE_DIR"
fi

echo "--- pytest async run: ${FILE_PATH} (cwd: ${PROJECT_ROOT}) ---"

# Run pytest on the specific file with brief output
# --tb=short: concise tracebacks
# -q: quiet mode to reduce noise
# || true: async hooks should not fail the session; results are informational
(cd "$PROJECT_ROOT" && pytest "$FILE_PATH" --tb=short -q 2>&1) || true

exit 0

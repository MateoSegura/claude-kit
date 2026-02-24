#!/bin/bash
set -euo pipefail
# run-tests-async.sh — Runs pytest in the background after file changes
# Called by hooks.json as an async PostToolUse hook on Write|Edit tools
# Requires: jq, uv (for uv run pytest)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only trigger for Python source files — skip tests themselves to avoid infinite loop,
# skip YAML/Dockerfile/config changes that don't affect unit tests
if ! echo "$FILE_PATH" | grep -qE '\.py$'; then
  exit 0
fi

# Find the project root (directory containing pyproject.toml or setup.py or uv.lock)
PROJECT_ROOT=""
SEARCH_DIR=$(dirname "$FILE_PATH")
while [[ "$SEARCH_DIR" != "/" ]]; do
  if [[ -f "$SEARCH_DIR/pyproject.toml" ]] || [[ -f "$SEARCH_DIR/uv.lock" ]] || [[ -f "$SEARCH_DIR/setup.py" ]]; then
    PROJECT_ROOT="$SEARCH_DIR"
    break
  fi
  SEARCH_DIR=$(dirname "$SEARCH_DIR")
done

if [[ -z "$PROJECT_ROOT" ]]; then
  # Fall back to the directory of the modified file
  PROJECT_ROOT=$(dirname "$FILE_PATH")
fi

LOG_FILE="/tmp/pytest-async-$(date +%s).log"

echo "Running pytest in background for project at $PROJECT_ROOT (log: $LOG_FILE)" >&2

# Use uv run pytest if uv is available, fall back to python -m pytest
if command -v uv &>/dev/null; then
  (
    cd "$PROJECT_ROOT"
    uv run pytest \
      --tb=short \
      -q \
      --no-header \
      2>&1
  ) > "$LOG_FILE" 2>&1 &
else
  (
    cd "$PROJECT_ROOT"
    python3 -m pytest \
      --tb=short \
      -q \
      --no-header \
      2>&1
  ) > "$LOG_FILE" 2>&1 &
fi

echo "Test run started in background (PID $!). Results will be written to $LOG_FILE" >&2

exit 0

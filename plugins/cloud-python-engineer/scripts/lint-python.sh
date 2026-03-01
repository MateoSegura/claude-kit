#!/usr/bin/env bash
set -euo pipefail
# lint-python.sh — Runs ruff, YAML validation, and hadolint on modified files
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Requires: jq, ruff (for Python), python3 (for YAML), hadolint (optional for Dockerfile)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

EXT="${FILE_PATH##*.}"
BASENAME=$(basename "$FILE_PATH")
ERRORS=0

# --- Python files: ruff check + ruff format --check ---
if [[ "$EXT" == "py" ]]; then
  if command -v ruff &>/dev/null; then
    echo "Running ruff check on $FILE_PATH..." >&2

    if ! ruff check "$FILE_PATH" 2>&1; then
      ERRORS=$((ERRORS + 1))
    fi

    if ! ruff format --check "$FILE_PATH" 2>&1; then
      echo "ruff format: file is not formatted. Run 'ruff format $FILE_PATH' to fix." >&2
      ERRORS=$((ERRORS + 1))
    fi
  else
    echo "WARNING: ruff not found. Install with 'uv tool install ruff' or 'pip install ruff'." >&2
  fi
fi

# --- YAML files: validate syntax with Python ---
if [[ "$EXT" == "yml" || "$EXT" == "yaml" ]]; then
  if command -v python3 &>/dev/null; then
    if ! python3 -c "import sys, yaml; yaml.safe_load(open('$FILE_PATH'))" 2>&1; then
      echo "YAML syntax error in $FILE_PATH" >&2
      ERRORS=$((ERRORS + 1))
    fi
  else
    echo "WARNING: python3 not found, skipping YAML validation." >&2
  fi
fi

# --- Dockerfile: hadolint if available (non-blocking if missing) ---
if [[ "$BASENAME" == "Dockerfile" || "$BASENAME" == Dockerfile.* || "$EXT" == "dockerfile" ]]; then
  if command -v hadolint &>/dev/null; then
    if ! hadolint "$FILE_PATH" 2>&1; then
      ERRORS=$((ERRORS + 1))
    fi
  else
    echo "INFO: hadolint not installed. Skipping Dockerfile lint. Install with: brew install hadolint / apt install hadolint" >&2
  fi
fi

if [[ "$ERRORS" -gt 0 ]]; then
  echo "Linting found $ERRORS issue(s) in $FILE_PATH. Fix the reported problems before proceeding." >&2
  exit 2
fi

exit 0

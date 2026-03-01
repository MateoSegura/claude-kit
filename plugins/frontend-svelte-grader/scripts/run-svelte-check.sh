#!/bin/bash
set -euo pipefail
# run-svelte-check.sh — Runs svelte-check and tsc --noEmit on the submission directory
# Called by hooks.json as an async PostToolUse hook on Bash tool
# Runs in the background after reviewers execute analysis commands, providing additional diagnostics
# Results are written to /tmp for reviewer agents to read if needed
# Requires: jq, svelte-check (npx), tsc (npx)

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Attempt to determine the submission directory from the command context
# Look for common patterns: paths passed to grep, find, cat, etc.
SUBMISSION_DIR=""

# Try to extract a directory path from the command
CANDIDATE=$(echo "$COMMAND" | grep -oE '[^ ]+/(src|routes|components|lib)[^ ]*' | head -1 | xargs dirname 2>/dev/null || true)
if [[ -n "$CANDIDATE" ]] && [[ -d "$CANDIDATE" ]]; then
  # Walk up to find package.json (project root)
  CHECK_DIR="$CANDIDATE"
  while [[ "$CHECK_DIR" != "/" ]]; do
    if [[ -f "$CHECK_DIR/package.json" ]]; then
      SUBMISSION_DIR="$CHECK_DIR"
      break
    fi
    CHECK_DIR=$(dirname "$CHECK_DIR")
  done
fi

# Fall back to current working directory if we found a package.json there
if [[ -z "$SUBMISSION_DIR" ]] && [[ -f "$(pwd)/package.json" ]]; then
  SUBMISSION_DIR="$(pwd)"
fi

# Nothing to check if we cannot locate a project root
if [[ -z "$SUBMISSION_DIR" ]]; then
  exit 0
fi

# Output file for diagnostics (readable by reviewer agents)
DIAGNOSTICS_FILE="${TMPDIR:-/tmp}/svelte-check-diagnostics-$$.txt"

{
  echo "=== svelte-check diagnostics ==="
  echo "Submission directory: $SUBMISSION_DIR"
  echo "Run time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""

  # Run svelte-check if available
  if command -v svelte-check &>/dev/null; then
    echo "--- svelte-check output ---"
    svelte-check --workspace "$SUBMISSION_DIR" --output human 2>&1 || true
  elif [[ -f "$SUBMISSION_DIR/node_modules/.bin/svelte-check" ]]; then
    echo "--- svelte-check output ---"
    "$SUBMISSION_DIR/node_modules/.bin/svelte-check" --output human 2>&1 || true
  else
    echo "--- svelte-check: not found (install with: npm install -D svelte-check) ---"
  fi

  echo ""

  # Run tsc --noEmit if tsconfig.json exists
  if [[ -f "$SUBMISSION_DIR/tsconfig.json" ]]; then
    echo "--- TypeScript diagnostics (tsc --noEmit) ---"
    if command -v tsc &>/dev/null; then
      tsc --noEmit --project "$SUBMISSION_DIR/tsconfig.json" 2>&1 || true
    elif [[ -f "$SUBMISSION_DIR/node_modules/.bin/tsc" ]]; then
      "$SUBMISSION_DIR/node_modules/.bin/tsc" --noEmit --project "$SUBMISSION_DIR/tsconfig.json" 2>&1 || true
    else
      echo "tsc: not found in PATH or node_modules. TypeScript diagnostics skipped."
    fi
  else
    echo "--- TypeScript diagnostics: no tsconfig.json found at $SUBMISSION_DIR ---"
  fi

} > "$DIAGNOSTICS_FILE" 2>&1

# Write a stable symlink so reviewer agents can find the latest diagnostics
LATEST_LINK="${TMPDIR:-/tmp}/svelte-check-diagnostics-latest.txt"
ln -sf "$DIAGNOSTICS_FILE" "$LATEST_LINK" 2>/dev/null || true

exit 0

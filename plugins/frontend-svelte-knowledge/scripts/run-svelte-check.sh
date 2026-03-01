#!/usr/bin/env bash
set -euo pipefail
# run-svelte-check.sh — Runs svelte-check project-wide in the background
# Called by hooks.json as a PostToolUse async hook on Bash tool (async: true)
# Requires: jq
# Non-blocking: always exits 0. Runs asynchronously — results are informational.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only trigger on Svelte, TypeScript, and JavaScript files
if [ -n "$FILE_PATH" ]; then
  if ! echo "$FILE_PATH" | grep -qE '\.(svelte|ts|tsx|js|mjs|cjs)$'; then
    exit 0
  fi
fi

# Find the project root by looking for svelte.config.js or package.json
PROJECT_ROOT=""
SEARCH_DIR="${FILE_PATH:+$(dirname "$FILE_PATH")}"
SEARCH_DIR="${SEARCH_DIR:-$PWD}"

DIR="$SEARCH_DIR"
while [ "$DIR" != "/" ]; do
  if [ -f "$DIR/svelte.config.js" ] || [ -f "$DIR/svelte.config.ts" ]; then
    PROJECT_ROOT="$DIR"
    break
  fi
  if [ -f "$DIR/package.json" ]; then
    PROJECT_ROOT="$DIR"
    break
  fi
  DIR="$(dirname "$DIR")"
done

if [ -z "$PROJECT_ROOT" ]; then
  # Try current working directory as fallback
  if [ -f "$PWD/svelte.config.js" ] || [ -f "$PWD/package.json" ]; then
    PROJECT_ROOT="$PWD"
  else
    # No project root found — skip
    exit 0
  fi
fi

# Run svelte-check project-wide
SVELTE_CHECK=""
if command -v svelte-check &>/dev/null; then
  SVELTE_CHECK="svelte-check"
elif [ -f "$PROJECT_ROOT/node_modules/.bin/svelte-check" ]; then
  SVELTE_CHECK="$PROJECT_ROOT/node_modules/.bin/svelte-check"
fi

if [ -z "$SVELTE_CHECK" ]; then
  echo "svelte-check not found. Install with: pnpm add -D svelte-check" >&2
  exit 0
fi

echo "--- svelte-check (project-wide): $PROJECT_ROOT ---"
"$SVELTE_CHECK" --workspace "$PROJECT_ROOT" --output human 2>&1 || true

# Always exit 0 — async type checking is informational, never blocking
exit 0

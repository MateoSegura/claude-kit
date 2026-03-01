#!/usr/bin/env bash
set -euo pipefail
# lint-svelte-file.sh — Runs svelte-check and eslint on the modified file
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Requires: jq
# Non-blocking: always exits 0. Diagnostics are printed as informational output.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only lint Svelte, TypeScript, and JavaScript files
if ! echo "$FILE_PATH" | grep -qE '\.(svelte|ts|tsx|js|mjs|cjs)$'; then
  exit 0
fi

# Find the project root by looking for svelte.config.js or package.json
PROJECT_ROOT=""
DIR="$(dirname "$FILE_PATH")"
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
  # No project root found — skip linting
  exit 0
fi

# Run eslint on the file if eslint is available and configured
if [ -f "$PROJECT_ROOT/.eslintrc.js" ] || [ -f "$PROJECT_ROOT/.eslintrc.cjs" ] || [ -f "$PROJECT_ROOT/eslint.config.js" ] || [ -f "$PROJECT_ROOT/eslint.config.mjs" ]; then
  if command -v eslint &>/dev/null; then
    echo "--- eslint: $FILE_PATH ---"
    eslint --no-eslintrc --no-ignore "$FILE_PATH" 2>&1 || true
  elif [ -f "$PROJECT_ROOT/node_modules/.bin/eslint" ]; then
    echo "--- eslint: $FILE_PATH ---"
    "$PROJECT_ROOT/node_modules/.bin/eslint" "$FILE_PATH" 2>&1 || true
  fi
fi

# Run svelte-check on .svelte files for type and accessibility errors
if echo "$FILE_PATH" | grep -qE '\.svelte$'; then
  if command -v svelte-check &>/dev/null; then
    echo "--- svelte-check (single file): $FILE_PATH ---"
    # svelte-check operates on a project, but we limit output to the specific file
    svelte-check --workspace "$PROJECT_ROOT" --output human-verbose 2>&1 | grep -A5 "$(basename "$FILE_PATH")" || true
  elif [ -f "$PROJECT_ROOT/node_modules/.bin/svelte-check" ]; then
    echo "--- svelte-check (single file): $FILE_PATH ---"
    "$PROJECT_ROOT/node_modules/.bin/svelte-check" --workspace "$PROJECT_ROOT" --output human-verbose 2>&1 | grep -A5 "$(basename "$FILE_PATH")" || true
  fi
fi

# Always exit 0 — linting is informational, never blocking
exit 0

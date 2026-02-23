#!/bin/bash
set -euo pipefail
# validate-test-file.sh — Checks test file naming conventions after Write|Edit
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Validates that written files follow .test.ts or .spec.ts naming, or are recognized
# test config files. Provides feedback only — always exits 0 (non-blocking).
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Recognized test infrastructure files that are always allowed
if echo "$FILE_PATH" | grep -qE '(vitest\.config\.(ts|js)|playwright\.config\.(ts|js)|vitest\.setup\.(ts|js)|test-utils\.(ts|js)|fixtures/.*\.(ts|js)$|__mocks__/.*\.(ts|js)$)'; then
  echo "INFO: Test config/infrastructure file recognized: $FILE_PATH" >&2
  exit 0
fi

# Check for proper test file naming convention
if echo "$FILE_PATH" | grep -qE '\.(test|spec)\.(ts|js)$'; then
  # Good naming — now check for .svelte.test.ts pattern (component tests)
  if echo "$FILE_PATH" | grep -qE '\.svelte\.(test|spec)\.(ts|js)$'; then
    echo "INFO: Svelte component test file OK: $FILE_PATH" >&2
    exit 0
  fi
  echo "INFO: Test file naming convention OK: $FILE_PATH" >&2
  exit 0
fi

# Check for Playwright E2E test files (conventionally .ts in tests/ or e2e/ directory)
if echo "$FILE_PATH" | grep -qE '(tests/|e2e/|playwright/).*\.ts$'; then
  echo "INFO: Playwright E2E test file recognized: $FILE_PATH" >&2
  exit 0
fi

# File does not match test naming convention — warn but do not block
echo "WARNING: File does not follow test naming conventions: $FILE_PATH" >&2
echo "  Expected naming patterns:" >&2
echo "    Unit/component tests:  <name>.test.ts  or  <name>.spec.ts" >&2
echo "    Svelte component tests: <name>.svelte.test.ts" >&2
echo "    E2E tests:             tests/<name>.ts  or  e2e/<name>.ts" >&2
echo "    Config files:          vitest.config.ts, playwright.config.ts" >&2
echo "  If this is intentional (fixture, helper, mock), this warning can be ignored." >&2

# Always exit 0 — this hook provides feedback only, it does not block
exit 0

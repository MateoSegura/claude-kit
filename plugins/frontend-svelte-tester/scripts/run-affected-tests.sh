#!/bin/bash
set -euo pipefail
# run-affected-tests.sh — Runs tests related to the just-written file in the background
# Called by hooks.json as an async PostToolUse hook on Write|Edit tools (timeout: 180s)
# Determines which test command to run based on the file type, then executes it.
# Always exits 0 — failures are surfaced as output, not as hook failures.
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  echo "INFO: No file path found in hook input, skipping test run." >&2
  exit 0
fi

echo "INFO: Running affected tests for: $FILE_PATH"

# Determine which test runner to invoke based on file location and name
if echo "$FILE_PATH" | grep -qE '(tests/|e2e/|playwright/).*\.ts$'; then
  # Playwright E2E test
  echo "INFO: Detected Playwright E2E test. Running: npx playwright test $FILE_PATH"
  if command -v npx &> /dev/null; then
    npx playwright test "$FILE_PATH" --reporter=line 2>&1 || {
      echo "WARN: Playwright test run completed with failures. Review output above." >&2
    }
  else
    echo "WARN: npx not found — cannot run Playwright tests. Is Node.js installed?" >&2
  fi

elif echo "$FILE_PATH" | grep -qE '\.(test|spec)\.(ts|js)$'; then
  # Vitest unit or component test
  echo "INFO: Detected Vitest test file. Running: npx vitest run $FILE_PATH"
  if command -v npx &> /dev/null; then
    npx vitest run "$FILE_PATH" --reporter=verbose 2>&1 || {
      echo "WARN: Vitest run completed with failures. Review output above." >&2
    }
  else
    echo "WARN: npx not found — cannot run Vitest tests. Is Node.js installed?" >&2
  fi

elif echo "$FILE_PATH" | grep -qE 'vitest\.config\.(ts|js)$'; then
  # Vitest config changed — run the full suite to check nothing broke
  echo "INFO: vitest.config changed. Running full test suite: npx vitest run"
  if command -v npx &> /dev/null; then
    npx vitest run --reporter=verbose 2>&1 || {
      echo "WARN: Full Vitest suite completed with failures after config change. Review output above." >&2
    }
  else
    echo "WARN: npx not found — cannot run Vitest. Is Node.js installed?" >&2
  fi

elif echo "$FILE_PATH" | grep -qE 'playwright\.config\.(ts|js)$'; then
  # Playwright config changed — run a smoke test
  echo "INFO: playwright.config changed. Running smoke test: npx playwright test --grep @smoke 2>&1 || npx playwright test --shard=1/4"
  if command -v npx &> /dev/null; then
    npx playwright test --grep "@smoke" --reporter=line 2>&1 || \
    npx playwright test --shard=1/4 --reporter=line 2>&1 || {
      echo "WARN: Playwright smoke test completed with failures. Review output above." >&2
    }
  else
    echo "WARN: npx not found — cannot run Playwright. Is Node.js installed?" >&2
  fi

else
  echo "INFO: File $FILE_PATH is not a recognized test file type. Skipping test run."
fi

# Always exit 0 — this is an async informational hook, not a blocking gate
exit 0

#!/bin/bash
set -euo pipefail
# validate-test-file.sh — Validates test file structure after Write/Edit
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Checks for ZTEST_SUITE, proper includes, and testcase.yaml presence
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# For Edit tool, content might be in new_string
if [[ -z "$CONTENT" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
fi

# Only validate C test source files
if ! echo "$FILE_PATH" | grep -qE '\.c$'; then
  exit 0
fi

# Only validate files in test directories
if ! echo "$FILE_PATH" | grep -qE '(tests/|test_)'; then
  exit 0
fi

# Check for ZTEST_SUITE macro
if ! echo "$CONTENT" | grep -qE 'ZTEST_SUITE\s*\('; then
  # It might be a helper file, not the main test file -- only warn if it has ZTEST
  if echo "$CONTENT" | grep -qE 'ZTEST\s*\(|ZTEST_F\s*\('; then
    echo "WARNING: Test file contains ZTEST/ZTEST_F macros but no ZTEST_SUITE registration. Every test suite needs ZTEST_SUITE() to be discoverable by twister." >&2
  fi
fi

# Check for ztest.h include
if echo "$CONTENT" | grep -qE 'ZTEST\s*\(|ZTEST_F\s*\(|ZTEST_SUITE\s*\(|zassert_'; then
  if ! echo "$CONTENT" | grep -qE '#include\s+<zephyr/ztest\.h>'; then
    echo "WARNING: Test file uses ztest macros but does not include <zephyr/ztest.h>." >&2
  fi
fi

# Check for FFF include if FFF macros are used
if echo "$CONTENT" | grep -qE 'FAKE_VALUE_FUNC\s*\(|FAKE_VOID_FUNC\s*\(|DEFINE_FFF_GLOBALS|RESET_FAKE\s*\('; then
  if ! echo "$CONTENT" | grep -qE '#include\s+<zephyr/fff\.h>'; then
    echo "WARNING: Test file uses FFF macros but does not include <zephyr/fff.h>." >&2
  fi
fi

# Check for testcase.yaml in the test directory
TEST_DIR=$(dirname "$FILE_PATH")
# Walk up to find testcase.yaml (might be one level up from src/)
TESTCASE_FOUND=false
CHECK_DIR="$TEST_DIR"
for i in 1 2 3; do
  if [[ -f "$CHECK_DIR/testcase.yaml" ]]; then
    TESTCASE_FOUND=true
    break
  fi
  CHECK_DIR=$(dirname "$CHECK_DIR")
done

if [[ "$TESTCASE_FOUND" == "false" ]]; then
  if echo "$CONTENT" | grep -qE 'ZTEST_SUITE\s*\('; then
    echo "ADVISORY: No testcase.yaml found near $FILE_PATH. Every test suite needs a testcase.yaml to be discoverable by twister. Create one with at minimum: platform_allow, tags, and test identifier." >&2
  fi
fi

# Check for bare assertions (no message parameter)
# Look for patterns like zassert_equal(a, b); without a trailing format string
if echo "$CONTENT" | grep -qE 'zassert_(equal|true|false|not_null|is_null|ok)\s*\([^,]+,\s*[^,)]+\s*\)'; then
  echo "ADVISORY: Some zassert_* calls appear to be missing diagnostic messages. Add a format string: zassert_equal(a, b, \"descriptive message: got %d\", a)" >&2
fi

exit 0

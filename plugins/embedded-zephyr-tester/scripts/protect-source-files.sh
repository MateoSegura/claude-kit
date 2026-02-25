#!/bin/bash
set -euo pipefail
# protect-source-files.sh — Warns when tester modifies non-test source files
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Tester agents should only create/modify test files, not production source
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, skip
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Allow all files in test directories
if echo "$FILE_PATH" | grep -qE '(tests/|test_|_test\.|testcase\.yaml|mock_|/mocks/)'; then
  exit 0
fi

# Allow configuration files commonly created for tests
if echo "$FILE_PATH" | grep -qE '(prj\.conf|CMakeLists\.txt|\.overlay|\.conf|Kconfig|quarantine\.yaml)'; then
  exit 0
fi

# Warn if modifying source files (src/ directory)
if echo "$FILE_PATH" | grep -qE '/src/'; then
  echo "WARNING: Tester agent is modifying a production source file: $FILE_PATH" >&2
  echo "The tester plugin should only create and modify test files (tests/, mock_, testcase.yaml)." >&2
  echo "If this is intentional (e.g., adding a test hook or fixing a bug found during testing), proceed with caution." >&2
fi

# Warn if modifying header files outside test directories
if echo "$FILE_PATH" | grep -qE '\.h$'; then
  if ! echo "$FILE_PATH" | grep -qE '(tests/|mock_|/mocks/)'; then
    echo "WARNING: Tester agent is modifying a header file outside test directories: $FILE_PATH" >&2
    echo "Consider whether this change belongs in the tester context or should be done by the engineer plugin." >&2
  fi
fi

# Do not block -- just warn
exit 0

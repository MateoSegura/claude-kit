#!/bin/bash
set -euo pipefail
# run-build-async.sh — Captures build results and triggers tests if applicable
# Called by hooks.json as a PostToolUse async hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_result.exit_code // empty')
OUTPUT=$(echo "$INPUT" | jq -r '.tool_result.output // empty')

# Only process west build commands
if ! echo "$COMMAND" | grep -qE 'west\s+build'; then
  exit 0
fi

# Extract build directory
BUILD_DIR=$(echo "$COMMAND" | sed -n 's/.*-d\s\+\([^[:space:]]\+\).*/\1/p')
if [[ -z "$BUILD_DIR" ]]; then
  BUILD_DIR="build"
fi

# Check if build succeeded
if [[ "$EXIT_CODE" == "0" ]]; then
  echo "Build succeeded in $BUILD_DIR" >&2

  # Check for test directory with testcase.yaml
  if [[ -f "tests/testcase.yaml" ]] || [[ -f "testcase.yaml" ]]; then
    echo "ADVISORY: Tests detected. Consider running twister to validate: twister -T . -p native_sim" >&2
  fi

  # Check if sysbuild was used and both images were produced
  if [[ -d "$BUILD_DIR/mcuboot" ]] && [[ -f "$BUILD_DIR/zephyr/zephyr.elf" ]]; then
    echo "Sysbuild successful: Both app and MCUboot images produced." >&2
  fi
else
  echo "Build failed in $BUILD_DIR. Review error output." >&2
fi

exit 0

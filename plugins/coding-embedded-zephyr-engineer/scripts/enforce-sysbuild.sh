#!/bin/bash
set -euo pipefail
# enforce-sysbuild.sh — Enforces sysbuild usage for MCUboot integration
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check if this is a west build command
if ! echo "$COMMAND" | grep -qE 'west\s+build'; then
  exit 0
fi

# Allow if --sysbuild flag is present
if echo "$COMMAND" | grep -qE '--sysbuild'; then
  exit 0
fi

# Check if sysbuild.conf exists in current directory or specified build directory
BUILD_DIR=$(echo "$COMMAND" | sed -n 's/.*-d\s\+\([^[:space:]]\+\).*/\1/p')
if [[ -z "$BUILD_DIR" ]]; then
  BUILD_DIR="build"
fi

# Check for sysbuild.conf in project root or build directory parent
if [[ -f "sysbuild.conf" ]] || [[ -f "sysbuild/sysbuild.conf" ]]; then
  exit 0
fi

# Check if this is a test build (twister, samples, tests directory)
if echo "$COMMAND" | grep -qE '(twister|samples/|tests/|native_sim|native_posix)'; then
  exit 0
fi

# Warn about missing sysbuild
echo "WARNING: west build command without --sysbuild flag and no sysbuild.conf found. For production firmware, consider enabling sysbuild to integrate MCUboot from day one. Add --sysbuild flag or create sysbuild.conf. Legitimate test builds can ignore this warning." >&2

exit 0

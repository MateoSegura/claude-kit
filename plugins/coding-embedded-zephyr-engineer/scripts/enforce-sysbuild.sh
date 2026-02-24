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

# Check if this is a test/analysis build (twister, samples, tests, native targets, /tmp/ builds)
if echo "$COMMAND" | grep -qE '(twister|samples/|tests/|native_sim|native_posix|/tmp/)'; then
  exit 0
fi

# Allow --pristine or --dry-run builds (analysis/clean builds)
if echo "$COMMAND" | grep -qE '(--pristine|--dry-run)'; then
  exit 0
fi

# Block non-sysbuild production builds
echo "BLOCKED: west build without --sysbuild flag and no sysbuild.conf found. Production firmware must use sysbuild to integrate MCUboot from day one. Add --sysbuild flag or create sysbuild.conf. If this is a test build, use twister or target native_sim/native_posix." >&2

exit 2

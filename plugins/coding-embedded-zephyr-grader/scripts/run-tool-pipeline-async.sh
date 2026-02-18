#!/bin/bash
set -euo pipefail

# Kick off static analysis tool pipeline after successful west build
# Requires: jq

# Read the tool use event JSON from stdin
INPUT=$(cat)

# Extract the Bash command and exit code
COMMAND=$(echo "$INPUT" | jq -r '.arguments.command // ""')
EXIT_CODE=$(echo "$INPUT" | jq -r '.output.exit_code // 1')

# Only proceed if the command was a west build and it succeeded
if ! echo "$COMMAND" | grep -qE '^west build'; then
    exit 0
fi

if [ "$EXIT_CODE" -ne 0 ]; then
    exit 0
fi

# Extract build directory from the command
# Look for -b <dir> or --build-dir <dir>
BUILD_DIR=$(echo "$COMMAND" | grep -oP '(?:-b|--build-dir)\s+\S+' | awk '{print $2}' || echo "build")

# If build directory doesn't exist, exit
if [ ! -d "$BUILD_DIR" ]; then
    exit 0
fi

# Launch tool pipeline in background
# Run cppcheck, clang-tidy, lizard, checkpatch in parallel

echo "Launching static analysis tool pipeline for build in $BUILD_DIR..." >&2

# Create reports directory
REPORTS_DIR="${BUILD_DIR}/analysis-reports"
mkdir -p "$REPORTS_DIR"

# Launch each tool in background
# cppcheck
if command -v cppcheck &> /dev/null; then
    (cppcheck --enable=all --xml --xml-version=2 "$BUILD_DIR" 2> "$REPORTS_DIR/cppcheck.xml" || true) &
fi

# clang-tidy (if compilation database exists)
if command -v clang-tidy &> /dev/null && [ -f "$BUILD_DIR/compile_commands.json" ]; then
    (cd "$BUILD_DIR" && clang-tidy -p . $(find .. -name "*.c") > "$REPORTS_DIR/clang-tidy.txt" 2>&1 || true) &
fi

# lizard (complexity analysis)
if command -v lizard &> /dev/null; then
    (lizard -l c -o "$REPORTS_DIR/lizard.html" "$BUILD_DIR/../" 2>&1 || true) &
fi

# checkpatch (if ZEPHYR_BASE is set)
if [ -n "${ZEPHYR_BASE:-}" ] && [ -f "$ZEPHYR_BASE/scripts/checkpatch.pl" ]; then
    (find "$BUILD_DIR/../src" -name "*.c" -o -name "*.h" | xargs -I {} "$ZEPHYR_BASE/scripts/checkpatch.pl" --no-tree --file {} > "$REPORTS_DIR/checkpatch.txt" 2>&1 || true) &
fi

echo "Tool pipeline launched. Reports will be written to $REPORTS_DIR/" >&2

# Always succeed (this is informational, not blocking)
exit 0

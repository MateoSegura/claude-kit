#!/bin/bash
set -euo pipefail

# Validate that a directory has the minimum required structure for a Zephyr project
# Usage: validate-submission-structure.sh <directory>
# Exit 0 if valid, exit 1 with error message if not

SUBMISSION_DIR="${1:-}"

if [ -z "$SUBMISSION_DIR" ]; then
    echo "ERROR: No directory provided" >&2
    echo "Usage: validate-submission-structure.sh <directory>" >&2
    exit 1
fi

if [ ! -d "$SUBMISSION_DIR" ]; then
    echo "ERROR: Directory does not exist: $SUBMISSION_DIR" >&2
    exit 1
fi

ERRORS=()

# Check for CMakeLists.txt
if [ ! -f "$SUBMISSION_DIR/CMakeLists.txt" ]; then
    ERRORS+=("Missing CMakeLists.txt")
fi

# Check for prj.conf
if [ ! -f "$SUBMISSION_DIR/prj.conf" ]; then
    ERRORS+=("Missing prj.conf")
fi

# Check for src/ directory
if [ ! -d "$SUBMISSION_DIR/src" ]; then
    ERRORS+=("Missing src/ directory")
else
    # Check for at least one .c file in src/
    C_FILES=$(find "$SUBMISSION_DIR/src" -maxdepth 1 -name "*.c" 2>/dev/null | wc -l)
    if [ "$C_FILES" -eq 0 ]; then
        ERRORS+=("No .c files found in src/ directory")
    fi
fi

# Report results
if [ ${#ERRORS[@]} -eq 0 ]; then
    echo "Submission structure validation PASSED: $SUBMISSION_DIR" >&2
    exit 0
else
    echo "ERROR: Invalid submission structure in $SUBMISSION_DIR" >&2
    echo "" >&2
    echo "Missing required components:" >&2
    for ERROR in "${ERRORS[@]}"; do
        echo "  - $ERROR" >&2
    done
    echo "" >&2
    echo "A valid Zephyr submission must contain:" >&2
    echo "  - CMakeLists.txt (build configuration)" >&2
    echo "  - prj.conf (project configuration)" >&2
    echo "  - src/ directory with at least one .c file" >&2
    exit 1
fi

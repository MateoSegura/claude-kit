#!/bin/bash
set -euo pipefail

# Check for required tools and warn about missing dependencies
# Never fails - just provides warnings with installation instructions

echo "Checking grading environment for required tools..." >&2

MISSING_TOOLS=()

# Check for west
if ! command -v west &> /dev/null; then
    MISSING_TOOLS+=("west")
    echo "WARNING: west not found" >&2
    echo "  Install: pip install west" >&2
fi

# Check for cppcheck
if ! command -v cppcheck &> /dev/null; then
    MISSING_TOOLS+=("cppcheck")
    echo "WARNING: cppcheck not found" >&2
    echo "  Install: apt install cppcheck / brew install cppcheck" >&2
fi

# Check for clang-tidy
if ! command -v clang-tidy &> /dev/null; then
    MISSING_TOOLS+=("clang-tidy")
    echo "WARNING: clang-tidy not found" >&2
    echo "  Install: apt install clang-tidy / brew install llvm" >&2
fi

# Check for lizard
if ! command -v lizard &> /dev/null; then
    MISSING_TOOLS+=("lizard")
    echo "WARNING: lizard not found" >&2
    echo "  Install: pip install lizard" >&2
fi

# Check for cloc
if ! command -v cloc &> /dev/null; then
    MISSING_TOOLS+=("cloc")
    echo "WARNING: cloc not found" >&2
    echo "  Install: apt install cloc / brew install cloc" >&2
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    MISSING_TOOLS+=("jq")
    echo "WARNING: jq not found (CRITICAL - required for hook scripts)" >&2
    echo "  Install: apt install jq / brew install jq" >&2
fi

# Check for arm-zephyr-eabi-size
if ! command -v arm-zephyr-eabi-size &> /dev/null; then
    MISSING_TOOLS+=("arm-zephyr-eabi-size")
    echo "WARNING: arm-zephyr-eabi-size not found" >&2
    echo "  Install Zephyr SDK: https://docs.zephyrproject.org/latest/develop/getting_started/" >&2
fi

# Check for bloaty
if ! command -v bloaty &> /dev/null; then
    MISSING_TOOLS+=("bloaty")
    echo "WARNING: bloaty not found" >&2
    echo "  Install: apt install bloaty / brew install bloaty" >&2
fi

# Check for checkpatch.pl via ZEPHYR_BASE
if [ -z "${ZEPHYR_BASE:-}" ]; then
    echo "WARNING: ZEPHYR_BASE not set - checkpatch.pl unavailable" >&2
    echo "  Set ZEPHYR_BASE to your Zephyr installation directory" >&2
elif [ ! -f "$ZEPHYR_BASE/scripts/checkpatch.pl" ]; then
    echo "WARNING: checkpatch.pl not found at \$ZEPHYR_BASE/scripts/checkpatch.pl" >&2
fi

# Summary
if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
    echo "Environment check PASSED: All tools available" >&2
else
    echo "" >&2
    echo "Environment check completed with ${#MISSING_TOOLS[@]} missing tool(s)" >&2
    echo "Missing: ${MISSING_TOOLS[*]}" >&2
    echo "" >&2
    echo "Grading will continue, but some analysis features may be unavailable." >&2
fi

# Always succeed
exit 0

#!/bin/bash
set -euo pipefail

# Block dangerous commands that could modify submissions or flash hardware
# Requires: jq

# Read the tool use event JSON from stdin
INPUT=$(cat)

# Extract the command being executed
COMMAND=$(echo "$INPUT" | jq -r '.arguments.command // ""')

# If no command found, allow (shouldn't happen for Bash tool)
if [ -z "$COMMAND" ]; then
    exit 0
fi

# Block patterns for dangerous operations
BLOCKED_PATTERNS=(
    "rm -rf.*submissions"
    "rm -rf.*submission"
    "west flash"
    "west debug"
    "sudo "
    "chmod 777"
    "git push"
    "git commit.*--amend"
    "git reset --hard"
)

# Check if command matches any blocked pattern
for PATTERN in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$PATTERN"; then
        echo "ERROR: Blocked dangerous command: $COMMAND" >&2
        echo "Grading agents must NEVER:" >&2
        echo "  - Modify submission files (read-only assessment)" >&2
        echo "  - Flash hardware (west flash/debug)" >&2
        echo "  - Use sudo or modify permissions" >&2
        echo "  - Push to git remotes" >&2
        echo "" >&2
        echo "You may only READ submission files and WRITE report outputs." >&2
        exit 2
    fi
done

# Additional check: block writes to submission directories
# Look for output redirects or file writes into submission paths
if echo "$COMMAND" | grep -qE '(>|tee|cp|mv|write).*/(submission|submissions)/'; then
    echo "ERROR: Blocked attempt to write to submission directory" >&2
    echo "Submission files are READ-ONLY. You may only write to report output directories." >&2
    exit 2
fi

# All checks passed
exit 0

#!/bin/bash
set -euo pipefail

# Block dangerous Bash commands that could modify device or repository state.
# Allow read-only analysis tools.
# Requires: jq
#
# Input: JSON on stdin with tool_input.command field containing the Bash command.
# Exit 2 to block, exit 0 to allow.

# Read the command from stdin JSON
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
    # No command found in input — allow (may be a non-standard invocation)
    exit 0
fi

# Blocked patterns — destructive or state-modifying commands
BLOCKED_PATTERNS=(
    'rm -rf'
    'rm -fr'
    'git reset --hard'
    'git push --force'
    'git push -f'
    'git clean -f'
    'west flash'
    'west build --pristine'
    'nrfjprog --program'
    'nrfjprog --eraseall'
    'nrfjprog --recover'
    'nrfjprog --reset'
    'esptool write_flash'
    'esptool erase_flash'
    'esptool\.py write_flash'
    'esptool\.py erase_flash'
    'dd if='
    'mkfs\.'
    'openocd.*flash write'
    'st-flash write'
    'st-flash erase'
    'JLinkExe.*erase'
    'JLinkExe.*loadbin'
    'JLinkExe.*loadfile'
    'pyocd flash'
    'pyocd erase'
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        echo "BLOCKED: Command matches dangerous pattern '$pattern'. The debugger is read-only and cannot execute commands that modify device state, erase flash, or alter the repository. Command: $COMMAND" >&2
        exit 2
    fi
done

# If we get here, the command is allowed
exit 0

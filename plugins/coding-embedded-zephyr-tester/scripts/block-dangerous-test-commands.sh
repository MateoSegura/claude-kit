#!/bin/bash
set -euo pipefail
# block-dangerous-test-commands.sh — Blocks dangerous commands in tester context
# Called by hooks.json as a PreToolUse hook on Bash tool
# Tester agents should only run tests, not flash/debug/erase hardware
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block west flash — tester should never flash hardware
if echo "$COMMAND" | grep -qE 'west\s+flash'; then
  echo "BLOCKED: west flash is not allowed in tester context. The tester plugin runs tests via twister, not flash firmware. Use the engineer plugin for flashing." >&2
  exit 2
fi

# Block west debug — tester should never start debug sessions
if echo "$COMMAND" | grep -qE 'west\s+debug'; then
  echo "BLOCKED: west debug is not allowed in tester context. The tester plugin analyzes test results, not debug firmware. Use the engineer plugin for debugging." >&2
  exit 2
fi

# Block rm -rf on critical paths
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*r|--force.*--recursive|-[a-zA-Z]*r[a-zA-Z]*f|--recursive.*--force)'; then
  if echo "$COMMAND" | grep -qE '(/\s|/\$|~|home|\$HOME|\$ZEPHYR_BASE|zephyr\s|project|src/)'; then
    echo "BLOCKED: Destructive rm -rf command targeting critical path. Review the path carefully and use a more targeted deletion." >&2
    exit 2
  fi
fi

# Block git push --force to main/master
if echo "$COMMAND" | grep -qE 'git\s+push.*--force'; then
  if echo "$COMMAND" | grep -qE '(main|master)'; then
    echo "BLOCKED: Force push to main/master is not allowed." >&2
    exit 2
  fi
  echo "WARNING: Force push detected. Ensure you understand the implications." >&2
fi

# Block git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards all uncommitted work. Stash or commit first." >&2
  exit 2
fi

# Warn on sudo usage
if echo "$COMMAND" | grep -qE '^\s*sudo\s+'; then
  echo "WARNING: sudo command detected. Running as root can be dangerous. Ensure this is necessary." >&2
fi

# Warn on nrfjprog --eraseall
if echo "$COMMAND" | grep -qE 'nrfjprog.*--eraseall'; then
  echo "WARNING: nrfjprog --eraseall will erase the entire flash. This is destructive for production hardware." >&2
fi

# Allow west twister (this is what tester agents should be running)
# Allow west build (needed for test compilation)
# Allow all other safe commands

exit 0

#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive shell commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block rm -rf on critical paths
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*r|--force.*--recursive|-[a-zA-Z]*r[a-zA-Z]*f|--recursive.*--force)'; then
  if echo "$COMMAND" | grep -qE '(/\s|/\$|~|home|\$HOME|\$ZEPHYR_BASE|zephyr\s|project)'; then
    echo "BLOCKED: Destructive rm -rf command targeting critical path. This could delete the Zephyr tree, project root, or home directory. Review the path carefully and use a more targeted deletion." >&2
    exit 2
  fi
fi

# Block git push --force to main/master
if echo "$COMMAND" | grep -qE 'git\s+push.*--force'; then
  if echo "$COMMAND" | grep -qE '(main|master)'; then
    echo "BLOCKED: Force push to main/master is not allowed. This could overwrite shared history. Use --force-with-lease if you must override, or resolve conflicts through proper merge/rebase." >&2
    exit 2
  fi
  # Warn on force push to other branches
  echo "WARNING: Force push detected. This rewrites history. Ensure you understand the implications." >&2
fi

# Block git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards all uncommitted work. Stash or commit your changes first." >&2
  exit 2
fi

# Block dd commands with device output
if echo "$COMMAND" | grep -qE 'dd\s+.*of=/dev/'; then
  echo "BLOCKED: dd command writing to /dev/ device. This can overwrite disk partitions or connected hardware. Verify the target device explicitly with the user before proceeding." >&2
  exit 2
fi

# Warn on chmod 777
if echo "$COMMAND" | grep -qE 'chmod\s+(777|a\+rwx)'; then
  echo "WARNING: chmod 777 grants full permissions to all users. This is a security risk. Use more restrictive permissions (e.g., 755 or 644)." >&2
fi

# Warn on sudo usage
if echo "$COMMAND" | grep -qE '^\s*sudo\s+'; then
  echo "WARNING: sudo command detected. Running as root can be dangerous. Ensure this is necessary for the operation." >&2
fi

# Warn on nrfjprog --eraseall (dangerous for real hardware)
if echo "$COMMAND" | grep -qE 'nrfjprog.*--eraseall'; then
  echo "WARNING: nrfjprog --eraseall will erase the entire flash, including bootloader and UICR. This is destructive for production hardware. Confirm this is intentional." >&2
fi

# Warn on west flash without --verify on non-native_sim boards
if echo "$COMMAND" | grep -qE 'west\s+flash'; then
  if ! echo "$COMMAND" | grep -qE '(--verify|native_sim|native_posix)'; then
    echo "WARNING: west flash without --verify. Consider adding --verify to confirm successful flashing on real hardware." >&2
  fi
fi

exit 0

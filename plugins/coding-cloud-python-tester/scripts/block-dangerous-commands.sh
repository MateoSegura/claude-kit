#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive shell commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# Allows: pytest, docker, uv
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Block rm -rf targeting broad or sensitive paths
if echo "$COMMAND" | grep -qE 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r'; then
  if echo "$COMMAND" | grep -qE '(/\s*$|/\.|~\s*$|\.\.\s*$|/(etc|usr|var|home|root|bin|lib|sys|proc|dev)\b)'; then
    echo "BLOCKED: Destructive rm -rf targeting a sensitive or root path. Use a more targeted path." >&2
    exit 2
  fi
fi

# Block dropping databases or tables
if echo "$COMMAND" | grep -qiE '(DROP\s+DATABASE|DROP\s+TABLE|TRUNCATE\s+TABLE)'; then
  echo "BLOCKED: Destructive SQL statement detected. Do not drop or truncate tables from automated hooks." >&2
  exit 2
fi

# Block force-push to remote
if echo "$COMMAND" | grep -qE 'git\s+push\s+(.*\s+)?--force($|\s)' && ! echo "$COMMAND" | grep -qE '--force-with-lease'; then
  echo "BLOCKED: git push --force is not allowed. Use --force-with-lease if overriding is necessary." >&2
  exit 2
fi

# Block git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards uncommitted changes. Stash or commit work before resetting." >&2
  exit 2
fi

# Block writing to /etc, /usr, /bin, /sbin, /lib, /boot, /sys, /proc
if echo "$COMMAND" | grep -qE '>\s*/(etc|usr|bin|sbin|lib|boot|sys|proc)/'; then
  echo "BLOCKED: Writing to a system directory is not permitted." >&2
  exit 2
fi

# Block sudo with destructive subcommands
if echo "$COMMAND" | grep -qE 'sudo\s+(rm|mkfs|dd|shred|wipefs)'; then
  echo "BLOCKED: sudo with a destructive command ($COMMAND) is not allowed." >&2
  exit 2
fi

# Block chmod 777 (broad permission grants)
if echo "$COMMAND" | grep -qE 'chmod\s+(777|a\+rwx|o\+wx)'; then
  echo "BLOCKED: chmod 777 / a+rwx / o+wx grants world-write access. Use more restrictive permissions." >&2
  exit 2
fi

# Block redirecting to /dev/sd* or /dev/nvme* (disk wipe patterns)
if echo "$COMMAND" | grep -qE '>\s*/dev/(sd|nvme|vd|hd)[a-z]'; then
  echo "BLOCKED: Redirecting output to a raw block device is not permitted." >&2
  exit 2
fi

exit 0

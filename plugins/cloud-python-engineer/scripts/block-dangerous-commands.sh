#!/usr/bin/env bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive shell commands for cloud Python projects
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Block rm -rf on sensitive paths (root, home, etc, var, src, app, data)
if echo "$COMMAND" | grep -qE 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r'; then
  if echo "$COMMAND" | grep -qE '(/\s*$|/\.|~|/home|/etc|/var|/usr|/opt|/srv|/data|/app|/src|\.\.)'; then
    echo "BLOCKED: rm -rf targeting a sensitive path. Use a more targeted deletion with an explicit relative path inside the project directory." >&2
    exit 2
  fi
fi

# Block git force push
if echo "$COMMAND" | grep -qE 'git\s+push\s+(.*\s+)?(-f|--force)\b'; then
  echo "BLOCKED: Force push is not allowed. Use --force-with-lease if you must override, or resolve conflicts through a proper merge/rebase workflow." >&2
  exit 2
fi

# Block git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards uncommitted work permanently. Stash or commit your changes first, then reset if needed." >&2
  exit 2
fi

# Block DROP TABLE (raw SQL against databases)
if echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b'; then
  echo "BLOCKED: DROP TABLE detected. Use Alembic migration downgrade or a reviewed migration script instead of raw DDL drops." >&2
  exit 2
fi

# Block kubectl delete namespace (cannot be undone)
if echo "$COMMAND" | grep -qE 'kubectl\s+(delete|del)\s+namespace\b'; then
  echo "BLOCKED: kubectl delete namespace is irreversible and will destroy all workloads in the namespace. Verify intent and execute manually outside the agent session." >&2
  exit 2
fi

# Block docker system prune (destroys volumes, images, containers)
if echo "$COMMAND" | grep -qE 'docker\s+system\s+prune'; then
  echo "BLOCKED: docker system prune removes all unused images, containers, networks, and volumes. Run manually with explicit --filter flags after reviewing what will be removed." >&2
  exit 2
fi

# Block helm uninstall on production releases
if echo "$COMMAND" | grep -qE 'helm\s+uninstall\b'; then
  if echo "$COMMAND" | grep -qiE '(prod|production|prd|live)'; then
    echo "BLOCKED: helm uninstall targeting a production release. Verify the release name and environment, then execute manually with explicit cluster context set." >&2
    exit 2
  fi
fi

exit 0

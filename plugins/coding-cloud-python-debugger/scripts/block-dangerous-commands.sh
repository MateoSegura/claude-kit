#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive cloud/DB/infra commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Block kubectl delete (namespace, pod, deployment, etc.)
if echo "$COMMAND" | grep -qE 'kubectl\s+delete'; then
  echo "BLOCKED: 'kubectl delete' is destructive. Use 'kubectl describe', 'kubectl get', or 'kubectl logs' for read-only diagnosis." >&2
  exit 2
fi

# Block docker rm -f
if echo "$COMMAND" | grep -qE 'docker\s+(rm|container\s+rm)\s+.*-[a-zA-Z]*f'; then
  echo "BLOCKED: 'docker rm -f' forcibly removes containers. Use 'docker inspect' or 'docker logs' to diagnose instead." >&2
  exit 2
fi

# Block raw SQL DROP TABLE / DROP DATABASE / TRUNCATE
if echo "$COMMAND" | grep -qiE '(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)'; then
  echo "BLOCKED: Destructive SQL DDL statement detected (DROP/TRUNCATE). Use EXPLAIN ANALYZE or SELECT queries for debugging." >&2
  exit 2
fi

# Block rm -rf targeting source directories
# Allow /tmp, but block anything that looks like a source tree
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive.*--force|--force.*--recursive)'; then
  # Allow /tmp paths
  if ! echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]+ )+/tmp/'; then
    echo "BLOCKED: 'rm -rf' on a non-/tmp path risks destroying source files. Identify and remove specific files instead." >&2
    exit 2
  fi
fi

# Block git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: 'git reset --hard' discards uncommitted changes. Stash or commit changes before resetting." >&2
  exit 2
fi

# Block git push --force / git push -f (both long and short form)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(-f\b|--force\b)'; then
  echo "BLOCKED: Force push is not allowed. Use '--force-with-lease' only after explicit team agreement, or resolve divergence normally." >&2
  exit 2
fi

exit 0

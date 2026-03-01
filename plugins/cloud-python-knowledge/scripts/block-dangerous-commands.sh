#!/usr/bin/env bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive commands in cloud/container environments
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Block kubectl delete without --dry-run (destructive cluster operations)
if echo "$COMMAND" | grep -qE 'kubectl\s+delete'; then
  if ! echo "$COMMAND" | grep -qE '\-\-dry\-run'; then
    echo "BLOCKED: 'kubectl delete' without --dry-run may affect production resources." >&2
    echo "  Add --dry-run=client to preview the operation first, or confirm you intend to delete live resources." >&2
    exit 2
  fi
fi

# Block kubectl rollout restart / scale to 0 on production namespaces
if echo "$COMMAND" | grep -qE 'kubectl\s+(rollout\s+restart|scale\s+.*--replicas=0)'; then
  if echo "$COMMAND" | grep -qE '\-n\s*(prod|production|live|staging)'; then
    echo "BLOCKED: Dangerous kubectl operation targeting a production/staging namespace." >&2
    echo "  Verify the target namespace and confirm this is intentional before proceeding." >&2
    exit 2
  fi
fi

# Block docker rm -f on running containers (forces removal of live containers)
if echo "$COMMAND" | grep -qE 'docker\s+(rm|container\s+rm)\s+(-f|--force)'; then
  echo "BLOCKED: 'docker rm -f' forcefully removes running containers without graceful shutdown." >&2
  echo "  Use 'docker stop <container>' first, then 'docker rm <container>'." >&2
  exit 2
fi

# Block docker system prune without confirmation flag awareness
if echo "$COMMAND" | grep -qE 'docker\s+system\s+prune\s+(-a|--all)\s+(-f|--force)'; then
  echo "BLOCKED: 'docker system prune -af' removes ALL unused images, networks, and containers." >&2
  echo "  Run without -f to review what will be removed, or remove -a to keep tagged images." >&2
  exit 2
fi

# Block pip install --break-system-packages (corrupts system Python)
if echo "$COMMAND" | grep -qE 'pip[23]?\s+install.*--break-system-packages'; then
  echo "BLOCKED: --break-system-packages can corrupt the system Python installation." >&2
  echo "  Use a virtual environment (python -m venv .venv) or a container instead." >&2
  exit 2
fi

# Block pip install directly on the system Python without a venv (heuristic: no venv activated)
# Allow pip inside virtual envs or docker RUN contexts
if echo "$COMMAND" | grep -qE '^pip[23]?\s+install\s+.*--target\s+/usr'; then
  echo "BLOCKED: Installing pip packages to /usr system paths is unsafe." >&2
  echo "  Use a virtual environment or install to a project-local directory." >&2
  exit 2
fi

# Block rm -rf on project root or common important directories
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive.*--force|--force.*--recursive)'; then
  if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]+ )*(\/\s*$|\.\s*$|\.\.\s*$|~\s*$|\/home|\/var|\/etc|\/usr|\/opt|\/app\s*$|\/src\s*$|\/code\s*$)'; then
    echo "BLOCKED: Recursive force-delete targeting a critical directory or project root." >&2
    echo "  Specify a more targeted path. Double-check the path before deleting." >&2
    exit 2
  fi
fi

# Block terraform destroy without -target (destroys entire infrastructure)
if echo "$COMMAND" | grep -qE 'terraform\s+destroy'; then
  if ! echo "$COMMAND" | grep -qE '\-target'; then
    echo "BLOCKED: 'terraform destroy' without -target will destroy ALL managed infrastructure." >&2
    echo "  Use 'terraform destroy -target=<resource>' to limit scope, or add --auto-approve only after review." >&2
    exit 2
  fi
fi

# Block dropping databases
if echo "$COMMAND" | grep -qiE '(DROP\s+DATABASE|DROP\s+SCHEMA)\s+\w+'; then
  echo "BLOCKED: DROP DATABASE/SCHEMA detected. This is irreversible." >&2
  echo "  Ensure you have a current backup and are targeting the correct database before proceeding." >&2
  exit 2
fi

# Block truncating tables without explicit confirmation pattern
if echo "$COMMAND" | grep -qiE 'TRUNCATE\s+TABLE\s+\w+'; then
  echo "BLOCKED: TRUNCATE TABLE detected. This permanently removes all rows." >&2
  echo "  Use DELETE with a WHERE clause to remove specific rows, or confirm this is intentional." >&2
  exit 2
fi

# Block git push --force to main/master/production branches
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force'; then
  if echo "$COMMAND" | grep -qE '(main|master|prod|production|release)'; then
    echo "BLOCKED: Force-pushing to a protected branch (main/master/prod) is not allowed." >&2
    echo "  Use --force-with-lease on a feature branch, or open a PR to merge changes." >&2
    exit 2
  fi
fi

exit 0

#!/usr/bin/env bash
set -euo pipefail
# check-protected-files.sh — Blocks writes to protected files in cloud Python projects
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Block writes to Python dependency lock files
if echo "$FILE_PATH" | grep -qE '(uv\.lock|poetry\.lock|pip\.lock|requirements\.lock)$'; then
  echo "BLOCKED: Do not modify lock files directly. Use 'uv lock', 'poetry lock', or 'pip-compile' to regenerate them after updating your dependency declarations." >&2
  exit 2
fi

# Block writes to .env files (secrets must not be overwritten by the agent)
if echo "$FILE_PATH" | grep -qE '(^|/)\.env(\.[a-zA-Z0-9._-]+)?$'; then
  echo "BLOCKED: Do not write to .env files. Manage secrets through your secrets manager (e.g., AWS Secrets Manager, GCP Secret Manager, Vault) or ask the developer to update environment configuration manually." >&2
  exit 2
fi

# Block writes to already-applied Alembic migration files
# Heuristic: alembic/versions/*.py files that already exist on disk are applied migrations
if echo "$FILE_PATH" | grep -qE '(alembic|migrations)/versions/[^/]+\.py$'; then
  # If the file already exists, it may already be applied — block modification
  if [[ -f "$FILE_PATH" ]]; then
    echo "BLOCKED: Modifying an existing Alembic migration file is unsafe. Already-applied migrations must not change. Create a new migration with 'alembic revision --autogenerate' to add further schema changes." >&2
    exit 2
  fi
fi

# Block writes to Kubernetes Secret manifests
if echo "$FILE_PATH" | grep -qE '\.(ya?ml)$'; then
  # Check if the file content being written looks like a K8s Secret
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
  if echo "$CONTENT" | grep -qE 'kind:\s*Secret'; then
    echo "BLOCKED: Writing a Kubernetes Secret manifest is not allowed. Secrets must be managed through a secrets manager (Vault, AWS Secrets Manager, Sealed Secrets) or applied manually by an operator." >&2
    exit 2
  fi

  # Also block if the file path itself signals a K8s secret file
  if echo "$FILE_PATH" | grep -qiE '(secret|secrets)\.(ya?ml)$'; then
    echo "BLOCKED: This file path looks like a Kubernetes Secrets manifest. Manage secrets through a dedicated secrets manager or have an operator apply them manually." >&2
    exit 2
  fi
fi

exit 0

#!/bin/bash
set -euo pipefail
# check-protected-files.sh — Blocks writes to protected files
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Block writes to package lock files — must be managed by the package manager
if echo "$FILE_PATH" | grep -qE '(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|npm-shrinkwrap\.json)$'; then
  echo "BLOCKED: Do not modify lock files directly. Use the package manager to update dependencies: pnpm add <pkg> or pnpm update <pkg>." >&2
  exit 2
fi

# Block writes to CI/CD workflow files — require human review
if echo "$FILE_PATH" | grep -qE '\.github/(workflows|actions)/.*\.(yml|yaml)$'; then
  echo "BLOCKED: CI/CD workflow files in .github/ are protected. Review and edit these manually after discussion with the team." >&2
  exit 2
fi

# Block writes to production environment files — sensitive configuration
if echo "$FILE_PATH" | grep -qE '\.env\.(production|prod|staging|live)$'; then
  echo "BLOCKED: Production environment files (.env.production, .env.prod, .env.staging) are protected. Edit these manually with care — they contain sensitive configuration." >&2
  exit 2
fi

# Warn about (but allow) writes to base .env file — it may contain local dev secrets
# We do not block .env because it is commonly committed as a template without real secrets
# Only block if the file contains obvious real secrets (we can't check content here, so just warn)
if echo "$FILE_PATH" | grep -qE '^\.env$|/\.env$'; then
  # Non-blocking: .env is commonly a template file. Print informational message only.
  echo "NOTE: Writing to .env file. Ensure this file does not contain real secrets before committing. Use .env.example for committed templates." >&2
fi

exit 0

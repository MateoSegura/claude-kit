#!/bin/bash
set -euo pipefail
# check-safe-svelte-command.sh — Blocks dangerous commands that could damage a Svelte project
# Called by hooks.json as a PreToolUse hook on the Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Block rm -rf node_modules without explicit confirmation pattern
# We look for bare `rm -rf node_modules` or `rm -rf ./node_modules` without a preceding confirmation step
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive.*--force|--force.*--recursive)\s+\.?/?node_modules'; then
  echo "BLOCKED: Deleting node_modules with rm -rf is destructive and slow to recover from." >&2
  echo "  Use one of these safer alternatives instead:" >&2
  echo "    npm ci          — clean install from package-lock.json" >&2
  echo "    pnpm install    — reinstall with pnpm" >&2
  echo "    npx rimraf node_modules && npm install  — cross-platform clean reinstall" >&2
  exit 2
fi

# Block force-deletion of .svelte-kit directory (generated build cache)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive.*--force|--force.*--recursive)\s+\.?/?\.svelte-kit'; then
  echo "BLOCKED: Force-deleting .svelte-kit is rarely necessary and may corrupt build state." >&2
  echo "  To reset SvelteKit build cache safely, use:" >&2
  echo "    npx svelte-kit sync   — regenerate .svelte-kit" >&2
  echo "    npm run build         — rebuild from scratch" >&2
  exit 2
fi

# Block rm -rf targeting the entire project root or parent
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+(\/|~|\.\.\/)'; then
  echo "BLOCKED: Destructive rm -rf targeting the project root or a parent directory." >&2
  echo "  Verify the path is correct and use a more targeted deletion." >&2
  exit 2
fi

# Block git push --force to main or master (protect production branches)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force[^-]' && echo "$COMMAND" | grep -qE '(main|master)'; then
  echo "BLOCKED: Force-pushing to main/master is not allowed." >&2
  echo "  Use --force-with-lease to prevent overwriting others' work, or resolve conflicts normally." >&2
  exit 2
fi

# Block git reset --hard without a specific safe ref
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard\s*$'; then
  echo "BLOCKED: git reset --hard with no ref discards all uncommitted work irreversibly." >&2
  echo "  Stash your changes first: git stash && git reset --hard <ref>" >&2
  exit 2
fi

exit 0

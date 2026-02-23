#!/bin/bash
set -euo pipefail
# check-safe-command.sh — Blocks destructive shell commands for the svelte-tester role
# Called by hooks.json as a PreToolUse hook on the Bash tool
# The tester must never run commands that destroy data, force-push, or modify production source
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Block rm -rf targeting sensitive paths (project source, home, system directories)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?|--recursive|--force)'; then
  if echo "$COMMAND" | grep -qE '(/src|/lib|/routes|/components|/stores|\.svelte|\.ts|~|/home|/etc|/var|/usr|\.\.)'; then
    echo "BLOCKED: rm targeting source files or sensitive system paths is not allowed for the tester role." >&2
    echo "The tester writes test files only. If cleanup is needed, target only test directories (e.g. src/**/*.test.ts)." >&2
    exit 2
  fi
fi

# Block git force push (any variant)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(-f\b|--force\b)' && ! echo "$COMMAND" | grep -qE '--force-with-lease'; then
  echo "BLOCKED: git push --force is not allowed. Use --force-with-lease if you must override, or resolve conflicts normally." >&2
  exit 2
fi

# Block git reset --hard (discards uncommitted work)
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards uncommitted work. Stash changes first with git stash, or commit them." >&2
  exit 2
fi

# Block git clean -f (removes untracked files without review)
if echo "$COMMAND" | grep -qE 'git\s+clean\s+.*-f'; then
  echo "BLOCKED: git clean -f permanently deletes untracked files. Review which files would be deleted with git clean -n first." >&2
  exit 2
fi

# Block npm publish / pnpm publish / yarn publish (tester must not publish packages)
if echo "$COMMAND" | grep -qE '(npm|pnpm|yarn)\s+publish'; then
  echo "BLOCKED: Publishing packages is outside the scope of the tester role. The tester writes and runs tests only." >&2
  exit 2
fi

# Block direct writes to production source via shell redirection (e.g. echo "..." > src/lib/MyComponent.svelte)
if echo "$COMMAND" | grep -qE '>\s*(src/|lib/|routes/).*\.(svelte|ts|js)$' && ! echo "$COMMAND" | grep -qE '(\.test\.|\.spec\.)'; then
  echo "BLOCKED: Redirecting output to production source files (.svelte, .ts, .js in src/ or lib/) is not allowed." >&2
  echo "The tester writes test files only (.test.ts, .spec.ts, playwright.config.ts, vitest.config.ts)." >&2
  exit 2
fi

# Block dd and other low-level destructive commands
if echo "$COMMAND" | grep -qE '^\s*(dd\s|mkfs\.|shred\s)'; then
  echo "BLOCKED: Low-level destructive command detected. This command is not allowed in the tester role." >&2
  exit 2
fi

exit 0

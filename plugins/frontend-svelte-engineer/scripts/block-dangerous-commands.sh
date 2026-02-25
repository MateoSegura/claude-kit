#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive shell commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Block rm -rf targeting sensitive or broad paths
# Allow rm -rf on clearly scoped build/tmp/node_modules targets
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*)'; then
  if echo "$COMMAND" | grep -qE 'rm\s+.*(-rf|-fr)\s+(/|~|\$HOME|\.\./)'; then
    echo "BLOCKED: rm -rf targeting root, home, or parent directory is not allowed. Use a more targeted path." >&2
    exit 2
  fi
  if echo "$COMMAND" | grep -qE 'rm\s+.*(-rf|-fr)\s+.*(src/|lib/|app/|routes/|components/)'; then
    echo "BLOCKED: rm -rf targeting source directories (src/, lib/, app/, routes/, components/) is not allowed. Delete individual files or use git to revert." >&2
    exit 2
  fi
fi

# Block git push --force (use --force-with-lease instead)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force([^-]|$)'; then
  echo "BLOCKED: git push --force is not allowed. Use --force-with-lease to prevent overwriting others' work, or resolve conflicts normally." >&2
  exit 2
fi

# Block git reset --hard (discards uncommitted work)
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards all uncommitted changes. Stash or commit your work first, then reset." >&2
  exit 2
fi

# Block npm publish without --dry-run (accidental package publishing)
if echo "$COMMAND" | grep -qE '(npm|pnpm)\s+publish'; then
  if ! echo "$COMMAND" | grep -qE -- '--dry-run'; then
    echo "BLOCKED: npm/pnpm publish without --dry-run is not allowed. Run with --dry-run first to verify the package contents, then publish manually after review." >&2
    exit 2
  fi
fi

# Block git clean -fd (removes untracked files)
if echo "$COMMAND" | grep -qE 'git\s+clean\s+.*-[a-zA-Z]*f'; then
  echo "BLOCKED: git clean -f removes untracked files permanently. Use 'git status' to review untracked files first, then delete individually if needed." >&2
  exit 2
fi

exit 0

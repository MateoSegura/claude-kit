#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Block destructive shell commands; allow read-only diagnostics
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# ── Blocked patterns ────────────────────────────────────────────────────────

# Destructive file removal
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive|--force)'; then
  echo "BLOCKED: rm -rf is not permitted in read-only diagnostic mode. This plugin diagnoses — it does not modify files." >&2
  exit 2
fi

# Hard git reset (discards uncommitted work)
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard is not permitted. It discards uncommitted changes. Use the engineer plugin to apply fixes." >&2
  exit 2
fi

# Force push
if echo "$COMMAND" | grep -qE 'git\s+push\s+(.*\s)?--force'; then
  echo "BLOCKED: git push --force is not permitted in diagnostic mode." >&2
  exit 2
fi

# In-place sed edits (modifies files)
if echo "$COMMAND" | grep -qE 'sed\s+(.*\s)?-i'; then
  echo "BLOCKED: sed -i modifies files in place. This plugin is read-only. Use the engineer plugin to apply fixes." >&2
  exit 2
fi

# patch command (modifies files)
if echo "$COMMAND" | grep -qE '^\s*patch(\s|$)'; then
  echo "BLOCKED: patch modifies files. This plugin is read-only. Use the engineer plugin to apply fixes." >&2
  exit 2
fi

# Redirect into files (tee >, >file, >>file)
if echo "$COMMAND" | grep -qE '(tee\s+[^|]|\s+>+\s*\S)'; then
  echo "BLOCKED: Redirecting output to files is not permitted in read-only diagnostic mode." >&2
  exit 2
fi

# npm publish
if echo "$COMMAND" | grep -qE 'npm\s+publish'; then
  echo "BLOCKED: npm publish is not permitted in diagnostic mode." >&2
  exit 2
fi

# npx --yes / npx -y (auto-install arbitrary packages)
if echo "$COMMAND" | grep -qE 'npx\s+(--yes|-y)\s'; then
  echo "BLOCKED: npx --yes auto-installs packages without confirmation. Use npx --no-install to restrict to already-installed tools." >&2
  exit 2
fi

# ── Allowed pattern fast-path ────────────────────────────────────────────────
# If the command matches a known safe diagnostic pattern, allow immediately.

if echo "$COMMAND" | grep -qE \
  '(svelte-check|tsc\s+--noEmit|vitest\s+--run|playwright\s+test|node\s+(--version|-e)|npm\s+(ls|list|run\s+check|run\s+type-check)|npx\s+(vitest|playwright|svelte-check|tsc)|cat\s|less\s|head\s|tail\s|ls(\s|$)|find\s|grep\s|rg\s|git\s+(log|diff|status|show)|echo\s)'; then
  exit 0
fi

# ── Default: allow anything not explicitly blocked ───────────────────────────
# The block list above covers the most dangerous operations. Unknown commands
# are permitted so the debugger can run project-specific diagnostic scripts.
exit 0

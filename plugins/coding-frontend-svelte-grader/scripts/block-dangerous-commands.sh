#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive and mutating shell commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# The grader should only run read-only diagnostic commands (svelte-check, tsc --noEmit, grep, find)
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block rm with recursive or force flags targeting non-trivial paths
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*[rf]|--(recursive|force))'; then
  if echo "$COMMAND" | grep -qE '(/|\.\.|~|home|etc|var|usr|node_modules|src|lib|components|routes|stores)'; then
    echo "BLOCKED: Destructive rm command detected targeting a significant path. The grader must not delete project files. Only read-only analysis commands are permitted." >&2
    exit 2
  fi
fi

# Block git push (any form — grader must not push)
if echo "$COMMAND" | grep -qE 'git\s+push'; then
  echo "BLOCKED: git push is not permitted from the grader. The grader evaluates code — it does not modify or push repositories." >&2
  exit 2
fi

# Block git force operations
if echo "$COMMAND" | grep -qE 'git\s+(reset\s+--hard|clean\s+-[a-zA-Z]*f|checkout\s+\.|restore\s+\.)'; then
  echo "BLOCKED: Destructive git operation detected. The grader must not modify the submission repository's working tree." >&2
  exit 2
fi

# Block npm/pnpm/yarn publish
if echo "$COMMAND" | grep -qE '(npm|pnpm|yarn)\s+publish'; then
  echo "BLOCKED: Package publishing is not permitted from the grader. The grader evaluates submissions — it does not publish packages." >&2
  exit 2
fi

# Block npm/pnpm/yarn install that would mutate node_modules in the submission
if echo "$COMMAND" | grep -qE '(npm|pnpm|yarn)\s+install\b' && ! echo "$COMMAND" | grep -qE '--dry-run'; then
  echo "BLOCKED: Package installation is not permitted from the grader. The grader must not modify the submission's node_modules. Use --dry-run for inspection only." >&2
  exit 2
fi

# Block writes via shell redirection to source files
if echo "$COMMAND" | grep -qE '>\s*\S+\.(svelte|ts|tsx|js|jsx|css|scss|sass)'; then
  echo "BLOCKED: Shell output redirection to source files is not permitted. The grader must not modify submission source files." >&2
  exit 2
fi

# Block sed -i (in-place editing of files)
if echo "$COMMAND" | grep -qE "sed\s+(-[a-zA-Z]*i|--in-place)"; then
  echo "BLOCKED: In-place file editing with sed is not permitted. The grader must not modify submission source files." >&2
  exit 2
fi

# Block chmod changes that could expose the submission
if echo "$COMMAND" | grep -qE 'chmod\s+(777|a\+w|o\+w)'; then
  echo "BLOCKED: Permissive chmod operation detected. The grader must not alter file permissions on the submission." >&2
  exit 2
fi

exit 0

#!/bin/bash
set -euo pipefail
# block-dangerous-commands.sh — Blocks destructive shell commands in grading sessions
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq
#
# ALLOWED: read-only and analysis tools — mypy, ruff, pytest --collect-only,
#          cat, ls, find, grep, head, tail, wc, stat, file, tree
# BLOCKED: anything that modifies files, installs packages, or has side effects

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block file deletion
if echo "$COMMAND" | grep -qE '\brm\b'; then
  echo "BLOCKED: File deletion is not permitted in grading sessions. The grader is read-only." >&2
  exit 2
fi

# Block writes via redirection (e.g., > file, >> file, tee file)
if echo "$COMMAND" | grep -qE '(>[^>]|>>|tee\s+[^-])'; then
  # Allow grep/ruff/mypy output redirection only if clearly going to /dev/null
  if ! echo "$COMMAND" | grep -qE '>\s*/dev/null'; then
    echo "BLOCKED: Output redirection that writes to files is not permitted. The grader must not modify any files." >&2
    exit 2
  fi
fi

# Block package installation
if echo "$COMMAND" | grep -qE '\b(pip\s+install|pip3\s+install|uv\s+add|poetry\s+add|conda\s+install|apt(-get)?\s+install)\b'; then
  echo "BLOCKED: Package installation is not permitted in grading sessions. Use only the pre-installed analysis tools." >&2
  exit 2
fi

# Block git write operations
if echo "$COMMAND" | grep -qE '\bgit\s+(commit|push|add|reset|checkout|branch\s+-[Dd]|merge|rebase|stash\s+pop|rm|mv)\b'; then
  echo "BLOCKED: Git write operations are not permitted in grading sessions. Analysis only." >&2
  exit 2
fi

# Block destructive git operations
if echo "$COMMAND" | grep -qE 'git\s+(push\s+.*--force|reset\s+--hard|clean\s+-[a-zA-Z]*f)'; then
  echo "BLOCKED: Destructive git operations are not permitted." >&2
  exit 2
fi

# Block sed/awk/perl with in-place edits
if echo "$COMMAND" | grep -qE '\bsed\s+(-[a-zA-Z]*i|--in-place)'; then
  echo "BLOCKED: In-place file editing with sed is not permitted. The grader must not modify source files." >&2
  exit 2
fi

if echo "$COMMAND" | grep -qE '\bperl\s+(-[a-zA-Z]*i|--in-place)'; then
  echo "BLOCKED: In-place file editing with perl is not permitted. The grader must not modify source files." >&2
  exit 2
fi

# Block cp/mv that would overwrite project files (allow copying to /tmp)
if echo "$COMMAND" | grep -qE '\b(mv|cp)\b' && ! echo "$COMMAND" | grep -qE '/tmp/'; then
  echo "BLOCKED: Moving or copying project files is not permitted in grading sessions." >&2
  exit 2
fi

# Block chmod/chown
if echo "$COMMAND" | grep -qE '\b(chmod|chown)\b'; then
  echo "BLOCKED: Permission changes are not permitted in grading sessions." >&2
  exit 2
fi

# Block make/cmake write targets (allow check/test targets that are read-only by convention)
if echo "$COMMAND" | grep -qE '\bmake\s+(install|clean|distclean|uninstall)\b'; then
  echo "BLOCKED: Make install/clean targets are not permitted. Use make check or make test for analysis only." >&2
  exit 2
fi

# Block docker write operations
if echo "$COMMAND" | grep -qE '\bdocker\s+(run|exec|build|push|rm|rmi|stop|kill|create)\b'; then
  echo "BLOCKED: Docker operations are not permitted in grading sessions." >&2
  exit 2
fi

# Block sudo
if echo "$COMMAND" | grep -qE '\bsudo\b'; then
  echo "BLOCKED: sudo is not permitted in grading sessions." >&2
  exit 2
fi

# Block curl/wget with output (downloading is a side effect)
if echo "$COMMAND" | grep -qE '\b(curl|wget)\b' && ! echo "$COMMAND" | grep -qE '(-I|-s\s+--head|--spider|--dry-run)'; then
  echo "BLOCKED: Network downloads are not permitted in grading sessions. Grading is offline analysis only." >&2
  exit 2
fi

# Block pytest with side effects (allow --collect-only and read-only runs, but not xdist write modes)
# Pytest itself is allowed for reading — block only if it writes coverage or mutant files
if echo "$COMMAND" | grep -qE '\bpytest\b.*--cov-report\s*=\s*(xml|html)'; then
  echo "BLOCKED: pytest coverage report generation that writes files is not permitted. Use --co or --collect-only for analysis." >&2
  exit 2
fi

exit 0

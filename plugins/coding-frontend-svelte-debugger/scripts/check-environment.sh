#!/bin/bash
set -euo pipefail
# check-environment.sh — Verify diagnostic tools are available at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq (advisory check only — this script always exits 0)

WARN=0

# Helper: print version line or warn if command not found
check_tool() {
  local name="$1"
  local cmd="$2"
  local version_flag="${3:---version}"

  if command -v "$cmd" &>/dev/null; then
    local ver
    ver=$("$cmd" $version_flag 2>&1 | head -1 || true)
    echo "OK: $name found — $ver"
  else
    echo "WARN: $name ($cmd) not found — some diagnostics will be unavailable" >&2
    WARN=1
  fi
}

echo "=== Svelte Debugger — Environment Check ==="

# Node.js — require >= 18
if command -v node &>/dev/null; then
  NODE_VER=$(node --version 2>&1 | head -1)
  MAJOR=$(echo "$NODE_VER" | sed 's/v\([0-9]*\).*/\1/')
  if [ "$MAJOR" -ge 18 ] 2>/dev/null; then
    echo "OK: node found — $NODE_VER"
  else
    echo "WARN: node $NODE_VER is below the required v18. Upgrade for full Svelte 5 support." >&2
    WARN=1
  fi
else
  echo "WARN: node not found — required for all Svelte diagnostics" >&2
  WARN=1
fi

# npx — bundled with Node but worth confirming
check_tool "npx" "npx" "--version"

# svelte-check — project-level type and template checking
if npx --no-install svelte-check --version &>/dev/null 2>&1; then
  SVE_VER=$(npx --no-install svelte-check --version 2>&1 | head -1 || true)
  echo "OK: svelte-check found — $SVE_VER"
else
  echo "WARN: svelte-check not found in project. Run: npm install --save-dev svelte-check" >&2
  WARN=1
fi

# tsc — TypeScript compiler for .ts/.svelte type errors
if npx --no-install tsc --version &>/dev/null 2>&1; then
  TSC_VER=$(npx --no-install tsc --version 2>&1 | head -1 || true)
  echo "OK: tsc found — $TSC_VER"
else
  echo "WARN: tsc not found in project. Run: npm install --save-dev typescript" >&2
  WARN=1
fi

# vitest — unit test runner
if npx --no-install vitest --version &>/dev/null 2>&1; then
  VIT_VER=$(npx --no-install vitest --version 2>&1 | head -1 || true)
  echo "OK: vitest found — $VIT_VER"
else
  echo "WARN: vitest not found in project — unit test diagnostics unavailable" >&2
  WARN=1
fi

# playwright — end-to-end test runner
if npx --no-install playwright --version &>/dev/null 2>&1; then
  PW_VER=$(npx --no-install playwright --version 2>&1 | head -1 || true)
  echo "OK: playwright found — $PW_VER"
else
  echo "WARN: playwright not found in project — e2e diagnostics unavailable" >&2
  WARN=1
fi

if [ "$WARN" -eq 1 ]; then
  echo "" >&2
  echo "Some tools are missing. Diagnostics will be limited to available tools." >&2
fi

echo "=== Environment check complete ==="

# Always advisory — never block the session
exit 0

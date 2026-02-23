#!/bin/bash
set -euo pipefail
# check-environment.sh — Verifies required tools are available at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq

MISSING=""
WARNINGS=""

# Check for jq (needed by all other hook scripts)
if ! command -v jq &>/dev/null; then
  WARNINGS="${WARNINGS}\nWARNING: jq is not installed. Hook scripts require jq for JSON parsing. Install with: apt install jq / brew install jq"
fi

# Check for node
if ! command -v node &>/dev/null; then
  MISSING="${MISSING}\n  - node (https://nodejs.org)"
fi

# Check for pnpm (preferred) or npm (fallback)
if command -v pnpm &>/dev/null; then
  : # pnpm found — preferred package manager
elif command -v npm &>/dev/null; then
  WARNINGS="${WARNINGS}\nWARNING: pnpm not found. npm is available but pnpm is preferred for this plugin. Install pnpm: npm install -g pnpm"
else
  MISSING="${MISSING}\n  - pnpm or npm (https://pnpm.io)"
fi

# Check for svelte-check (type checking for Svelte files)
if ! command -v svelte-check &>/dev/null; then
  WARNINGS="${WARNINGS}\nWARNING: svelte-check not found. Install in your project: pnpm add -D svelte-check"
fi

# Check for tsc (TypeScript compiler)
if ! command -v tsc &>/dev/null; then
  WARNINGS="${WARNINGS}\nWARNING: tsc not found globally. TypeScript may still work via npx or project-local install. Install globally: pnpm add -g typescript"
fi

# Check for svelteserver (svelte-language-server)
if ! command -v svelteserver &>/dev/null; then
  WARNINGS="${WARNINGS}\nWARNING: svelte-language-server (svelteserver) not found. LSP features unavailable. Install: pnpm add -g svelte-language-server"
fi

# Report hard missing tools (still exit 0 — non-blocking)
if [ -n "$MISSING" ]; then
  echo "WARNING: Required tools not found. Install them to use this plugin fully:" >&2
  printf "%b\n" "$MISSING" >&2
fi

# Report soft warnings
if [ -n "$WARNINGS" ]; then
  printf "%b\n" "$WARNINGS" >&2
fi

# Always exit 0 — environment warnings never block the session
exit 0

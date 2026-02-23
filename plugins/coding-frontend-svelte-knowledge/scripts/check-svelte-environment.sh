#!/bin/bash
set -euo pipefail
# check-svelte-environment.sh — Reports Svelte project environment status at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq

CWD="${PWD}"

echo "=== Svelte Project Environment Check ===" >&2

# Check for svelte.config.js / svelte.config.ts
SVELTE_CONFIG=""
if [ -f "${CWD}/svelte.config.js" ]; then
  SVELTE_CONFIG="${CWD}/svelte.config.js"
elif [ -f "${CWD}/svelte.config.ts" ]; then
  SVELTE_CONFIG="${CWD}/svelte.config.ts"
fi

if [ -n "$SVELTE_CONFIG" ]; then
  echo "  [OK] Svelte config found: ${SVELTE_CONFIG}" >&2
else
  echo "  [WARN] No svelte.config.js / svelte.config.ts found in ${CWD}" >&2
fi

# Check package.json for Svelte dependency
PACKAGE_JSON="${CWD}/package.json"
if [ -f "$PACKAGE_JSON" ]; then
  if command -v jq &>/dev/null; then
    SVELTE_VERSION=$(jq -r '(.dependencies.svelte // .devDependencies.svelte // "not found")' "$PACKAGE_JSON" 2>/dev/null || echo "not found")
    SVELTEKIT_VERSION=$(jq -r '(.dependencies["@sveltejs/kit"] // .devDependencies["@sveltejs/kit"] // "not found")' "$PACKAGE_JSON" 2>/dev/null || echo "not found")

    if [ "$SVELTE_VERSION" != "not found" ]; then
      echo "  [OK] svelte: ${SVELTE_VERSION}" >&2
    else
      echo "  [WARN] svelte not found in package.json dependencies" >&2
    fi

    if [ "$SVELTEKIT_VERSION" != "not found" ]; then
      echo "  [OK] @sveltejs/kit: ${SVELTEKIT_VERSION}" >&2
    else
      echo "  [INFO] @sveltejs/kit not present (pure Svelte project or not yet installed)" >&2
    fi
  else
    echo "  [INFO] jq not installed — skipping package.json dependency check" >&2
  fi
else
  echo "  [WARN] No package.json found in ${CWD} — not in a Node.js project root" >&2
fi

# Check node_modules
if [ -d "${CWD}/node_modules" ]; then
  echo "  [OK] node_modules present" >&2
else
  echo "  [WARN] node_modules not found — run: npm install / pnpm install" >&2
fi

# Check for .svelte-kit (SvelteKit build cache)
if [ -d "${CWD}/.svelte-kit" ]; then
  echo "  [OK] .svelte-kit directory present (SvelteKit sync has run)" >&2
else
  echo "  [INFO] No .svelte-kit directory — run: npx svelte-kit sync (after install)" >&2
fi

echo "=== Environment check complete ===" >&2

exit 0

#!/bin/bash
set -euo pipefail
# check-environment.sh — Verifies test tooling is available at session start
# Called by hooks.json as a SessionStart hook
# Checks for: Node.js, npx, vitest, playwright, vitest-axe, relevant config files
# Always exits 0 — missing tools generate warnings, not hard failures
# Requires: jq (checked first)

WARNINGS=()
INFOS=()

# ─── Core runtime ────────────────────────────────────────────────────────────

if ! command -v node &> /dev/null; then
  WARNINGS+=("Node.js is not installed or not in PATH. All test tools require Node.js.")
else
  NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
  INFOS+=("Node.js: $NODE_VERSION")
fi

if ! command -v npx &> /dev/null; then
  WARNINGS+=("npx is not available. Install Node.js >= 18 to get npx.")
fi

if ! command -v jq &> /dev/null; then
  WARNINGS+=("jq is not installed. Hook scripts require jq for JSON parsing. Install: apt install jq / brew install jq")
fi

# ─── Package.json presence ───────────────────────────────────────────────────

if [[ ! -f "package.json" ]]; then
  WARNINGS+=("No package.json found in working directory. Are you in the project root?")
else
  INFOS+=("package.json found in working directory.")

  # ─── Vitest ────────────────────────────────────────────────────────────────

  if ! jq -e '.devDependencies.vitest // .dependencies.vitest // null' package.json &> /dev/null; then
    WARNINGS+=("vitest not found in package.json dependencies. Install: npm install -D vitest")
  else
    VITEST_VERSION=$(jq -r '.devDependencies.vitest // .dependencies.vitest // "unknown"' package.json 2>/dev/null)
    INFOS+=("vitest: $VITEST_VERSION")
  fi

  # ─── vitest-browser-svelte ─────────────────────────────────────────────────

  if ! jq -e '(.devDependencies["vitest-browser-svelte"] // .dependencies["vitest-browser-svelte"]) // null' package.json &> /dev/null; then
    WARNINGS+=("vitest-browser-svelte not found. Component tests in browser mode require it. Install: npm install -D vitest-browser-svelte")
  else
    INFOS+=("vitest-browser-svelte found.")
  fi

  # ─── vitest-axe ────────────────────────────────────────────────────────────

  if ! jq -e '(.devDependencies["vitest-axe"] // .dependencies["vitest-axe"]) // null' package.json &> /dev/null; then
    WARNINGS+=("vitest-axe not found. Accessibility tests require it. Install: npm install -D vitest-axe axe-core")
  else
    INFOS+=("vitest-axe found.")
  fi

  # ─── @playwright/test ──────────────────────────────────────────────────────

  if ! jq -e '(.devDependencies["@playwright/test"] // .dependencies["@playwright/test"]) // null' package.json &> /dev/null; then
    WARNINGS+=("@playwright/test not found. E2E tests require it. Install: npm install -D @playwright/test && npx playwright install")
  else
    PW_VERSION=$(jq -r '.devDependencies["@playwright/test"] // .dependencies["@playwright/test"] // "unknown"' package.json 2>/dev/null)
    INFOS+=("@playwright/test: $PW_VERSION")
  fi

  # ─── TypeScript ────────────────────────────────────────────────────────────

  if ! jq -e '.devDependencies.typescript // .dependencies.typescript // null' package.json &> /dev/null; then
    WARNINGS+=("typescript not found in package.json. Strict TypeScript is required for all test files.")
  else
    TS_VERSION=$(jq -r '.devDependencies.typescript // .dependencies.typescript // "unknown"' package.json 2>/dev/null)
    INFOS+=("typescript: $TS_VERSION")
  fi
fi

# ─── Config files ─────────────────────────────────────────────────────────────

if [[ ! -f "vitest.config.ts" ]] && [[ ! -f "vitest.config.js" ]]; then
  WARNINGS+=("No vitest.config.ts found. Vitest unit and component tests need a config file.")
else
  INFOS+=("vitest.config.ts found.")
fi

if [[ ! -f "playwright.config.ts" ]] && [[ ! -f "playwright.config.js" ]]; then
  WARNINGS+=("No playwright.config.ts found. Playwright E2E tests need a config file.")
else
  INFOS+=("playwright.config.ts found.")
fi

# ─── Chromium for browser-mode tests ─────────────────────────────────────────

if command -v npx &> /dev/null; then
  if ! npx playwright install --dry-run chromium &> /dev/null 2>&1; then
    # Check if chromium binary already exists instead
    if ! npx playwright install chromium --dry-run 2>&1 | grep -q "already installed" 2>/dev/null; then
      WARNINGS+=("Chromium browser binary may not be installed. Browser-mode Vitest tests require it. Run: npx playwright install chromium")
    fi
  fi
fi

# ─── Output ──────────────────────────────────────────────────────────────────

echo "=== coding-frontend-svelte-tester: Environment Check ==="

for info in "${INFOS[@]}"; do
  echo "  OK  $info"
done

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo ""
  echo "  WARNINGS — the following tools or config files are missing:"
  for warn in "${WARNINGS[@]}"; do
    echo "  WARN  $warn" >&2
  done
  echo ""
  echo "  Missing tools will cause test commands to fail. Install them before writing tests."
else
  echo ""
  echo "  All required test tools are available. Ready to write and run tests."
fi

# Always exit 0 — this is an informational check, not a hard gate
exit 0

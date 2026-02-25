#!/usr/bin/env bash
# Smoke tests for the claude-kit CLI.
# Tests exit codes and output content for all safe, non-destructive commands.
# Skips: setup, restore, uninstall (interactive/destructive), --kit <real> (launches Claude).

set -uo pipefail

CLI="$(cd "$(dirname "$0")/.." && pwd)/claude-kit"
PASS=0
FAIL=0

_ok()   { echo "  PASS  $1"; PASS=$((PASS + 1)); }
_fail() { echo "  FAIL  $1"; echo "        $2"; FAIL=$((FAIL + 1)); }

# Assert command exits with expected code
expect_exit() {
  local desc="$1" expected="$2"; shift 2
  local actual=0
  python3 "$CLI" "$@" >/dev/null 2>&1 || actual=$?
  if [ "$actual" -eq "$expected" ]; then _ok "$desc"
  else _fail "$desc" "expected exit $expected, got $actual"; fi
}

# Assert command output contains a string
expect_output() {
  local desc="$1" pattern="$2"; shift 2
  local out actual=0
  out=$(python3 "$CLI" "$@" 2>&1) || actual=$?
  if echo "$out" | grep -qF -- "$pattern"; then _ok "$desc"
  else _fail "$desc" "output missing '$pattern' (exit $actual)"; fi
}

# Assert command exits non-zero (any error)
expect_error() {
  local desc="$1"; shift
  local actual=0
  python3 "$CLI" "$@" >/dev/null 2>&1 || actual=$?
  if [ "$actual" -ne 0 ]; then _ok "$desc"
  else _fail "$desc" "expected non-zero exit, got 0"; fi
}

echo ""
echo "  claude-kit CLI smoke tests"
echo "  $(python3 "$CLI" version 2>/dev/null | grep -oP 'v\d+\.\d+\.\d+' | head -1)"
echo "  ──────────────────────────────────────"
echo ""

# ── help ──────────────────────────────────────────────────────────────────────
expect_exit   "help (positional)"    0 help
expect_exit   "help (--help)"        0 --help
expect_exit   "help (-h)"            0 -h
expect_output "help shows usage"     "claude-kit" help
expect_output "help shows --kit"     "--kit" help

# ── list ──────────────────────────────────────────────────────────────────────
expect_exit   "list exits 0"                      0 list
expect_output "list shows Bundled section"        "Bundled" list
expect_output "list shows a plugin"               "embedded-zephyr" list
expect_output "list shows shortcut hint"          "claude-kit -k" list
expect_output "list shows plugin version"         "0." list

# ── validate ──────────────────────────────────────────────────────────────────
expect_exit   "validate --all exits 0"            0 validate --all
expect_exit   "validate <plugin> exits 0"         0 validate embedded-zephyr-engineer
expect_exit   "validate --changed exits 0"        0 validate --changed
expect_error  "validate nonexistent plugin fails"   validate nonexistent-plugin-xyz-abc

# ── version ───────────────────────────────────────────────────────────────────
expect_exit   "version exits 0"                   0 version
expect_output "version shows tag format"          "v0." version

# ── core plugin structure (scalable — auto-discovers all core-* plugins) ──────
PLUGINS_DIR="$(cd "$(dirname "$0")/.." && pwd)/plugins"

# Every core-* knowledge plugin must have a domain field in ctl.json
# (core-spec is a system plugin, not a knowledge plugin — skip it)
for core_dir in "$PLUGINS_DIR"/core-*/; do
  [ -d "$core_dir" ] || continue
  name="$(basename "$core_dir")"
  ctl="$core_dir/.claude-plugin/ctl.json"
  if [ -f "$ctl" ]; then
    role=$(python3 -c "import json; print(json.load(open('$ctl')).get('role',''))" 2>/dev/null)
    [ "$role" = "system" ] && continue  # system plugins don't need domain
    domain=$(python3 -c "import json; print(json.load(open('$ctl')).get('domain',''))" 2>/dev/null)
    if [ -n "$domain" ]; then _ok "core domain: $name → $domain"
    else _fail "core domain: $name" "missing 'domain' in ctl.json"; fi
  else _fail "core domain: $name" "ctl.json not found"; fi
done

# Every team plugin must have a domain field in ctl.json
for team in embedded-zephyr cloud-python frontend-svelte; do
  for team_dir in "$PLUGINS_DIR"/${team}-*/; do
    [ -d "$team_dir" ] || continue
    name="$(basename "$team_dir")"
    ctl="$team_dir/.claude-plugin/ctl.json"
    if [ -f "$ctl" ]; then
      domain=$(python3 -c "import json; print(json.load(open('$ctl')).get('domain',''))" 2>/dev/null)
      if [ -n "$domain" ]; then _ok "team domain: $name → $domain"
      else _fail "team domain: $name" "missing 'domain' in ctl.json"; fi
    fi
  done
done

# Core auto-loading: resolve_core_plugins returns correct plugins per domain
_test_core_resolve() {
  local desc="$1" domain="$2" expect="$3"
  local result
  result=$(python3 -c "
from importlib.machinery import SourceFileLoader
ck = SourceFileLoader('ck', '$CLI').load_module()
plugins = ck.resolve_core_plugins('$domain')
print(' '.join(sorted(plugins)))
" 2>/dev/null)
  local ok=true
  for exp in $expect; do
    if ! echo "$result" | grep -qF "$exp"; then ok=false; break; fi
  done
  if $ok; then _ok "$desc"
  else _fail "$desc" "expected '$expect' in '$result'"; fi
}

_test_core_excludes() {
  local desc="$1" domain="$2" reject="$3"
  local result
  result=$(python3 -c "
from importlib.machinery import SourceFileLoader
ck = SourceFileLoader('ck', '$CLI').load_module()
plugins = ck.resolve_core_plugins('$domain')
print(' '.join(sorted(plugins)))
" 2>/dev/null)
  if echo "$result" | grep -qF "$reject"; then
    _fail "$desc" "'$reject' should NOT be in '$result'"
  else _ok "$desc"; fi
}

_test_core_resolve  "core resolve: universals load for backend"    "backend"  "core-git core-security"
_test_core_resolve  "core resolve: backend includes core-backend"  "backend"  "core-backend"
_test_core_resolve  "core resolve: frontend includes core-frontend" "frontend" "core-frontend"
_test_core_resolve  "core resolve: embedded includes core-embedded" "embedded" "core-embedded"
_test_core_excludes "core resolve: backend excludes core-frontend" "backend"  "core-frontend"
_test_core_excludes "core resolve: backend excludes core-embedded" "backend"  "core-embedded"
_test_core_excludes "core resolve: frontend excludes core-backend" "frontend" "core-backend"
_test_core_excludes "core resolve: embedded excludes core-frontend" "embedded" "core-frontend"

# List command shows core plugins grouped
expect_output "list shows core group"              "core" list

# ── error cases ───────────────────────────────────────────────────────────────
expect_error  "unknown flag exits non-zero"       --unknown-flag-xyz
expect_error  "--kit with no name exits non-zero" --kit
expect_error  "--kit nonexistent plugin fails"    --kit nonexistent-plugin-xyz-abc
expect_error  "--model with no value fails"       --kit embedded-zephyr-engineer --model

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ──────────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo "  Results: $PASS passed, 0 failed"
else
  echo "  Results: $PASS passed, $FAIL failed"
fi
echo ""

[ "$FAIL" -eq 0 ]

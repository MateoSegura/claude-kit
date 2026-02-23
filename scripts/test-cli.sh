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
expect_output "list shows a plugin"               "coding-embedded-zephyr" list
expect_output "list shows shortcut hint"          "claude-kit -k" list
expect_output "list shows plugin version"         "0." list

# ── validate ──────────────────────────────────────────────────────────────────
expect_exit   "validate --all exits 0"            0 validate --all
expect_exit   "validate <plugin> exits 0"         0 validate coding-embedded-zephyr-engineer
expect_exit   "validate --changed exits 0"        0 validate --changed
expect_error  "validate nonexistent plugin fails"   validate nonexistent-plugin-xyz-abc

# ── version ───────────────────────────────────────────────────────────────────
expect_exit   "version exits 0"                   0 version
expect_output "version shows tag format"          "v0." version

# ── error cases ───────────────────────────────────────────────────────────────
expect_error  "unknown flag exits non-zero"       --unknown-flag-xyz
expect_error  "--kit with no name exits non-zero" --kit
expect_error  "--kit nonexistent plugin fails"    --kit nonexistent-plugin-xyz-abc
expect_error  "--model with no value fails"       --kit coding-embedded-zephyr-engineer --model

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

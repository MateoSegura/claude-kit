#!/usr/bin/env bash
# resolve-active-spec.sh — Shared helper to resolve active spec directory.
# Source this script; do not invoke directly.
# Sets: SPEC_ROOT (root for all specs), ACTIVE_PLAN_DIR (active spec dir, or empty)

# Determine project root (git root or cwd fallback)
_project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Look up configured spec root from ~/.claude-kit/spec-registry.json
if command -v jq >/dev/null 2>&1 && [ -f ~/.claude-kit/spec-registry.json ]; then
  SPEC_ROOT=$(jq -r --arg p "$_project_root" \
    '.registrations[$p] // empty' \
    ~/.claude-kit/spec-registry.json 2>/dev/null) || true
else
  SPEC_ROOT=""
fi
[ -z "$SPEC_ROOT" ] && SPEC_ROOT="docs/specs"

ACTIVE_PLAN_DIR=""

if [ ! -f "${SPEC_ROOT}/.active" ]; then
  return 0 2>/dev/null || exit 0
fi

_active_name=$(cat "${SPEC_ROOT}/.active" 2>/dev/null)
if [ -z "$_active_name" ]; then
  return 0 2>/dev/null || exit 0
fi

ACTIVE_PLAN_DIR="${SPEC_ROOT}/${_active_name}"

if [ ! -d "$ACTIVE_PLAN_DIR" ]; then
  ACTIVE_PLAN_DIR=""
  return 0 2>/dev/null || exit 0
fi

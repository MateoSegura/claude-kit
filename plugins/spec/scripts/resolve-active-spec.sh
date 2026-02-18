#!/usr/bin/env bash
# resolve-active-spec.sh — Shared helper to resolve the active spec directory.
# Source this script; do not invoke directly. Sets ACTIVE_PLAN_DIR.

ACTIVE_PLAN_DIR=""

if [ ! -f "docs/specs/.active" ]; then
  return 0 2>/dev/null || exit 0
fi

_active_name=$(cat "docs/specs/.active" 2>/dev/null)
if [ -z "$_active_name" ]; then
  return 0 2>/dev/null || exit 0
fi

ACTIVE_PLAN_DIR="docs/specs/${_active_name}"

if [ ! -d "$ACTIVE_PLAN_DIR" ]; then
  ACTIVE_PLAN_DIR=""
  return 0 2>/dev/null || exit 0
fi

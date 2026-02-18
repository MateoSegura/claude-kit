#!/usr/bin/env bash
# resolve-active-plan.sh — Shared helper to resolve the active plan directory.
# Source this script; do not invoke directly. Sets ACTIVE_PLAN_DIR.

ACTIVE_PLAN_DIR=""

if [ ! -f "docs/plans/.active" ]; then
  return 0 2>/dev/null || exit 0
fi

_active_name=$(cat "docs/plans/.active" 2>/dev/null)
if [ -z "$_active_name" ]; then
  return 0 2>/dev/null || exit 0
fi

ACTIVE_PLAN_DIR="docs/plans/${_active_name}"

if [ ! -d "$ACTIVE_PLAN_DIR" ]; then
  ACTIVE_PLAN_DIR=""
  return 0 2>/dev/null || exit 0
fi

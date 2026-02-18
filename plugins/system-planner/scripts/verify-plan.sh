#!/usr/bin/env bash
set -euo pipefail
# verify-plan.sh — PreToolUse hook for Write|Edit
# Blocks source file edits if no active plan exists.
# Plan files, configs, docs, and dotfiles are always allowed.

# Source the shared helper to resolve active plan directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-plan.sh"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, allow (shouldn't happen for Write/Edit)
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Always allow: docs/plans directory files, dotfiles/configs, docs, markdown, json, yaml, toml
if echo "$FILE_PATH" | grep -qE '(^|/)docs/plans/|/\.claude|\.claude-plugin|CLAUDE\.md|\.md$|\.json$|\.ya?ml$|\.toml$|\.txt$|\.log$|\.sh$|\.conf$|\.cfg$|\.ini$|Makefile|CMakeLists|Kconfig|\.gitignore|\.editorconfig'; then
  exit 0
fi

# Check if active plan exists and has overview.md
if [ -z "$ACTIVE_PLAN_DIR" ] || [ ! -f "$ACTIVE_PLAN_DIR/overview.md" ]; then
  echo "BLOCKED: No active plan found in $(pwd)." >&2
  echo "[system-planner] Create a plan first with /system-planner:plan before editing source files." >&2
  echo "[system-planner] Allowed without plan: docs/plans/ files, configs (.json, .yaml, .toml), docs (.md), scripts (.sh)." >&2
  exit 2
fi

exit 0

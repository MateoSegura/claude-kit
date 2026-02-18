#!/usr/bin/env bash
set -euo pipefail
# verify-spec.sh — PreToolUse hook for Write|Edit
# Blocks NEW file creation if no active spec exists.
# Editing existing files is always allowed — this hook only gates new work.
# Spec files, configs, docs, and dotfiles are always allowed.

# Source the shared helper to resolve active spec directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-spec.sh"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, allow (shouldn't happen for Write/Edit)
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Always allow: spec directory files, dotfiles/configs, docs, markdown, json, yaml, toml, scripts
if echo "$FILE_PATH" | grep -qE '(^|/)docs/specs/|/\.claude|\.claude-plugin|CLAUDE\.md|\.md$|\.json$|\.ya?ml$|\.toml$|\.txt$|\.log$|\.sh$|\.conf$|\.cfg$|\.ini$|Makefile|CMakeLists|Kconfig|\.gitignore|\.editorconfig'; then
  exit 0
fi

# If the file already exists on disk, allow the edit freely
if [ -f "$FILE_PATH" ]; then
  exit 0
fi

# File does not exist — this is new file creation. Require an active spec.
if [ -z "$ACTIVE_PLAN_DIR" ] || [ ! -f "$ACTIVE_PLAN_DIR/overview.md" ]; then
  echo "BLOCKED: No active spec found in $(pwd)." >&2
  echo "[spec] Create a spec first with /spec:new before creating new source files." >&2
  echo "[spec] Editing existing files is always allowed." >&2
  echo "[spec] Allowed without spec: docs/specs/ files, configs (.json, .yaml, .toml), docs (.md), scripts (.sh)." >&2
  exit 2
fi

exit 0

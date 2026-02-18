#!/usr/bin/env bash
# check-plan-integrity.sh — PostToolUse hook for Write|Edit
# Validates spec file structure when spec directory files are written.
# Warns about status.log direct writes.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-spec.sh"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

# Only care about files under SPEC_ROOT
if [ -z "$FILE_PATH" ] || ! echo "$FILE_PATH" | grep -qF "${SPEC_ROOT}/"; then
  exit 0
fi

# Hard rule: status.log must only be written by hooks
if echo "$FILE_PATH" | grep -q 'status\.log$'; then
  echo "[spec] WARNING: status.log must only be written by hook scripts, not directly."
  exit 0
fi

# overview.md — check required sections
if echo "$FILE_PATH" | grep -q 'overview\.md$'; then
  missing=""
  for section in "## Context" "## Requirements" "## Acceptance Criteria" "## Goal" \
                 "## Architecture Decisions" "## Constraints" "## Phase Summary" "## Key Files"; do
    if ! grep -q "$section" "$FILE_PATH" 2>/dev/null; then
      missing="$missing $section,"
    fi
  done
  if [ -n "$missing" ]; then
    echo "[spec] Note: overview.md is missing sections:${missing%,}"
    echo "[spec] Add them before compaction — the recovery agent needs these sections."
  fi
fi

# phase-NN.md — check required sections
if echo "$FILE_PATH" | grep -qE 'phases/phase-[0-9]+\.md$'; then
  missing=""
  for section in "## Objective" "## Steps" "## Files to Create/Modify" "## Acceptance Criteria"; do
    if ! grep -q "$section" "$FILE_PATH" 2>/dev/null; then
      missing="$missing $section,"
    fi
  done
  if [ -n "$missing" ]; then
    echo "[spec] Note: phase file is missing sections:${missing%,}"
  fi
fi

exit 0

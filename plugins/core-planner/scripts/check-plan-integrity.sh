#!/usr/bin/env bash
# check-plan-integrity.sh — PostToolUse hook for Write|Edit
# Validates plan file structure when docs/plans/ files are written.
# Warns about status.log direct writes.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only care about files under docs/plans/
if ! echo "$FILE_PATH" | grep -q 'docs/plans/'; then
  exit 0
fi

# Hard rule: status.log must only be written by hooks
if echo "$FILE_PATH" | grep -q 'status\.log$'; then
  echo "[core-planner] WARNING: status.log must only be written by hook scripts, not directly."
  echo "[core-planner] This may indicate a non-negotiable rule violation."
  exit 0
fi

# overview.md — check required sections
if echo "$FILE_PATH" | grep -q 'overview\.md$'; then
  missing=""
  for section in "## Context" "## Goal" "## Architecture Decisions" "## Constraints" "## Phase Summary" "## Key Files"; do
    if ! grep -q "$section" "$FILE_PATH" 2>/dev/null; then
      missing="$missing $section,"
    fi
  done
  if [ -n "$missing" ]; then
    echo "[core-planner] overview.md missing sections:$missing"
    echo "[core-planner] The context-recovery agent requires these sections to restore state after compaction."
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
    echo "[core-planner] Phase file missing sections:$missing"
  fi
fi

exit 0

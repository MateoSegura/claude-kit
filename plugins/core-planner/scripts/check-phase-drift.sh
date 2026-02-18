#!/usr/bin/env bash
# check-phase-drift.sh — PostToolUse hook for Write|Edit
# Advisory drift detection: warns when an edit falls outside the current
# phase's declared scope. Does NOT block — the edit already happened.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Plan files are always in scope
if echo "$FILE_PATH" | grep -q 'docs/plans/'; then
  exit 0
fi

# No active plan — nothing to check against
if [ ! -f docs/plans/.active ]; then
  exit 0
fi

ACTIVE=$(cat docs/plans/.active 2>/dev/null)
if [ -z "$ACTIVE" ]; then
  exit 0
fi

# Find current phase number
PHASE_NUM_FILE="docs/plans/$ACTIVE/.current-phase"
if [ -f "$PHASE_NUM_FILE" ]; then
  PHASE_NUM=$(cat "$PHASE_NUM_FILE" | tr -d '[:space:]')
else
  # Infer from the lowest phase file with uncompleted steps
  PHASE_NUM=""
  for f in "docs/plans/$ACTIVE/phases"/phase-*.md; do
    [ -f "$f" ] || continue
    if grep -q '\- \[ \]' "$f" 2>/dev/null; then
      PHASE_NUM=$(basename "$f" | grep -o '[0-9]\+' | head -1 | sed 's/^0*//')
      break
    fi
  done
fi

if [ -z "$PHASE_NUM" ]; then
  exit 0
fi

PHASE_FILE=$(printf "docs/plans/%s/phases/phase-%02d.md" "$ACTIVE" "$PHASE_NUM")
if [ ! -f "$PHASE_FILE" ]; then
  exit 0
fi

# Check if the edited file appears anywhere in the phase file
BASENAME=$(basename "$FILE_PATH")
if grep -qF "$FILE_PATH" "$PHASE_FILE" 2>/dev/null || grep -qF "$BASENAME" "$PHASE_FILE" 2>/dev/null; then
  exit 0
fi

# Drift detected — advisory message only
TARGETS=$(grep -A30 "## Files to Create/Modify" "$PHASE_FILE" 2>/dev/null \
  | grep '^\s*[-*]' | head -8 | sed 's/^\s*[-*]\s*//' | tr '\n' ', ' | sed 's/, $//')

echo "[core-planner] Drift: '$FILE_PATH' is not in Phase ${PHASE_NUM}'s declared scope."
if [ -n "$TARGETS" ]; then
  echo "[core-planner] Phase ${PHASE_NUM} targets: $TARGETS"
fi
echo "[core-planner] If intentional: update the phase file to include this file, or acknowledge the scope change."

exit 0

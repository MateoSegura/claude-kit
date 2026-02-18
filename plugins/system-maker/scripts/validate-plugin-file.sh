#!/usr/bin/env bash
# validate-plugin-file.sh — PostToolUse hook for Write|Edit
# Validates plugin file frontmatter conventions.
# Only checks files that appear to be plugin components — exits immediately for all others.

INPUT=$(cat)

# Extract file_path without jq
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')
[ -z "$FILE_PATH" ] && exit 0

# Only validate plugin component files
case "$FILE_PATH" in
  */agents/*.md) TYPE="agent" ;;
  */commands/*.md) TYPE="command" ;;
  */skills/*/*.md) TYPE="skill" ;;
  */hooks/*.json|*/.claude-plugin/*.json) TYPE="json" ;;
  *) exit 0 ;;  # Not a plugin file — skip
esac

[ ! -f "$FILE_PATH" ] && exit 0

# JSON files: validate syntax
if [ "$TYPE" = "json" ]; then
  if command -v python3 >/dev/null 2>&1; then
    if ! python3 -m json.tool "$FILE_PATH" >/dev/null 2>&1; then
      echo "[system-maker] WARNING: $FILE_PATH is not valid JSON"
    fi
  fi
  exit 0
fi

# MD files: check frontmatter
FIRST_LINE=$(head -1 "$FILE_PATH" 2>/dev/null)
if [ "$FIRST_LINE" != "---" ]; then
  echo "[system-maker] WARNING: $FILE_PATH is missing frontmatter (should start with ---)"
  exit 0
fi

# Agent files must use 'tools:' not 'allowed-tools:'
if [ "$TYPE" = "agent" ]; then
  if head -20 "$FILE_PATH" | grep -q '^allowed-tools:'; then
    echo "[system-maker] WARNING: Agent file $FILE_PATH uses 'allowed-tools:' — should use 'tools:'"
  fi
fi

# Command/skill files must use 'allowed-tools:' not 'tools:'
if [ "$TYPE" = "command" ] || [ "$TYPE" = "skill" ]; then
  if head -20 "$FILE_PATH" | grep -q '^tools:'; then
    echo "[system-maker] WARNING: Command/skill file $FILE_PATH uses 'tools:' — should use 'allowed-tools:'"
  fi
fi

exit 0

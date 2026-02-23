#!/bin/bash
set -euo pipefail
# restrict-writes.sh — Restricts file writes to report output files only
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# The grader NEVER writes production code — only grading reports (.md, .json, .html)
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path was parsed, allow (may be a non-file Write variant)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Extract the file extension (lowercase)
EXTENSION="${FILE_PATH##*.}"
EXTENSION=$(echo "$EXTENSION" | tr '[:upper:]' '[:lower:]')

# Allow only report output file types
case "$EXTENSION" in
  md|json|html)
    # Permitted report formats — allow the write
    exit 0
    ;;
  svelte)
    echo "BLOCKED: The grader must not write .svelte source files. The grader only produces grading reports (.md, .json, .html). Show fix suggestions as code examples inside the report, not as file writes." >&2
    exit 2
    ;;
  ts|tsx)
    echo "BLOCKED: The grader must not write .ts/.tsx source files. The grader only produces grading reports (.md, .json, .html). Show fix suggestions as code examples inside the report, not as file writes." >&2
    exit 2
    ;;
  js|jsx)
    echo "BLOCKED: The grader must not write .js/.jsx source files. The grader only produces grading reports (.md, .json, .html). Show fix suggestions as code examples inside the report, not as file writes." >&2
    exit 2
    ;;
  css|scss|sass|less)
    echo "BLOCKED: The grader must not write stylesheet files (.css, .scss, etc.). The grader only produces grading reports (.md, .json, .html). Show fix suggestions as code examples inside the report, not as file writes." >&2
    exit 2
    ;;
  *)
    echo "BLOCKED: Writing .$EXTENSION files is not permitted for the grader. Only report output files are allowed: .md, .json, .html. File attempted: $FILE_PATH" >&2
    exit 2
    ;;
esac

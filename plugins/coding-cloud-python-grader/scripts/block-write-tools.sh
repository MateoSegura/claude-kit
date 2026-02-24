#!/bin/bash
set -euo pipefail
# block-write-tools.sh — HARD BLOCK all write and edit operations
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Requires: jq
#
# The coding-cloud-python-grader NEVER modifies source code or any file.
# It reads, analyses, and scores — it does not write.
# This is an unconditional, hard safety boundary. Exit 2 always.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "Write/Edit"')

echo "BLOCKED: The Python grader must not modify any files. Attempted ${TOOL_NAME} on: ${FILE_PATH}" >&2
echo "The grader role is strictly read-only. Use Bash with read-only analysis tools (mypy, ruff, grep, cat) to inspect code, then produce the grading report in your response text." >&2
exit 2

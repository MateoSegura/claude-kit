#!/bin/bash
set -euo pipefail

# Restrict file writes to report formats only (.md, .json, .html)
# Block writes to source/config files to prevent "fixing" code being graded
# Requires: jq

# Read the tool use event JSON from stdin
INPUT=$(cat)

# Extract the file path from Write or Edit tool arguments
FILE_PATH=$(echo "$INPUT" | jq -r '.arguments.file_path // ""')

# If no file path found, allow (shouldn't happen)
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Extract file extension
EXT="${FILE_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

# Allowed extensions for grading reports
ALLOWED_EXTS=("md" "json" "html" "txt")

# Check if extension is allowed
for ALLOWED in "${ALLOWED_EXTS[@]}"; do
    if [ "$EXT_LOWER" = "$ALLOWED" ]; then
        exit 0
    fi
done

# If we get here, extension is not allowed
echo "ERROR: Blocked write to file with extension .$EXT" >&2
echo "" >&2
echo "Grading agents may ONLY write report files:" >&2
echo "  - Markdown (.md)" >&2
echo "  - JSON (.json)" >&2
echo "  - HTML (.html)" >&2
echo "  - Text (.txt)" >&2
echo "" >&2
echo "Writing to source/config files is FORBIDDEN:" >&2
echo "  - C/C++ source (.c, .h, .cpp, .hpp)" >&2
echo "  - Configuration (.conf, .cmake, .yaml, .yml)" >&2
echo "  - Device tree (.dts, .dtsi, .overlay)" >&2
echo "  - Build files (CMakeLists.txt, Kconfig)" >&2
echo "" >&2
echo "Your role is to ASSESS code, not FIX it." >&2
echo "File attempted: $FILE_PATH" >&2
exit 2

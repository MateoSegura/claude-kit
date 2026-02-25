#!/usr/bin/env bash
# Check if any staging directories have uncommitted work before stopping.
# Called by the Stop hook to warn about potential lost work.

set -euo pipefail

STAGING_DIRS=$(ls -d /tmp/claude-kit-update-* 2>/dev/null || true)

if [ -z "$STAGING_DIRS" ]; then
  echo '{"ok": true}' >&2
  exit 0
fi

for dir in $STAGING_DIRS; do
  if [ -d "$dir" ]; then
    file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
      echo "{\"ok\": false, \"reason\": \"Staging directory $dir has $file_count file(s) not finalized to plugins/. Re-run the update workflow to finalize or remove with: rm -rf $dir\"}" >&2
      exit 2
    fi
  fi
done

echo '{"ok": true}' >&2
exit 0

#!/usr/bin/env bash
# Check if any staging directories have uncommitted work before stopping.
# Called by the Stop hook to warn about potential lost work.

STAGING_DIRS=$(ls -d /tmp/agent-config-update-* 2>/dev/null)

if [ -z "$STAGING_DIRS" ]; then
  exit 0
fi

for dir in $STAGING_DIRS; do
  if [ -d "$dir" ]; then
    file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
      echo "[system-updater] WARNING: Staging directory $dir has $file_count file(s)."
      echo "[system-updater] Changes have not been finalized back to plugins/."
      echo "[system-updater] Re-run the update workflow to finalize or discard."
    fi
  fi
done

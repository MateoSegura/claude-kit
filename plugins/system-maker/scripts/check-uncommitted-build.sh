#!/usr/bin/env bash
# Check if any build directories have uncommitted work before stopping.
# Called by the Stop hook to warn about potential lost work.
# NOTE: Build directory pattern /tmp/claude-kit-build-* matches the convention defined in commands/make-agent.md Phase 2

BUILD_DIRS=$(ls -d /tmp/claude-kit-build-* 2>/dev/null)

if [ -z "$BUILD_DIRS" ]; then
  exit 0
fi

for dir in $BUILD_DIRS; do
  if [ -d "$dir" ]; then
    file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
      echo "[system-maker] WARNING: Build directory $dir has $file_count file(s)." >&2
      echo "[system-maker] These files have not been finalized to plugins/." >&2
      echo "[system-maker] Run Phase 11 finalization or remove with: rm -rf $dir" >&2
      exit 2
    fi
  fi
done

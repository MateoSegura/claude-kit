#!/usr/bin/env bash
# Check if any build directories have uncommitted work before stopping.
# Called by the Stop hook to warn about potential lost work.
# NOTE: Build directory pattern /tmp/claude-kit-build-* matches the convention defined in commands/make-member.md Phase 2

set -euo pipefail

BUILD_DIRS=$(ls -d /tmp/claude-kit-build-* 2>/dev/null || true)

if [ -z "$BUILD_DIRS" ]; then
  echo '{"ok": true}' >&2
  exit 0
fi

for dir in $BUILD_DIRS; do
  if [ -d "$dir" ]; then
    file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
      echo "{\"ok\": false, \"reason\": \"Build directory $dir has $file_count file(s) not finalized to plugins/. Run Phase 10 finalization or remove with: rm -rf $dir\"}" >&2
      exit 2
    fi
  fi
done

echo '{"ok": true}' >&2
exit 0

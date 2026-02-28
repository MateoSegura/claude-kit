#!/usr/bin/env bash
# Validates the documentation site configuration for consistency.
# Checks: nav entries resolve to real files, no orphan pages, valid site.json.
#
# Usage:
#   bash qms/docs-site/validate-site.sh           # Full check
#   bash qms/docs-site/validate-site.sh --links   # Links only
#   bash qms/docs-site/validate-site.sh --nav     # Nav consistency only
#   bash qms/docs-site/validate-site.sh --orphans # Orphan detection only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MKDOCS_YML="$SCRIPT_DIR/mkdocs.yml"
SITE_JSON="$SCRIPT_DIR/site.json"

CHECK_NAV=false
CHECK_LINKS=false
CHECK_ORPHANS=false
CHECK_ALL=true

for arg in "$@"; do
  case "$arg" in
    --nav)     CHECK_NAV=true; CHECK_ALL=false ;;
    --links)   CHECK_LINKS=true; CHECK_ALL=false ;;
    --orphans) CHECK_ORPHANS=true; CHECK_ALL=false ;;
    *)         echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

if [ "$CHECK_ALL" = true ]; then
  CHECK_NAV=true
  CHECK_LINKS=true
  CHECK_ORPHANS=true
fi

errors=0
warnings=0

_err() { echo "  ERROR: $1"; ((errors++)) || true; }
_warn() { echo "  WARN:  $1"; ((warnings++)) || true; }
_ok()  { echo "  OK:    $1"; }

echo ""
echo "  Documentation Site Health Check"
echo "  ────────────────────────────────"
echo ""

# ── Build the source-to-content mapping ──────────────────────────────────────
# Nav entries reference files relative to docs_dir (.docs-build/), but source
# files live in docs/ and qms/. Map nav paths back to source paths.

_resolve_source() {
  local nav_path="$1"
  if [[ "$nav_path" == docs/* ]]; then
    echo "$REPO_ROOT/$nav_path"
  elif [[ "$nav_path" == processes/* ]]; then
    echo "$REPO_ROOT/qms/$nav_path"
  elif [[ "$nav_path" == mappings/* ]]; then
    echo "$REPO_ROOT/qms/$nav_path"
  elif [[ "$nav_path" == index.md ]]; then
    echo "$SCRIPT_DIR/index.md"
  else
    # Top-level files (CATALOG.md, etc.) come from qms/
    echo "$REPO_ROOT/qms/$nav_path"
  fi
}

# ── Check 1: Nav consistency ────────────────────────────────────────────────

if [ "$CHECK_NAV" = true ]; then
  echo "  [1/4] Nav consistency..."

  # Extract all file paths from nav (lines ending in .md)
  nav_files=$(grep -oP '[a-zA-Z0-9_./-]+\.md' "$MKDOCS_YML" | sort -u)
  missing=0
  found=0

  while IFS= read -r nav_path; do
    [ -z "$nav_path" ] && continue
    source_path=$(_resolve_source "$nav_path")
    if [ ! -f "$source_path" ]; then
      _err "nav entry points to missing file: $nav_path (expected: $source_path)"
      ((missing++)) || true
    else
      ((found++)) || true
    fi
  done <<< "$nav_files"

  if [ "$missing" -eq 0 ]; then
    _ok "$found nav entries resolve to existing files"
  fi

  # Check for duplicate nav entries
  dupes=$(echo "$nav_files" | sort | uniq -d)
  if [ -n "$dupes" ]; then
    while IFS= read -r dup; do
      _warn "duplicate nav entry: $dup"
    done <<< "$dupes"
  else
    _ok "no duplicate nav entries"
  fi

  echo ""
fi

# ── Check 2: Orphan detection ──────────────────────────────────────────────

if [ "$CHECK_ORPHANS" = true ]; then
  echo "  [2/4] Orphan detection..."

  # Collect all markdown files from source directories
  all_source_files=()
  while IFS= read -r f; do
    all_source_files+=("$f")
  done < <(find "$REPO_ROOT/docs" -name "*.md" -type f 2>/dev/null | sort)

  while IFS= read -r f; do
    all_source_files+=("$f")
  done < <(find "$REPO_ROOT/qms/processes" "$REPO_ROOT/qms/mappings" -name "*.md" -type f 2>/dev/null | sort)

  for f in "$REPO_ROOT/qms/CATALOG.md" "$REPO_ROOT/qms/VERSION-POLICY.md" "$REPO_ROOT/qms/MATURITY-MODEL.md"; do
    [ -f "$f" ] && all_source_files+=("$f")
  done

  nav_files_set=$(grep -oP '[a-zA-Z0-9_./-]+\.md' "$MKDOCS_YML" | sort -u)
  orphans=0

  for source_file in "${all_source_files[@]}"; do
    # Convert source path to nav path
    rel="${source_file#"$REPO_ROOT/"}"
    if [[ "$rel" == qms/processes/* ]]; then
      nav_path="${rel#qms/}"
    elif [[ "$rel" == qms/mappings/* ]]; then
      nav_path="${rel#qms/}"
    elif [[ "$rel" == qms/*.md ]]; then
      nav_path="$(basename "$rel")"
    else
      nav_path="$rel"
    fi

    if ! echo "$nav_files_set" | grep -qF "$nav_path"; then
      _warn "orphan page (not in nav): $rel"
      ((orphans++)) || true
    fi
  done

  if [ "$orphans" -eq 0 ]; then
    _ok "no orphan pages detected"
  else
    _warn "$orphans orphan page(s) found — consider adding to nav"
  fi

  echo ""
fi

# ── Check 3: Internal link validation ──────────────────────────────────────

if [ "$CHECK_LINKS" = true ]; then
  echo "  [3/4] Internal link validation..."

  # Check markdown cross-references (REQ-XXX, ADR-XXX, etc.) in docs/
  broken_refs=0
  checked_refs=0

  while IFS= read -r source_file; do
    [ -z "$source_file" ] && continue
    # Look for cross-reference patterns like "REQ-001", "ADR-003", "QA-005"
    refs=$(grep -oP '\b(REQ|ADR|QA|PROC-[A-Z]+|TEST|INC|BM|REG|SPEC|MIG|RB)-\d{3}\b' "$source_file" 2>/dev/null | sort -u || true)
    [ -z "$refs" ] && continue

    while IFS= read -r ref; do
      [ -z "$ref" ] && continue
      ((checked_refs++)) || true
      # Search for a file containing this ID in its name
      match=$(find "$REPO_ROOT/docs" "$REPO_ROOT/qms/processes" -name "*${ref}*" -type f 2>/dev/null | head -1)
      if [ -z "$match" ]; then
        _warn "unresolved cross-reference: $ref in $(basename "$source_file")"
        ((broken_refs++)) || true
      fi
    done <<< "$refs"
  done < <(find "$REPO_ROOT/docs" -name "*.md" -type f 2>/dev/null)

  if [ "$broken_refs" -eq 0 ]; then
    _ok "$checked_refs cross-references validated"
  fi

  echo ""
fi

# ── Check 4: site.json validation ──────────────────────────────────────────

echo "  [4/4] Site metadata..."

if [ ! -f "$SITE_JSON" ]; then
  _err "site.json not found at $SITE_JSON"
else
  # Validate JSON syntax
  if ! jq empty "$SITE_JSON" 2>/dev/null; then
    _err "site.json is not valid JSON"
  else
    version=$(jq -r '.version' "$SITE_JSON")
    build_number=$(jq -r '.buildNumber' "$SITE_JSON")

    # Validate semver format
    if ! echo "$version" | grep -qP '^\d+\.\d+\.\d+$'; then
      _err "site.json version '$version' is not valid semver"
    else
      _ok "site.json version: $version (build $build_number)"
    fi
  fi
fi

echo ""

# ── Summary ──────────────────────────────────────────────────────────────────

echo "  ────────────────────────────────"
if [ "$errors" -gt 0 ]; then
  echo "  RESULT: FAILED — $errors error(s), $warnings warning(s)"
  exit 1
elif [ "$warnings" -gt 0 ]; then
  echo "  RESULT: PASSED with $warnings warning(s)"
  exit 0
else
  echo "  RESULT: PASSED — all checks clean"
  exit 0
fi

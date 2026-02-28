#!/usr/bin/env bash
# Docs structure validation — catches missing INDEX files, duplicate IDs,
# filename/ID mismatches, broken cross-references, and missing Traces sections.
# Runs as part of fast-validate on every push. Pure bash, no Claude needed.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_DIR="$ROOT/docs"
PASS=0
FAIL=0
WARN=0

_ok()   { echo "  PASS  $1"; PASS=$((PASS + 1)); }
_warn() { echo "  WARN  $1"; echo "        $2"; WARN=$((WARN + 1)); }
_fail() { echo "  FAIL  $1"; echo "        $2"; FAIL=$((FAIL + 1)); }

echo ""
echo "  Docs structure validation"
echo "  ──────────────────────────────────────"
echo ""

# ── Check 1: INDEX.md exists in each top-level docs subdirectory ─────────────
echo "  Checking INDEX.md presence..."
index_ok=true
for subdir in "$DOCS_DIR"/*/; do
  [ -d "$subdir" ] || continue
  name="$(basename "$subdir")"
  if [ -f "$subdir/INDEX.md" ]; then
    _ok "$name: INDEX.md present"
  else
    _fail "$name: INDEX.md present" "missing INDEX.md in docs/$name/"
    index_ok=false
  fi
done
if [ "$index_ok" = true ]; then
  _ok "all top-level docs subdirectories have INDEX.md"
fi

# ── Collect all document files with ID prefixes ─────────────────────────────
# Map each ID prefix to its expected directory
declare -A prefix_to_dir=(
  ["REQ"]="requirements"
  ["ADR"]="architecture/decisions"
  ["SPEC"]="specs"
  ["TEST"]="testing/evidence"
  ["REG"]="testing/regression"
  ["BM"]="benchmarks"
  ["INC"]="operations/incidents"
  ["RB"]="operations/runbooks"
  ["MIG"]="operations/migration"
  ["QA"]="constraints"
)

# Reverse map: directory to expected prefix
declare -A dir_to_prefix=(
  ["requirements"]="REQ"
  ["architecture/decisions"]="ADR"
  ["specs"]="SPEC"
  ["testing/evidence"]="TEST"
  ["testing/regression"]="REG"
  ["benchmarks"]="BM"
  ["operations/incidents"]="INC"
  ["operations/runbooks"]="RB"
  ["operations/migration"]="MIG"
  ["constraints"]="QA"
)

# Collect all ID-prefixed files
declare -A seen_ids  # id -> filepath
id_files=()

for prefix in "${!prefix_to_dir[@]}"; do
  dir="${prefix_to_dir[$prefix]}"
  full_dir="$DOCS_DIR/$dir"
  [ -d "$full_dir" ] || continue
  for f in "$full_dir"/${prefix}-*.md; do
    [ -f "$f" ] || continue
    id_files+=("$f")
  done
done

# Also scan for misplaced ID files in wrong directories
for dir in "${!dir_to_prefix[@]}"; do
  full_dir="$DOCS_DIR/$dir"
  [ -d "$full_dir" ] || continue
  for f in "$full_dir"/*.md; do
    [ -f "$f" ] || continue
    basename_f="$(basename "$f")"
    # Skip INDEX.md and non-ID files
    [[ "$basename_f" == "INDEX.md" ]] && continue
    # Check if it matches ANY known prefix pattern
    if echo "$basename_f" | grep -qP '^(REQ|ADR|SPEC|TEST|REG|BM|INC|RB|MIG|QA)-\d{3}'; then
      # Already in id_files if prefix matches dir, otherwise it'll be caught by check 3
      :
    fi
  done
done

# Skip checks 2-6 if no documents exist yet
if [ ${#id_files[@]} -eq 0 ]; then
  echo ""
  echo "  No ID-prefixed documents found — skipping ID, reference, and content checks."
  echo ""
  echo "  ──────────────────────────────────────"
  echo "  Results: $PASS passed, $WARN warned, $FAIL failed"
  echo ""
  [ "$FAIL" -eq 0 ]
  exit $?
fi

# ── Check 2: Document IDs are globally unique ────────────────────────────────
echo ""
echo "  Checking ID uniqueness..."
for f in "${id_files[@]}"; do
  basename_f="$(basename "$f")"
  # Extract ID: everything before the second hyphen-separated segment
  doc_id=$(echo "$basename_f" | grep -oP '^[A-Z]+-\d{3}')
  if [ -z "$doc_id" ]; then
    continue
  fi
  if [ -n "${seen_ids[$doc_id]+x}" ]; then
    _fail "ID uniqueness" "$doc_id used by both ${seen_ids[$doc_id]} and $f"
  else
    seen_ids["$doc_id"]="$f"
  fi
done
if [ "$FAIL" -eq 0 ]; then
  _ok "all document IDs are unique"
fi

# ── Check 3: Filenames match their directory's ID pattern ────────────────────
echo ""
echo "  Checking filename/directory consistency..."
for dir in "${!dir_to_prefix[@]}"; do
  full_dir="$DOCS_DIR/$dir"
  expected_prefix="${dir_to_prefix[$dir]}"
  [ -d "$full_dir" ] || continue
  for f in "$full_dir"/*.md; do
    [ -f "$f" ] || continue
    basename_f="$(basename "$f")"
    [[ "$basename_f" == "INDEX.md" ]] && continue
    # Check that the file starts with the expected prefix
    if ! echo "$basename_f" | grep -qP "^${expected_prefix}-\d{3}-"; then
      _fail "filename pattern: $dir/$basename_f" "expected ${expected_prefix}-XXX-<description>.md"
    fi
  done
done
_ok "filename/directory consistency"

# ── Check 4: Cross-references resolve to real files ──────────────────────────
echo ""
echo "  Checking cross-reference resolution..."
# Build a set of all known IDs
for f in "${id_files[@]}"; do
  basename_f="$(basename "$f")"
  doc_id=$(echo "$basename_f" | grep -oP '^[A-Z]+-\d{3}')
  [ -n "$doc_id" ] && seen_ids["$doc_id"]="$f"
done

# Scan all doc files for references to ID patterns
ref_pattern='(REQ|ADR|SPEC|TEST|REG|BM|INC|RB|MIG|QA)-[0-9]{3}'
for f in "${id_files[@]}"; do
  basename_f="$(basename "$f")"
  own_id=$(echo "$basename_f" | grep -oP '^[A-Z]+-\d{3}')
  # Extract all ID references from the file body (skip frontmatter-like lines)
  refs=$(grep -oP "$ref_pattern" "$f" 2>/dev/null | sort -u)
  for ref in $refs; do
    # Skip self-references
    [ "$ref" = "$own_id" ] && continue
    if [ -z "${seen_ids[$ref]+x}" ]; then
      _warn "cross-ref in $(basename "$f")" "$ref referenced but no matching file found"
    fi
  done
done
_ok "cross-reference check complete"

# ── Check 5: Status field contains valid value ───────────────────────────────
echo ""
echo "  Checking status field validity..."

declare -A valid_statuses=(
  ["REQ"]="draft|active|deprecated|superseded-by"
  ["ADR"]="proposed|accepted|superseded-by|rejected"
  ["SPEC"]="draft|active|completed|abandoned"
  ["TEST"]="pass|fail|partial"
  ["REG"]="open|fixed|wont-fix"
  ["BM"]="active|superseded-by|retired"
  ["INC"]="investigating|resolved|post-mortem-complete"
  ["RB"]="active|deprecated|superseded-by"
  ["MIG"]="draft|active|completed"
  ["QA"]="draft|active|deferred|deprecated"
)

for f in "${id_files[@]}"; do
  basename_f="$(basename "$f")"
  prefix=$(echo "$basename_f" | grep -oP '^[A-Z]+')
  [ -n "$prefix" ] || continue
  allowed="${valid_statuses[$prefix]:-}"
  [ -n "$allowed" ] || continue

  # Extract Status field value
  status_val=$(grep -iP '^\*\*Status:\*\*\s+' "$f" 2>/dev/null | head -1 | sed 's/.*\*\*Status:\*\*\s*//' | xargs)
  if [ -z "$status_val" ]; then
    _warn "status: $basename_f" "no **Status:** field found"
    continue
  fi

  # Check if the status value starts with one of the valid values
  status_base=$(echo "$status_val" | grep -oP '^[a-z-]+')
  if ! echo "$status_base" | grep -qP "^($allowed)$"; then
    _warn "status: $basename_f" "status '$status_val' not in valid set ($allowed)"
  fi
done
_ok "status field check complete"

# ── Check 6: Documents contain required Traces section ───────────────────────
echo ""
echo "  Checking Traces section presence..."
for f in "${id_files[@]}"; do
  basename_f="$(basename "$f")"
  if ! grep -qP '^##\s+Traces' "$f" 2>/dev/null; then
    _warn "traces: $basename_f" "missing '## Traces' section"
  fi
done
_ok "traces section check complete"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "  ──────────────────────────────────────"
echo "  Results: $PASS passed, $WARN warned, $FAIL failed"
echo ""

[ "$FAIL" -eq 0 ]

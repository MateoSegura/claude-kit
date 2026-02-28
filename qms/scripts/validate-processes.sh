#!/usr/bin/env bash
# Process framework validation — checks process document structure, versioning,
# cross-references, artifact mappings, and maturity consistency.
# Runs as Layer 5 of the test cascade. Pure bash, no Claude needed.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
QMS_DIR="$ROOT/qms"
DOCS_DIR="$ROOT/docs"
PASS=0
FAIL=0
WARN=0

_ok()   { echo "  PASS  $1"; PASS=$((PASS + 1)); }
_warn() { echo "  WARN  $1"; echo "        $2"; WARN=$((WARN + 1)); }
_fail() { echo "  FAIL  $1"; echo "        $2"; FAIL=$((FAIL + 1)); }

echo ""
echo "  Process framework validation"
echo "  ──────────────────────────────────────"
echo ""

# ── Check 1: CATALOG.md exists ──────────────────────────────────────────────
echo "  Checking CATALOG.md presence..."
if [ -f "$QMS_DIR/CATALOG.md" ]; then
  _ok "CATALOG.md present"
else
  _fail "CATALOG.md present" "missing qms/CATALOG.md"
fi

# ── Collect all process files ───────────────────────────────────────────────
proc_files=()
for f in "$QMS_DIR"/processes/base/lifecycle/PROC-LC-*.md \
         "$QMS_DIR"/processes/base/support/PROC-SP-*.md \
         "$QMS_DIR"/processes/base/organizational/PROC-ORG-*.md \
         "$QMS_DIR"/processes/base/security/PROC-SEC-*.md \
         "$QMS_DIR"/processes/gov/compliance/PROC-GOV-*.md \
         "$QMS_DIR"/processes/gov/audit/PROC-GOV-*.md \
         "$QMS_DIR"/processes/gov/deployment/PROC-GOV-*.md; do
  [ -f "$f" ] && proc_files+=("$f")
done

if [ ${#proc_files[@]} -eq 0 ]; then
  echo ""
  echo "  No process documents found — skipping structural checks."
  echo ""
  echo "  ──────────────────────────────────────"
  echo "  Results: $PASS passed, $WARN warned, $FAIL failed"
  echo ""
  [ "$FAIL" -eq 0 ]
  exit $?
fi

echo "  Found ${#proc_files[@]} process documents"
echo ""

# ── Check 2: All 15 required sections present ──────────────────────────────
echo "  Checking required sections..."
required_sections=(
  "## 1. Purpose"
  "## 2. Scope"
  "## 3. Entry Criteria"
  "## 4. Inputs"
  "## 5. Activities"
  "## 6. Outputs / Artifacts"
  "## 7. Exit Criteria"
  "## 8. Quality Gates"
  "## 9. Roles and Responsibilities"
  "## 10. Metrics"
  "## 11. Standards Alignment"
  "## 12. Tailoring Guidance"
  "## 13. Related Processes"
  "## 14. Traces"
  "## 15. Change History"
)

for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  for section in "${required_sections[@]}"; do
    if ! grep -qF "$section" "$f" 2>/dev/null; then
      _fail "sections: $basename_f" "missing '$section'"
    fi
  done
done
_ok "required sections check complete"

# ── Check 3: Version fields are valid semver ────────────────────────────────
echo ""
echo "  Checking version fields..."
for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  version_val=$(grep -oP '^\*\*Version:\*\*\s+\K[0-9]+\.[0-9]+\.[0-9]+' "$f" 2>/dev/null | head -1)
  if [ -z "$version_val" ]; then
    _fail "version: $basename_f" "no valid **Version:** field found (expected semver X.Y.Z)"
  fi
done
_ok "version field check complete"

# ── Check 4: Status fields are valid ────────────────────────────────────────
echo ""
echo "  Checking status fields..."
valid_statuses="draft|active|deprecated|superseded-by"
for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  status_val=$(grep -iP '^\*\*Status:\*\*\s+' "$f" 2>/dev/null | head -1 | sed 's/.*\*\*Status:\*\*\s*//' | xargs)
  if [ -z "$status_val" ]; then
    _warn "status: $basename_f" "no **Status:** field found"
    continue
  fi
  status_base=$(echo "$status_val" | grep -oP '^[a-z-]+')
  if ! echo "$status_base" | grep -qP "^($valid_statuses)$"; then
    _warn "status: $basename_f" "status '$status_val' not in valid set ($valid_statuses)"
  fi
done
_ok "status field check complete"

# ── Check 5: Artifact mappings reference real docs/ paths ───────────────────
echo ""
echo "  Checking artifact directory references..."
for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  # Extract docs/ paths from Section 6 tables
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    # Skip glob patterns (e.g., docs/*/)
    [[ "$ref" == *'*'* ]] && continue
    full_path="$ROOT/$ref"
    if [ ! -d "$full_path" ]; then
      _warn "artifact path: $basename_f" "references $ref/ but directory does not exist"
    fi
  done < <(grep -oP '`docs/[^`]+/`' "$f" 2>/dev/null | sed 's/`//g' | sed 's|/$||')
done
_ok "artifact directory check complete"

# ── Check 6: Cross-references between processes resolve ────────────────────
echo ""
echo "  Checking process cross-references..."
# Build set of known process IDs
declare -A known_procs
for f in "${proc_files[@]}"; do
  proc_id=$(basename "$f" .md)
  known_procs["$proc_id"]=1
done

for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  # Find PROC-* references in the file
  refs=$(grep -oP 'PROC-[A-Z]+-\d{3}' "$f" 2>/dev/null | sort -u)
  own_id=$(basename "$f" .md)
  for ref in $refs; do
    [ "$ref" = "$own_id" ] && continue
    if [ -z "${known_procs[$ref]+x}" ]; then
      _warn "cross-ref: $basename_f" "references $ref but no matching process file found"
    fi
  done
done
_ok "process cross-reference check complete"

# ── Check 7: Every docs/ subdirectory is governed ──────────────────────────
echo ""
echo "  Checking governance coverage..."
for subdir in "$DOCS_DIR"/*/; do
  [ -d "$subdir" ] || continue
  name="$(basename "$subdir")"
  index="$subdir/INDEX.md"
  if [ -f "$index" ]; then
    if grep -qP '^\*\*Governing Process(es)?:\*\*' "$index" 2>/dev/null; then
      _ok "governance: $name has governing process"
    else
      _warn "governance: $name" "INDEX.md missing **Governing Process:** field"
    fi
  fi
done

# ── Check 8: Gov processes reference base prerequisites ─────────────────────
echo ""
echo "  Checking gov overlay references..."
for f in "$QMS_DIR"/processes/gov/compliance/PROC-GOV-*.md \
         "$QMS_DIR"/processes/gov/audit/PROC-GOV-*.md \
         "$QMS_DIR"/processes/gov/deployment/PROC-GOV-*.md; do
  [ -f "$f" ] || continue
  basename_f="$(basename "$f")"
  # Gov processes should reference at least one base process
  if ! grep -qP 'PROC-(LC|SP|ORG|SEC)-\d{3}' "$f" 2>/dev/null; then
    _warn "gov-refs: $basename_f" "government overlay process does not reference any base process"
  fi
done
_ok "gov overlay reference check complete"

# ── Check 9: Maturity consistency ───────────────────────────────────────────
echo ""
echo "  Checking maturity consistency..."
for f in "${proc_files[@]}"; do
  basename_f="$(basename "$f")"
  maturity=$(grep -iP '^\*\*Maturity:\*\*\s+' "$f" 2>/dev/null | head -1 | sed 's/.*\*\*Maturity:\*\*\s*//' | xargs)
  [ -z "$maturity" ] && continue

  case "$maturity" in
    defined|measured|optimizing)
      # Check that Metrics section has content beyond template placeholder
      metrics_content=$(sed -n '/^## 10\. Metrics/,/^## 11\./p' "$f" 2>/dev/null | grep -v '^##' | grep -v '^$' | grep -v '<' | head -1)
      if [ -z "$metrics_content" ]; then
        _warn "maturity: $basename_f" "maturity '$maturity' but Metrics section appears empty"
      fi
      ;;
  esac
done
_ok "maturity consistency check complete"

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "  ──────────────────────────────────────"
echo "  Results: $PASS passed, $WARN warned, $FAIL failed"
echo "  Processes checked: ${#proc_files[@]}"
echo ""

[ "$FAIL" -eq 0 ]

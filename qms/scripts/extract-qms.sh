#!/usr/bin/env bash
# QMS Customer Package Extraction
# Produces a customer-deliverable directory with process summaries,
# standards mappings, and evidence references.
#
# Usage:
#   bash qms/scripts/extract-qms.sh base              # Commercial package
#   bash qms/scripts/extract-qms.sh gov                # Full government package
#   bash qms/scripts/extract-qms.sh gov --standard cmmc    # CMMC-focused
#   bash qms/scripts/extract-qms.sh gov --standard fedramp # FedRAMP-focused

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
QMS_DIR="$ROOT/qms"
DOCS_DIR="$ROOT/docs"

# ── Parse arguments ──────────────────────────────────────────────────────────
FLAVOR="${1:-base}"
STANDARD=""

shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --standard) STANDARD="$2"; shift 2 ;;
    *)          echo "Unknown flag: $1"; exit 1 ;;
  esac
done

DATE="$(date +%Y-%m-%d)"
OUTPUT_DIR="$ROOT/claude-kit-qms-${FLAVOR}-${DATE}"

if [ -n "$STANDARD" ]; then
  OUTPUT_DIR="$ROOT/claude-kit-qms-${FLAVOR}-${STANDARD}-${DATE}"
fi

echo ""
echo "  QMS Customer Package Extraction"
echo "  ──────────────────────────────────────"
echo "  Flavor: $FLAVOR"
[ -n "$STANDARD" ] && echo "  Standard: $STANDARD"
echo "  Output: $OUTPUT_DIR"
echo ""

# ── Create output structure ──────────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"/{01-process-framework,02-standards-alignment,03-customer-integration,04-evidence,05-architecture-overview}

# ── 01: Process Framework ────────────────────────────────────────────────────
echo "  Extracting process framework..."

# Always include base processes
for dir in lifecycle support organizational security; do
  src="$QMS_DIR/processes/base/$dir"
  [ -d "$src" ] || continue
  for f in "$src"/PROC-*.md; do
    [ -f "$f" ] || continue
    cp "$f" "$OUTPUT_DIR/01-process-framework/"
  done
done

# Include gov processes if flavor is gov
if [ "$FLAVOR" = "gov" ]; then
  for dir in compliance audit deployment; do
    src="$QMS_DIR/processes/gov/$dir"
    [ -d "$src" ] || continue
    for f in "$src"/PROC-*.md; do
      [ -f "$f" ] || continue

      # If a specific standard is requested, filter by relevance
      if [ -n "$STANDARD" ]; then
        case "$STANDARD" in
          cmmc)
            grep -qiP 'CMMC|800-171|NIST SP 800-171|CUI' "$f" || continue
            ;;
          fedramp)
            grep -qiP 'FedRAMP|800-53|NIST SP 800-53|ATO' "$f" || continue
            ;;
        esac
      fi

      cp "$f" "$OUTPUT_DIR/01-process-framework/"
    done
  done
fi

# Copy framework meta documents
cp "$QMS_DIR/CATALOG.md" "$OUTPUT_DIR/01-process-framework/"
cp "$QMS_DIR/VERSION-POLICY.md" "$OUTPUT_DIR/01-process-framework/"
cp "$QMS_DIR/MATURITY-MODEL.md" "$OUTPUT_DIR/01-process-framework/"

# ── 02: Standards Alignment ──────────────────────────────────────────────────
echo "  Extracting standards alignment..."

# Always include base mappings
for f in "$QMS_DIR"/mappings/iso-12207.md "$QMS_DIR"/mappings/cmmi.md "$QMS_DIR"/mappings/nist-800-218.md; do
  [ -f "$f" ] && cp "$f" "$OUTPUT_DIR/02-standards-alignment/"
done

# Include gov mappings if flavor is gov
if [ "$FLAVOR" = "gov" ]; then
  for f in "$QMS_DIR"/mappings/nist-800-171.md "$QMS_DIR"/mappings/nist-ai-rmf.md; do
    [ -f "$f" ] && cp "$f" "$OUTPUT_DIR/02-standards-alignment/"
  done
fi

# ── 03: Customer Integration ─────────────────────────────────────────────────
echo "  Extracting customer integration docs..."

# Copy compliance customer packages if they exist
if [ -d "$DOCS_DIR/compliance/customer-packages" ]; then
  for f in "$DOCS_DIR/compliance/customer-packages"/*.md; do
    [ -f "$f" ] && [ "$(basename "$f")" != "INDEX.md" ] && cp "$f" "$OUTPUT_DIR/03-customer-integration/"
  done
fi

# ── 04: Evidence ─────────────────────────────────────────────────────────────
echo "  Extracting evidence overview..."

# Copy quality attribute summaries (public-safe portions)
if [ -d "$DOCS_DIR/quality" ]; then
  for f in "$DOCS_DIR/quality"/QA-*.md; do
    [ -f "$f" ] && cp "$f" "$OUTPUT_DIR/04-evidence/"
  done
fi

# ── 05: Architecture Overview ────────────────────────────────────────────────
echo "  Extracting architecture overview..."

if [ -d "$DOCS_DIR/architecture/components" ]; then
  for f in "$DOCS_DIR/architecture/components"/*.md; do
    [ -f "$f" ] && [ "$(basename "$f")" != "INDEX.md" ] && cp "$f" "$OUTPUT_DIR/05-architecture-overview/"
  done
fi

# ── Generate README ──────────────────────────────────────────────────────────
cat > "$OUTPUT_DIR/README.md" << READMEEOF
# claude-kit QMS Package — ${FLAVOR^} $([ -n "$STANDARD" ] && echo "($STANDARD)")

Generated: $DATE

## Contents

| Directory | Description |
|-----------|-------------|
| 01-process-framework/ | Process definitions, catalog, versioning, maturity |
| 02-standards-alignment/ | ISO 12207, CMMI, NIST standard mappings |
| 03-customer-integration/ | Shared responsibility and deployment guides |
| 04-evidence/ | Quality attributes and compliance evidence |
| 05-architecture-overview/ | Product architecture (public-safe) |

## Process Framework

This package contains the Process Asset Library (PAL) — a structured set of
software lifecycle, support, organizational, and security processes. Each
process follows a 15-section template and carries its own semantic version.

## Questions

For questions about this package, contact the development team.
READMEEOF

# ── Summary ──────────────────────────────────────────────────────────────────
proc_count=$(find "$OUTPUT_DIR/01-process-framework" -name "PROC-*.md" 2>/dev/null | wc -l)
mapping_count=$(find "$OUTPUT_DIR/02-standards-alignment" -name "*.md" 2>/dev/null | wc -l)

echo ""
echo "  ──────────────────────────────────────"
echo "  Package created: $OUTPUT_DIR"
echo "  Processes included: $proc_count"
echo "  Standards mappings: $mapping_count"
echo ""

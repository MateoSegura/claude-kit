#!/usr/bin/env bash
# Launches a local MkDocs development server with hot-reload.
# Content is merged from docs/ and qms/ into .docs-build/, then served.
#
# Usage:
#   bash qms/docs-site/serve.sh              # Default: port 8000
#   bash qms/docs-site/serve.sh --port 8080  # Custom port

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/.docs-build"
SITE_JSON="$SCRIPT_DIR/site.json"
MKDOCS_YML="$SCRIPT_DIR/mkdocs.yml"

PORT=8000
for arg in "$@"; do
  case "$arg" in
    --port)  shift; PORT="$1" ;;
    [0-9]*)  PORT="$arg" ;;
    *)       ;;
  esac
done

echo "[docs] Preparing content merge for dev server..."

# Merge content (same as build.sh but without --prod)
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

[ -d "$REPO_ROOT/docs" ] && cp -r "$REPO_ROOT/docs" "$BUILD_DIR/docs"
[ -d "$REPO_ROOT/qms/processes" ] && cp -r "$REPO_ROOT/qms/processes" "$BUILD_DIR/processes"
[ -d "$REPO_ROOT/qms/mappings" ] && cp -r "$REPO_ROOT/qms/mappings" "$BUILD_DIR/mappings"

for f in CATALOG.md VERSION-POLICY.md MATURITY-MODEL.md; do
  [ -f "$REPO_ROOT/qms/$f" ] && cp "$REPO_ROOT/qms/$f" "$BUILD_DIR/$f"
done

[ -f "$SCRIPT_DIR/index.md" ] && cp "$SCRIPT_DIR/index.md" "$BUILD_DIR/index.md"
[ -d "$SCRIPT_DIR/stylesheets" ] && cp -r "$SCRIPT_DIR/stylesheets" "$BUILD_DIR/stylesheets"

# Inject runtime settings into mkdocs config
site_version=$(jq -r '.version' "$SITE_JSON")
build_number=$(jq -r '.buildNumber' "$SITE_JSON")

MKDOCS_BUILD="$SCRIPT_DIR/.build-mkdocs.yml"
cp "$MKDOCS_YML" "$MKDOCS_BUILD"

cat >> "$MKDOCS_BUILD" << EOF

# ── Build-time settings (injected by serve.sh) ──
docs_dir: ${BUILD_DIR}
site_dir: ${SCRIPT_DIR}/site
extra:
  site_version: "${site_version}"
  build_number: ${build_number}
EOF

sed -i "s|custom_dir: overrides|custom_dir: ${SCRIPT_DIR}/overrides|" "$MKDOCS_BUILD"

echo "[docs] Starting development server on http://localhost:${PORT}"
echo "[docs] NOTE: Hot-reload watches .docs-build/ — to pick up new files in"
echo "       docs/ or qms/, restart the server (Ctrl+C then re-run)."
echo ""

mkdocs serve -f "$MKDOCS_BUILD" --dev-addr "0.0.0.0:${PORT}"

#!/usr/bin/env bash
# Builds the documentation site by merging content from docs/ and qms/ into
# a temporary .docs-build/ directory, then running mkdocs build.
#
# Usage:
#   bash qms/docs-site/build.sh --dev    # Dev build (no version bump)
#   bash qms/docs-site/build.sh --prod   # Production build (bumps build number)
#   bash qms/docs-site/build.sh --clean  # Remove build artifacts only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/.docs-build"
SITE_JSON="$SCRIPT_DIR/site.json"
MKDOCS_YML="$SCRIPT_DIR/mkdocs.yml"

MODE="dev"
for arg in "$@"; do
  case "$arg" in
    --prod)  MODE="prod" ;;
    --dev)   MODE="dev" ;;
    --clean)
      echo "[docs] Cleaning build artifacts..."
      rm -rf "$BUILD_DIR" "$SCRIPT_DIR/site" "$SCRIPT_DIR/.build-mkdocs.yml"
      echo "[docs] Clean complete."
      exit 0
      ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

echo "[docs] Building documentation site (mode: $MODE)"
echo ""

# ── Step 1: Create merged content directory ──────────────────────────────────

echo "[docs] Step 1: Merging content sources..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy docs/ tree (project artifacts)
if [ -d "$REPO_ROOT/docs" ]; then
  cp -r "$REPO_ROOT/docs" "$BUILD_DIR/docs"
  echo "  copied docs/ → .docs-build/docs/"
fi

# Copy process documents
if [ -d "$REPO_ROOT/qms/processes" ]; then
  cp -r "$REPO_ROOT/qms/processes" "$BUILD_DIR/processes"
  echo "  copied qms/processes/ → .docs-build/processes/"
fi

# Copy standards mappings
if [ -d "$REPO_ROOT/qms/mappings" ]; then
  cp -r "$REPO_ROOT/qms/mappings" "$BUILD_DIR/mappings"
  echo "  copied qms/mappings/ → .docs-build/mappings/"
fi

# Copy top-level QMS documents
for f in CATALOG.md VERSION-POLICY.md MATURITY-MODEL.md; do
  if [ -f "$REPO_ROOT/qms/$f" ]; then
    cp "$REPO_ROOT/qms/$f" "$BUILD_DIR/$f"
    echo "  copied qms/$f → .docs-build/$f"
  fi
done

# Copy landing page
if [ -f "$SCRIPT_DIR/index.md" ]; then
  cp "$SCRIPT_DIR/index.md" "$BUILD_DIR/index.md"
  echo "  copied index.md → .docs-build/index.md"
fi

# Copy stylesheets and overrides into the build directory
if [ -d "$SCRIPT_DIR/stylesheets" ]; then
  cp -r "$SCRIPT_DIR/stylesheets" "$BUILD_DIR/stylesheets"
  echo "  copied stylesheets/ → .docs-build/stylesheets/"
fi

echo ""

# ── Step 2: Inject site version into mkdocs extra config ────────────────────

site_version=$(jq -r '.version' "$SITE_JSON")
build_number=$(jq -r '.buildNumber' "$SITE_JSON")

# For production builds, increment build number before rendering so the
# footer displays the correct value
if [ "$MODE" = "prod" ]; then
  build_number=$((build_number + 1))
fi

# Create a temporary mkdocs config OUTSIDE docs_dir to avoid MkDocs constraint
# that docs_dir must not be the parent of the config file
MKDOCS_BUILD="$SCRIPT_DIR/.build-mkdocs.yml"
cp "$MKDOCS_YML" "$MKDOCS_BUILD"

# Append runtime settings
cat >> "$MKDOCS_BUILD" << EOF

# ── Build-time settings (injected by build.sh) ──
docs_dir: ${BUILD_DIR}
site_dir: ${SCRIPT_DIR}/site
extra:
  site_version: "${site_version}"
  build_number: ${build_number}
EOF

# Point custom_dir to the absolute path for overrides
sed -i "s|custom_dir: overrides|custom_dir: ${SCRIPT_DIR}/overrides|" "$MKDOCS_BUILD"

echo "[docs] Step 2: Building with MkDocs Material..."

# ── Step 3: Run mkdocs build ────────────────────────────────────────────────

mkdocs build -f "$MKDOCS_BUILD" 2>&1 | while IFS= read -r line; do
  echo "  $line"
done

build_exit=${PIPESTATUS[0]}
if [ "$build_exit" -ne 0 ]; then
  echo ""
  echo "[docs] BUILD FAILED (exit $build_exit)"
  exit 1
fi

echo ""

# ── Step 4: Update site.json (production only) ──────────────────────────────

if [ "$MODE" = "prod" ]; then
  echo "[docs] Step 3: Updating site metadata..."

  # build_number was already incremented before mkdocs build (Step 2)
  new_build="$build_number"

  # Read old hash before computing new one
  old_hash=$(jq -r '.contentHash // "none"' "$SITE_JSON" 2>/dev/null || echo "none")

  # Compute content hash from all source markdown
  content_hash=$(find "$REPO_ROOT/docs" "$REPO_ROOT/qms" -name "*.md" -type f 2>/dev/null \
    | sort \
    | xargs cat 2>/dev/null \
    | sha256sum \
    | awk '{print "sha256:" $1}')

  # Count output pages
  page_count=$(find "$SCRIPT_DIR/site" -name "*.html" -type f 2>/dev/null | wc -l)

  # Compute site size
  site_size=$(du -sh "$SCRIPT_DIR/site" 2>/dev/null | awk '{print $1}')

  # Get mkdocs version
  mkdocs_version=$(python3 -c "import mkdocs; print(mkdocs.__version__)" 2>/dev/null || echo "unknown")

  # Update site.json
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  tmp=$(mktemp)
  jq \
    --argjson buildNumber "$new_build" \
    --arg lastBuild "$timestamp" \
    --arg contentHash "$content_hash" \
    --argjson pageCount "$page_count" \
    --arg siteSize "$site_size" \
    --arg mkdocsVersion "$mkdocs_version" \
    '.buildNumber = $buildNumber |
     .lastBuild = $lastBuild |
     .contentHash = $contentHash |
     .pageCount = $pageCount |
     .siteSize = $siteSize |
     .mkdocsVersion = $mkdocsVersion' \
    "$SITE_JSON" > "$tmp" && mv "$tmp" "$SITE_JSON"

  echo "  buildNumber: $new_build"
  echo "  contentHash: $content_hash"
  echo "  pageCount:   $page_count"
  echo "  siteSize:    $site_size"

  # Check if content actually changed
  if [ "$content_hash" = "$old_hash" ] && [ "$old_hash" != "none" ]; then
    echo "  NOTE: Content hash unchanged — no content changes since last build"
  fi

  echo ""
fi

# ── Summary ─────────────────────────────────────────────────────────────────

echo "[docs] Build complete."
echo "  Site: $SCRIPT_DIR/site/"
echo "  Version: $site_version"
if [ "$MODE" = "prod" ]; then
  echo "  Build: $new_build"
fi
echo ""

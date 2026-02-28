#!/usr/bin/env bash
# QMS Process Asset Library installer
# Instruments any repository with process governance rules, hooks, and commands.
# Run from the target repository's root directory.
#
# Usage:
#   bash qms/install.sh              # Install base instrumentation
#   bash qms/install.sh --scaffold   # Also create docs/ directory structure
#   bash qms/install.sh --gov        # Include government overlay
#   bash qms/install.sh --dry-run    # Show what would be installed
#   bash qms/install.sh --force      # Overwrite existing QMS files (upgrade)
#   bash qms/install.sh --update     # Smart update: preserve customizations
#   bash qms/install.sh --docs       # Install docs site commands and hooks
#   bash qms/install.sh --uninstall  # Remove all QMS-installed files
#
# Versioning:
#   Three version dimensions are tracked:
#   - coreVersion:  QMS framework version (bumped by QMS maintainers)
#   - userRevision: User's customization revision (bumped by user via qms-revision)
#   - process versions: Each PROC-*.md has its own semver (in the document header)

set -euo pipefail

QMS_CORE_VERSION="1.0.0"

# ── Resolve paths ────────────────────────────────────────────────────────────
QMS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(pwd)"
CLAUDE_DIR="$REPO_ROOT/.claude"
MANIFEST="$CLAUDE_DIR/qms-manifest.json"
BACKUP_DIR="$REPO_ROOT/.qms-backup"

# ── Parse flags ──────────────────────────────────────────────────────────────
SCAFFOLD=false
GOV=false
DRY_RUN=false
FORCE=false
UPDATE=false
UNINSTALL=false
DOCS=false

for arg in "$@"; do
  case "$arg" in
    --scaffold)  SCAFFOLD=true ;;
    --gov)       GOV=true ;;
    --dry-run)   DRY_RUN=true ;;
    --force)     FORCE=true ;;
    --update)    UPDATE=true ;;
    --uninstall) UNINSTALL=true ;;
    --docs)      DOCS=true ;;
    *)           echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────
installed_files=()
backed_up_files=()

_log()  { echo "  [qms] $1"; }
_skip() { echo "  [qms] SKIP  $1 (already exists)"; }
_dry()  { echo "  [qms] WOULD $1"; }
_back() { echo "  [qms] BACKUP $1"; }

_is_customized() {
  local file="$1"
  # Check if file has a user-modified marker
  grep -q '<!-- qms-user-modified -->' "$file" 2>/dev/null
}

_install_file() {
  local src="$1"
  local dst="$2"
  local dst_dir
  dst_dir="$(dirname "$dst")"

  if [ "$DRY_RUN" = true ]; then
    _dry "install $dst"
    return
  fi

  if [ -f "$dst" ]; then
    if [ "$UPDATE" = true ] && _is_customized "$dst"; then
      # Backup customized file, don't overwrite
      mkdir -p "$BACKUP_DIR"
      cp "$dst" "$BACKUP_DIR/$(basename "$dst").$(date +%s)"
      _back "$dst (customized — backed up, not overwritten)"
      backed_up_files+=("$dst")
      return
    fi

    if [ "$FORCE" = false ] && [ "$UPDATE" = false ]; then
      _skip "$dst"
      return
    fi
  fi

  mkdir -p "$dst_dir"
  cp "$src" "$dst"
  _log "installed $dst"
  installed_files+=("$dst")
}

# ── Uninstall ────────────────────────────────────────────────────────────────
if [ "$UNINSTALL" = true ]; then
  if [ ! -f "$MANIFEST" ]; then
    echo "  [qms] No manifest found at $MANIFEST — nothing to uninstall."
    exit 0
  fi

  _log "Uninstalling QMS instrumentation..."
  while IFS= read -r file; do
    if [[ "$file" == *":merged" ]]; then
      # Remove QMS hooks from merged hooks.json
      hooks_file="${file%:merged}"
      if [ -f "$hooks_file" ]; then
        tmp=$(mktemp)
        # Remove any hook entries with "source": "qms" or "qms-docs"
        jq '
          .hooks |= (to_entries | map(
            .value |= [.[] | select(
              (.hooks | all(.source != "qms" and .source != "qms-docs"))
            )]
          ) | from_entries)
        ' "$hooks_file" > "$tmp" && mv "$tmp" "$hooks_file"
        _log "removed QMS hooks from $hooks_file"
      fi
      continue
    fi
    if [ -f "$file" ]; then
      rm "$file"
      _log "removed $file"
    fi
  done < <(jq -r '.files[]' "$MANIFEST" 2>/dev/null)

  # Clean up empty skill directories left behind
  find "$CLAUDE_DIR/skills/" -maxdepth 1 -name "qms-*" -type d -empty -delete 2>/dev/null || true

  rm "$MANIFEST"
  _log "removed manifest"
  _log "Uninstall complete."
  exit 0
fi

# ── Update mode: check for existing installation ────────────────────────────
if [ "$UPDATE" = true ]; then
  if [ ! -f "$MANIFEST" ]; then
    _log "No existing installation found. Running fresh install instead."
    UPDATE=false
  else
    installed_version=$(jq -r '.coreVersion // .version // "unknown"' "$MANIFEST")
    user_revision=$(jq -r '.userRevision // 0' "$MANIFEST")
    _log "Updating from core $installed_version (user revision $user_revision) → $QMS_CORE_VERSION"

    if [ "$installed_version" = "$QMS_CORE_VERSION" ]; then
      _log "Already at core version $QMS_CORE_VERSION — nothing to update."
      _log "Use --force to overwrite files anyway."
      exit 0
    fi
  fi
fi

# ── Step 1: Detect environment ───────────────────────────────────────────────
echo ""
echo "  QMS Process Asset Library — Installer"
echo "  ──────────────────────────────────────"
if [ "$UPDATE" = true ]; then
  echo "  Mode: UPDATE (preserving customizations)"
else
  echo "  Mode: INSTALL"
fi
echo "  Core version: $QMS_CORE_VERSION"
echo ""

if [ "$DRY_RUN" = true ]; then
  _log "DRY RUN — no files will be written"
  echo ""
fi

if [ ! -d "$CLAUDE_DIR" ]; then
  if [ "$DRY_RUN" = true ]; then
    _dry "create $CLAUDE_DIR/"
  else
    mkdir -p "$CLAUDE_DIR"
    _log "created $CLAUDE_DIR/"
  fi
fi

# ── Step 2: Install rules ───────────────────────────────────────────────────
_log "Installing rules..."
for src in "$QMS_DIR"/instrumentation/rules/*.md; do
  [ -f "$src" ] || continue
  name="$(basename "$src")"
  dst="$CLAUDE_DIR/rules/qms-${name}"
  _install_file "$src" "$dst"
done

# ── Step 3: Merge hooks ─────────────────────────────────────────────────────
_log "Merging hooks..."
HOOKS_SRC="$QMS_DIR/instrumentation/hooks.json"
HOOKS_DST="$CLAUDE_DIR/hooks.json"

if [ "$DRY_RUN" = true ]; then
  _dry "merge hooks from $HOOKS_SRC into $HOOKS_DST"
elif [ -f "$HOOKS_SRC" ]; then
  if [ ! -f "$HOOKS_DST" ]; then
    cp "$HOOKS_SRC" "$HOOKS_DST"
    _log "created $HOOKS_DST"
    installed_files+=("$HOOKS_DST")
  else
    # Merge QMS hooks into existing hooks.json using the nested event-key format:
    #   .hooks.PreToolUse[] and .hooks.PostToolUse[] are arrays of matcher groups
    #   Each matcher group has: { "matcher": "...", "hooks": [...] }
    #   Each inner hook has: { "type": "...", "description": "...", ... }
    #
    # Strategy: for each event type, for each QMS matcher group, check if a hook
    # with the same description already exists anywhere in that event type. If not,
    # append the matcher group. If yes, skip (or replace on --update/--force).

    # Collect all existing hook descriptions across all event types
    # Format: .hooks.<EventType>[].hooks[].description
    existing_descriptions=$(jq -r '
      [.hooks | to_entries[]? | .value[]? | .hooks[]? | .description? // empty]
      | unique[]' "$HOOKS_DST" 2>/dev/null || true)

    for event_type in PreToolUse PostToolUse; do
      # Get QMS matcher groups for this event type
      qms_groups=$(jq -c ".hooks.${event_type}[]?" "$HOOKS_SRC" 2>/dev/null)
      [ -z "$qms_groups" ] && continue

      while IFS= read -r group; do
        [ -z "$group" ] && continue
        desc=$(echo "$group" | jq -r '.hooks[0].description // empty')
        [ -z "$desc" ] && continue

        if echo "$existing_descriptions" | grep -qF "$desc"; then
          if [ "$UPDATE" = true ] || [ "$FORCE" = true ]; then
            # Remove old entry with same description, then append new one
            tmp=$(mktemp)
            jq --arg et "$event_type" --arg desc "$desc" --argjson group "$group" '
              .hooks[$et] = [.hooks[$et][]? | select(.hooks | all(.description != $desc))] + [$group]
            ' "$HOOKS_DST" > "$tmp" && mv "$tmp" "$HOOKS_DST"
            _log "updated hook: $desc"
          else
            _skip "hook: $desc"
          fi
        else
          # Append new matcher group to the event type array
          tmp=$(mktemp)
          jq --arg et "$event_type" --argjson group "$group" '
            .hooks[$et] = (.hooks[$et] // []) + [$group]
          ' "$HOOKS_DST" > "$tmp" && mv "$tmp" "$HOOKS_DST"
          _log "merged hook: $desc"
        fi
      done <<< "$qms_groups"
    done
    installed_files+=("$HOOKS_DST:merged")
  fi
fi

# ── Step 4: Install commands ─────────────────────────────────────────────────
_log "Installing commands..."
mkdir -p "$CLAUDE_DIR/commands"
for src in "$QMS_DIR"/instrumentation/commands/*.md; do
  [ -f "$src" ] || continue
  name="$(basename "$src")"
  dst="$CLAUDE_DIR/commands/qms-${name}"
  _install_file "$src" "$dst"
done

# ── Step 5: Install skills ──────────────────────────────────────────────────
_log "Installing skills..."
for skill_dir in "$QMS_DIR"/instrumentation/skills/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  dst_dir="$CLAUDE_DIR/skills/qms-${skill_name}"
  if [ "$DRY_RUN" = true ]; then
    _dry "install skill $skill_name"
  else
    mkdir -p "$dst_dir"
    for src in "$skill_dir"/*; do
      [ -f "$src" ] || continue
      _install_file "$src" "$dst_dir/$(basename "$src")"
    done
  fi
done

# ── Step 6: Docs site instrumentation (optional) ────────────────────────────
if [ "$DOCS" = true ]; then
  _log "Installing docs site instrumentation..."

  # Install docs-specific commands
  for cmd_name in docs-serve docs-build docs-deploy docs-add-page docs-health; do
    src="$QMS_DIR/instrumentation/commands/${cmd_name}.md"
    if [ -f "$src" ]; then
      dst="$CLAUDE_DIR/commands/qms-${cmd_name}.md"
      _install_file "$src" "$dst"
    fi
  done

  # Install docs-site rule
  src="$QMS_DIR/instrumentation/rules/docs-site.md"
  if [ -f "$src" ]; then
    dst="$CLAUDE_DIR/rules/qms-docs-site.md"
    _install_file "$src" "$dst"
  fi

  # Initialize site.json if it doesn't exist
  site_json="$QMS_DIR/docs-site/site.json"
  if [ "$DRY_RUN" = true ]; then
    _dry "check site.json at $site_json"
  elif [ ! -f "$site_json" ]; then
    mkdir -p "$(dirname "$site_json")"
    cat > "$site_json" << 'SJEOF'
{
  "version": "0.1.0",
  "buildNumber": 0,
  "lastBuild": null,
  "contentHash": null,
  "pageCount": 0,
  "siteSize": null,
  "mkdocsVersion": null,
  "changelog": [
    {
      "version": "0.1.0",
      "date": "2026-02-28",
      "summary": "Initial docs site with MkDocs Material"
    }
  ]
}
SJEOF
    _log "initialized $site_json"
  fi

  # Add .docs-build/ and site/ to .gitignore if not present
  gitignore="$REPO_ROOT/.gitignore"
  if [ "$DRY_RUN" = true ]; then
    _dry "update .gitignore with docs build paths"
  elif [ -f "$gitignore" ]; then
    for pattern in ".docs-build/" "qms/docs-site/site/"; do
      if ! grep -qF "$pattern" "$gitignore"; then
        echo "$pattern" >> "$gitignore"
        _log "added $pattern to .gitignore"
      fi
    done
  fi

  _log "Docs site instrumentation installed."
  _log "  Commands: qms-docs-serve, qms-docs-build, qms-docs-deploy,"
  _log "            qms-docs-add-page, qms-docs-health"
  _log "  Rule: qms-docs-site.md"
  echo ""
fi

# ── Step 7: Scaffold docs/ (optional) ───────────────────────────────────────
if [ "$SCAFFOLD" = true ]; then
  _log "Scaffolding docs/ directory structure..."
  docs_dirs=(
    "docs/research"
    "docs/requirements"
    "docs/architecture/decisions"
    "docs/architecture/components"
    "docs/specs"
    "docs/quality"
    "docs/testing/evidence"
    "docs/testing/regression"
    "docs/benchmarks"
    "docs/operations/incidents"
    "docs/operations/runbooks"
    "docs/operations/migration"
    "docs/methodology"
  )

  if [ "$GOV" = true ]; then
    docs_dirs+=(
      "docs/compliance/control-mappings"
      "docs/compliance/customer-packages"
    )
  fi

  for dir in "${docs_dirs[@]}"; do
    full="$REPO_ROOT/$dir"
    if [ "$DRY_RUN" = true ]; then
      _dry "create $dir/"
    elif [ ! -d "$full" ]; then
      mkdir -p "$full"
      _log "created $dir/"
    fi
  done
fi

# ── Step 8: Write manifest ──────────────────────────────────────────────────
if [ "$DRY_RUN" = false ]; then
  _log "Writing manifest..."
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  # Preserve userRevision on update
  if [ "$UPDATE" = true ] && [ -f "$MANIFEST" ]; then
    user_revision=$(jq -r '.userRevision // 0' "$MANIFEST")
    customized_files=$(jq -c '.customized // []' "$MANIFEST")
  else
    user_revision=0
    customized_files="[]"
  fi

  # Add any newly backed-up files to the customized list
  for f in "${backed_up_files[@]}"; do
    customized_files=$(echo "$customized_files" | jq --arg f "$f" 'if . | index($f) then . else . + [$f] end')
  done

  files_json="[]"
  for f in "${installed_files[@]}"; do
    files_json=$(echo "$files_json" | jq --arg f "$f" '. += [$f]')
  done

  jq -n \
    --arg coreVersion "$QMS_CORE_VERSION" \
    --argjson userRevision "$user_revision" \
    --arg installedAt "$([ "$UPDATE" = true ] && jq -r '.installedAt // empty' "$MANIFEST" 2>/dev/null || echo "$timestamp")" \
    --arg updatedAt "$timestamp" \
    --arg source "$QMS_DIR" \
    --argjson files "$files_json" \
    --argjson customized "$customized_files" \
    --argjson gov "$GOV" \
    --argjson docs "$DOCS" \
    '{
      coreVersion: $coreVersion,
      userRevision: $userRevision,
      installedAt: $installedAt,
      updatedAt: $updatedAt,
      source: $source,
      gov: $gov,
      docs: $docs,
      files: $files,
      customized: $customized
    }' \
    > "$MANIFEST"
  _log "wrote $MANIFEST"
fi

# ── Step 9: Validate ────────────────────────────────────────────────────────
if [ "$DRY_RUN" = false ]; then
  echo ""
  _log "Running validation..."
  if bash "$QMS_DIR/scripts/validate-processes.sh" 2>&1; then
    _log "Validation PASSED"
  else
    _log "Validation FAILED — check output above"
  fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
if [ "$UPDATE" = true ] && [ ${#backed_up_files[@]} -gt 0 ]; then
  _log "Customized files preserved (not overwritten):"
  for f in "${backed_up_files[@]}"; do
    echo "        $f"
  done
  _log "Backups saved to: $BACKUP_DIR/"
  echo ""
fi
_log "Installation complete. Core version: $QMS_CORE_VERSION"
echo ""

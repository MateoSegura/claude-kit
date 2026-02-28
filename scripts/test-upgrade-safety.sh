#!/usr/bin/env bash
# Upgrade safety checker — compares plugin API surface between two git refs.
# Deterministic (no Claude). Uses git show/git ls-tree (no checkout needed).
#
# Exit codes: 0=clean, 1=breaking changes, 2=cautionary-only
#
# Usage:
#   test-upgrade-safety.sh [--from <ref>] [--to <ref>] [--json] [--ci]
#     --from   Base ref (default: latest tag)
#     --to     Target ref (default: HEAD)
#     --json   Output JSON instead of human-readable text
#     --ci     CI mode: cautionary changes exit 0 (warnings only)

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Parse arguments ──────────────────────────────────────────────────────────

FROM_REF=""
TO_REF="HEAD"
JSON_MODE=false
CI_MODE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM_REF="$2"; shift 2 ;;
    --to)   TO_REF="$2"; shift 2 ;;
    --json) JSON_MODE=true; shift ;;
    --ci)   CI_MODE=true; shift ;;
    *)      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Default --from to latest tag
if [ -z "$FROM_REF" ]; then
  FROM_REF=$(git -C "$ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -z "$FROM_REF" ]; then
    echo "No tags found and --from not specified. Nothing to compare." >&2
    exit 0
  fi
fi

# Resolve refs to full SHAs for reliability
FROM_SHA=$(git -C "$ROOT" rev-parse "$FROM_REF" 2>/dev/null)
TO_SHA=$(git -C "$ROOT" rev-parse "$TO_REF" 2>/dev/null)

if [ -z "$FROM_SHA" ] || [ -z "$TO_SHA" ]; then
  echo "ERROR: Could not resolve refs: --from=$FROM_REF --to=$TO_REF" >&2
  exit 1
fi

if [ "$FROM_SHA" = "$TO_SHA" ]; then
  if $JSON_MODE; then
    echo '{"from":"'"$FROM_REF"'","to":"'"$TO_REF"'","breaking":[],"cautionary":[],"safe":[],"exit_code":0}'
  else
    echo "  Upgrade safety: no changes (same ref)"
  fi
  exit 0
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

BREAKING=()
CAUTIONARY=()
SAFE=()

_breaking()    { BREAKING+=("$1"); }
_cautionary()  { CAUTIONARY+=("$1"); }
_safe()        { SAFE+=("$1"); }

# List plugin directories at a given ref
_list_plugins() {
  local ref="$1"
  git -C "$ROOT" ls-tree --name-only "$ref" -- plugins/ 2>/dev/null \
    | sed 's|plugins/||' | sort
}

# List files in a plugin subdirectory at a given ref
_list_files() {
  local ref="$1" plugin="$2" subdir="$3"
  git -C "$ROOT" ls-tree --name-only "$ref" -- "plugins/$plugin/$subdir/" 2>/dev/null \
    | sed "s|plugins/$plugin/$subdir/||" | sort
}

# List skill directory names at a given ref
_list_skill_dirs() {
  local ref="$1" plugin="$2"
  git -C "$ROOT" ls-tree --name-only "$ref" -- "plugins/$plugin/skills/" 2>/dev/null \
    | sed "s|plugins/$plugin/skills/||" | sort
}

# Read a file at a given ref
_show_file() {
  local ref="$1" path="$2"
  git -C "$ROOT" show "$ref:$path" 2>/dev/null
}

# Extract a frontmatter field from markdown content (stdin)
_extract_field() {
  local field="$1"
  awk -v f="$field" '
    /^---$/ { n++; next }
    n == 1 && $0 ~ "^"f":" { sub("^"f":[ ]*", ""); print; exit }
  '
}

# Extract the name: field from a SKILL.md at a given ref
_skill_name() {
  local ref="$1" plugin="$2" skill="$3"
  _show_file "$ref" "plugins/$plugin/skills/$skill/SKILL.md" | _extract_field "name"
}

# Extract agent frontmatter fields
_agent_field() {
  local ref="$1" plugin="$2" agent="$3" field="$4"
  _show_file "$ref" "plugins/$plugin/agents/$agent" | _extract_field "$field"
}

# Parse hooks.json and output a normalized summary
_hooks_summary() {
  local ref="$1" plugin="$2"
  local content
  content=$(_show_file "$ref" "plugins/$plugin/hooks/hooks.json") || return
  echo "$content" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    hooks = data.get('hooks', data)
    for event, entries in sorted(hooks.items()):
        for entry in entries:
            matcher = entry.get('matcher', '*')
            for h in entry.get('hooks', []):
                htype = h.get('type', 'unknown')
                print(f'{event}/{matcher}:{htype}')
except Exception:
    pass
" 2>/dev/null | sort
}

# Parse companions from ctl.json
_companions() {
  local ref="$1" plugin="$2"
  local content
  content=$(_show_file "$ref" "plugins/$plugin/.claude-plugin/ctl.json") || return
  echo "$content" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for c in d.get('companions', []):
        print(c)
except Exception:
    pass
" 2>/dev/null | sort
}

# ── Collect plugin lists ─────────────────────────────────────────────────────

FROM_PLUGINS=$(_list_plugins "$FROM_SHA")
TO_PLUGINS=$(_list_plugins "$TO_SHA")

# ── Check plugin existence ───────────────────────────────────────────────────

# Deleted plugins = BREAKING
while IFS= read -r plugin; do
  [ -z "$plugin" ] && continue
  if ! echo "$TO_PLUGINS" | grep -qx "$plugin"; then
    _breaking "plugin-deleted: $plugin"
  fi
done <<< "$FROM_PLUGINS"

# New plugins = SAFE
while IFS= read -r plugin; do
  [ -z "$plugin" ] && continue
  if ! echo "$FROM_PLUGINS" | grep -qx "$plugin"; then
    _safe "plugin-added: $plugin"
  fi
done <<< "$TO_PLUGINS"

# Plugins in both refs — check API surface changes
COMMON_PLUGINS=$(comm -12 <(echo "$FROM_PLUGINS") <(echo "$TO_PLUGINS"))

while IFS= read -r plugin; do
  [ -z "$plugin" ] && continue

  # ── Commands ─────────────────────────────────────────────────────────────
  from_cmds=$(_list_files "$FROM_SHA" "$plugin" "commands")
  to_cmds=$(_list_files "$TO_SHA" "$plugin" "commands")

  # Deleted commands = BREAKING
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    if ! echo "$to_cmds" | grep -qx "$cmd"; then
      _breaking "command-deleted: $plugin/$cmd"
    fi
  done <<< "$from_cmds"

  # New commands = SAFE
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    if ! echo "$from_cmds" | grep -qx "$cmd"; then
      _safe "command-added: $plugin/$cmd"
    fi
  done <<< "$to_cmds"

  # ── Agents ───────────────────────────────────────────────────────────────
  from_agents=$(_list_files "$FROM_SHA" "$plugin" "agents")
  to_agents=$(_list_files "$TO_SHA" "$plugin" "agents")

  # Deleted agents = BREAKING
  while IFS= read -r agent; do
    [ -z "$agent" ] && continue
    if ! echo "$to_agents" | grep -qx "$agent"; then
      _breaking "agent-deleted: $plugin/$agent"
    fi
  done <<< "$from_agents"

  # New agents = SAFE
  while IFS= read -r agent; do
    [ -z "$agent" ] && continue
    if ! echo "$from_agents" | grep -qx "$agent"; then
      _safe "agent-added: $plugin/$agent"
    fi
  done <<< "$to_agents"

  # Common agents — check frontmatter changes
  common_agents=$(comm -12 <(echo "$from_agents") <(echo "$to_agents") 2>/dev/null)
  while IFS= read -r agent; do
    [ -z "$agent" ] && continue

    # Tools reduced = CAUTIONARY
    from_tools=$(_agent_field "$FROM_SHA" "$plugin" "$agent" "tools")
    to_tools=$(_agent_field "$TO_SHA" "$plugin" "$agent" "tools")
    if [ -n "$from_tools" ] && [ -n "$to_tools" ] && [ "$from_tools" != "$to_tools" ]; then
      # Count tools (comma-separated)
      from_count=$(echo "$from_tools" | tr ',' '\n' | wc -l)
      to_count=$(echo "$to_tools" | tr ',' '\n' | wc -l)
      if [ "$to_count" -lt "$from_count" ]; then
        _cautionary "agent-tools-reduced: $plugin/$agent ($from_tools -> $to_tools)"
      else
        _safe "agent-tools-changed: $plugin/$agent"
      fi
    fi

    # permissionMode changed = CAUTIONARY
    from_pm=$(_agent_field "$FROM_SHA" "$plugin" "$agent" "permissionMode")
    to_pm=$(_agent_field "$TO_SHA" "$plugin" "$agent" "permissionMode")
    if [ -n "$from_pm" ] && [ -n "$to_pm" ] && [ "$from_pm" != "$to_pm" ]; then
      _cautionary "agent-permission-changed: $plugin/$agent ($from_pm -> $to_pm)"
    fi

    # Skills list reduced = CAUTIONARY
    from_skills=$(_agent_field "$FROM_SHA" "$plugin" "$agent" "skills")
    to_skills=$(_agent_field "$TO_SHA" "$plugin" "$agent" "skills")
    if [ -n "$from_skills" ] && [ -n "$to_skills" ] && [ "$from_skills" != "$to_skills" ]; then
      from_scount=$(echo "$from_skills" | tr ',' '\n' | wc -l)
      to_scount=$(echo "$to_skills" | tr ',' '\n' | wc -l)
      if [ "$to_scount" -lt "$from_scount" ]; then
        _cautionary "agent-skills-reduced: $plugin/$agent"
      fi
    fi

    # Description changed = informational (SAFE)
    from_desc=$(_agent_field "$FROM_SHA" "$plugin" "$agent" "description")
    to_desc=$(_agent_field "$TO_SHA" "$plugin" "$agent" "description")
    if [ -n "$from_desc" ] && [ -n "$to_desc" ] && [ "$from_desc" != "$to_desc" ]; then
      _safe "agent-description-changed: $plugin/$agent"
    fi
  done <<< "$common_agents"

  # ── Skills ───────────────────────────────────────────────────────────────
  from_skills=$(_list_skill_dirs "$FROM_SHA" "$plugin")
  to_skills=$(_list_skill_dirs "$TO_SHA" "$plugin")

  # Deleted skill directories = BREAKING
  while IFS= read -r skill; do
    [ -z "$skill" ] && continue
    if ! echo "$to_skills" | grep -qx "$skill"; then
      _breaking "skill-deleted: $plugin/$skill"
    fi
  done <<< "$from_skills"

  # New skill directories = SAFE
  while IFS= read -r skill; do
    [ -z "$skill" ] && continue
    if ! echo "$from_skills" | grep -qx "$skill"; then
      _safe "skill-added: $plugin/$skill"
    fi
  done <<< "$to_skills"

  # Common skills — check name: field change
  common_skills=$(comm -12 <(echo "$from_skills") <(echo "$to_skills") 2>/dev/null)
  while IFS= read -r skill; do
    [ -z "$skill" ] && continue
    from_name=$(_skill_name "$FROM_SHA" "$plugin" "$skill")
    to_name=$(_skill_name "$TO_SHA" "$plugin" "$skill")
    if [ -n "$from_name" ] && [ -n "$to_name" ] && [ "$from_name" != "$to_name" ]; then
      _breaking "skill-name-changed: $plugin/$skill ($from_name -> $to_name)"
    fi
  done <<< "$common_skills"

  # ── Hooks ────────────────────────────────────────────────────────────────
  from_hooks=$(_hooks_summary "$FROM_SHA" "$plugin")
  to_hooks=$(_hooks_summary "$TO_SHA" "$plugin")

  if [ "$from_hooks" != "$to_hooks" ]; then
    # Hooks removed = CAUTIONARY
    removed_hooks=$(comm -23 <(echo "$from_hooks") <(echo "$to_hooks") 2>/dev/null)
    added_hooks=$(comm -13 <(echo "$from_hooks") <(echo "$to_hooks") 2>/dev/null)

    while IFS= read -r hook; do
      [ -z "$hook" ] && continue
      _cautionary "hook-removed: $plugin ($hook)"
    done <<< "$removed_hooks"

    while IFS= read -r hook; do
      [ -z "$hook" ] && continue
      _safe "hook-added: $plugin ($hook)"
    done <<< "$added_hooks"
  fi

  # ── Companions ───────────────────────────────────────────────────────────
  from_comps=$(_companions "$FROM_SHA" "$plugin")
  to_comps=$(_companions "$TO_SHA" "$plugin")

  if [ "$from_comps" != "$to_comps" ]; then
    removed_comps=$(comm -23 <(echo "$from_comps") <(echo "$to_comps") 2>/dev/null)
    added_comps=$(comm -13 <(echo "$from_comps") <(echo "$to_comps") 2>/dev/null)

    while IFS= read -r comp; do
      [ -z "$comp" ] && continue
      _cautionary "companion-removed: $plugin ($comp)"
    done <<< "$removed_comps"

    while IFS= read -r comp; do
      [ -z "$comp" ] && continue
      _safe "companion-added: $plugin ($comp)"
    done <<< "$added_comps"
  fi

done <<< "$COMMON_PLUGINS"

# ── Output ───────────────────────────────────────────────────────────────────

BREAK_COUNT=${#BREAKING[@]}
CAUTION_COUNT=${#CAUTIONARY[@]}
SAFE_COUNT=${#SAFE[@]}

# Determine exit code
EXIT_CODE=0
if [ "$BREAK_COUNT" -gt 0 ]; then
  EXIT_CODE=1
elif [ "$CAUTION_COUNT" -gt 0 ]; then
  if $CI_MODE; then
    EXIT_CODE=0
  else
    EXIT_CODE=2
  fi
fi

if $JSON_MODE; then
  # Build JSON arrays
  _json_array() {
    local -n arr=$1
    local first=true
    echo -n "["
    for item in "${arr[@]+"${arr[@]}"}"; do
      $first || echo -n ","
      first=false
      # Escape quotes in item
      item="${item//\\/\\\\}"
      item="${item//\"/\\\"}"
      echo -n "\"$item\""
    done
    echo -n "]"
  }

  echo -n '{"from":"'"$FROM_REF"'","to":"'"$TO_REF"'",'
  echo -n '"breaking_count":'"$BREAK_COUNT"','
  echo -n '"cautionary_count":'"$CAUTION_COUNT"','
  echo -n '"safe_count":'"$SAFE_COUNT"','
  echo -n '"breaking":'
  _json_array BREAKING
  echo -n ',"cautionary":'
  _json_array CAUTIONARY
  echo -n ',"safe":'
  _json_array SAFE
  echo -n ',"exit_code":'"$EXIT_CODE"
  echo '}'
else
  echo ""
  echo "  Upgrade Safety Report"
  echo "  ──────────────────────────────────────"
  echo "  Comparing: $FROM_REF → $TO_REF"
  echo ""

  if [ "$BREAK_COUNT" -gt 0 ]; then
    echo "  BREAKING ($BREAK_COUNT):"
    for item in "${BREAKING[@]}"; do
      echo "    !! $item"
    done
    echo ""
  fi

  if [ "$CAUTION_COUNT" -gt 0 ]; then
    echo "  CAUTIONARY ($CAUTION_COUNT):"
    for item in "${CAUTIONARY[@]}"; do
      echo "    ?? $item"
    done
    echo ""
  fi

  if [ "$SAFE_COUNT" -gt 0 ]; then
    echo "  SAFE ($SAFE_COUNT):"
    for item in "${SAFE[@]}"; do
      echo "    ok $item"
    done
    echo ""
  fi

  if [ "$BREAK_COUNT" -eq 0 ] && [ "$CAUTION_COUNT" -eq 0 ] && [ "$SAFE_COUNT" -eq 0 ]; then
    echo "  No API surface changes detected."
    echo ""
  fi

  echo "  ──────────────────────────────────────"
  echo "  Summary: $BREAK_COUNT breaking, $CAUTION_COUNT cautionary, $SAFE_COUNT safe"

  if [ "$BREAK_COUNT" -gt 0 ]; then
    echo "  WARNING: Breaking changes detected — this must be a MAJOR version bump."
  elif [ "$CAUTION_COUNT" -gt 0 ]; then
    echo "  NOTE: Cautionary changes detected — review before releasing."
  fi

  echo ""
fi

exit $EXIT_CODE

#!/usr/bin/env bash
# Plugin consistency checks — catches cross-reference and version drift bugs.
# Runs as part of fast-validate on every push. Pure bash + jq, no Claude needed.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGINS_DIR="$ROOT/plugins"
PASS=0
FAIL=0
WARN=0

_ok()   { echo "  PASS  $1"; PASS=$((PASS + 1)); }
_warn() { echo "  WARN  $1"; echo "        $2"; WARN=$((WARN + 1)); }
_fail() { echo "  FAIL  $1"; echo "        $2"; FAIL=$((FAIL + 1)); }

echo ""
echo "  Plugin consistency checks"
echo "  ──────────────────────────────────────"
echo ""

# ── Check 1: Version badge in README matches plugin.json ─────────────────────
echo "  Checking version badge consistency..."
for pjson in "$PLUGINS_DIR"/*/".claude-plugin/plugin.json"; do
  plugin_dir="$(dirname "$(dirname "$pjson")")"
  name="$(basename "$plugin_dir")"
  readme="$plugin_dir/README.md"

  ver=$(python3 -c "import json; print(json.load(open('$pjson'))['version'])" 2>/dev/null)
  [ -z "$ver" ] && { _fail "$name: version badge" "cannot read plugin.json version"; continue; }

  if [ ! -f "$readme" ]; then
    _warn "$name: version badge" "README.md missing"
    continue
  fi

  # Match "**Version:** X.Y.Z" in first 5 lines
  badge_ver=$(head -5 "$readme" | grep -oP '(?<=Version:\*\* )\S+' | head -1)
  if [ -z "$badge_ver" ]; then
    _warn "$name: version badge" "no version badge found in README"
  elif [ "$badge_ver" != "$ver" ]; then
    _fail "$name: version badge" "plugin.json=$ver  README=$badge_ver"
  else
    _ok "$name: version badge"
  fi
done

# ── Check 2: Agent skill references resolve ──────────────────────────────────
echo ""
echo "  Checking agent skill cross-references..."
for agent_file in "$PLUGINS_DIR"/*/agents/*.md; do
  [ -f "$agent_file" ] || continue
  plugin_dir="$(dirname "$(dirname "$agent_file")")"
  plugin_name="$(basename "$plugin_dir")"
  agent_name="$(basename "$agent_file" .md)"

  # Extract skills: line from frontmatter (between --- markers)
  skills_line=$(awk '/^---$/{n++; next} n==1 && /^skills:/{print; exit}' "$agent_file")
  [ -z "$skills_line" ] && continue

  # Parse comma-separated skill names
  skills_csv="${skills_line#skills: }"
  IFS=',' read -ra skill_list <<< "$skills_csv"

  # Read companions from ctl.json
  ctl="$plugin_dir/.claude-plugin/ctl.json"
  companions=""
  if [ -f "$ctl" ]; then
    companions=$(python3 -c "
import json
d = json.load(open('$ctl'))
for c in d.get('companions', []):
    print(c)
" 2>/dev/null)
  fi

  for raw_skill in "${skill_list[@]}"; do
    skill="$(echo "$raw_skill" | xargs)"  # trim whitespace
    [ -z "$skill" ] && continue

    if [[ "$skill" == *:* ]]; then
      # Companion-prefixed skill: "companion-name:skill-name"
      comp_name="${skill%%:*}"
      skill_name="${skill#*:}"

      # Verify companion is declared
      if ! echo "$companions" | grep -qx "$comp_name"; then
        _fail "$plugin_name/$agent_name → $skill" "references companion '$comp_name' but it's not in ctl.json companions"
        continue
      fi

      # Verify companion plugin exists
      comp_dir="$PLUGINS_DIR/$comp_name"
      if [ ! -d "$comp_dir" ]; then
        _fail "$plugin_name/$agent_name → $skill" "companion plugin '$comp_name' does not exist"
        continue
      fi

      # Verify skill directory exists in companion
      if [ ! -d "$comp_dir/skills/$skill_name" ]; then
        _fail "$plugin_name/$agent_name → $skill" "skill '$skill_name' not found in companion '$comp_name/skills/'"
      fi
    else
      # Local skill — check this plugin's skills/ dir first
      if [ ! -d "$plugin_dir/skills/$skill" ]; then
        # Not local — check if it exists in any declared companion (unprefixed companion ref)
        found_in_companion=""
        while IFS= read -r comp_name; do
          [ -z "$comp_name" ] && continue
          if [ -d "$PLUGINS_DIR/$comp_name/skills/$skill" ]; then
            found_in_companion="$comp_name"
            break
          fi
        done <<< "$companions"

        if [ -n "$found_in_companion" ]; then
          _warn "$plugin_name/$agent_name → $skill" "found in companion '$found_in_companion' but missing prefix (should be '$found_in_companion:$skill')"
        else
          _fail "$plugin_name/$agent_name → $skill" "skill '$skill' not found locally or in any companion"
        fi
      fi
    fi
  done
  _ok "$plugin_name/$agent_name: skill refs"
done

# ── Check 3: No prompt/agent hooks in PreToolUse or PostToolUse ──────────────
echo ""
echo "  Checking hook type safety (no prompt/agent in hot path)..."
for hooks_file in "$PLUGINS_DIR"/*/hooks/hooks.json; do
  [ -f "$hooks_file" ] || continue
  plugin_dir="$(dirname "$(dirname "$hooks_file")")"
  plugin_name="$(basename "$plugin_dir")"

  # System plugins (system-maker, system-updater, core-spec) are never loaded
  # in teams, so prompt hooks in their hot path are acceptable.
  case "$plugin_name" in system-*|core-*) _ok "$plugin_name: hook safety (system — skip)"; continue ;; esac

  # Check PreToolUse and PostToolUse for prompt/agent type hooks
  bad_hooks=$(python3 -c "
import json, sys
data = json.load(open('$hooks_file'))
hooks = data.get('hooks', data)
bad = []
for event in ['PreToolUse', 'PostToolUse']:
    for entry in hooks.get(event, []):
        for h in entry.get('hooks', []):
            if h.get('type') in ('prompt', 'agent'):
                bad.append(f\"{event}/{entry.get('matcher','*')}: type={h['type']}\")
for b in bad:
    print(b)
" 2>/dev/null)

  if [ -n "$bad_hooks" ]; then
    while IFS= read -r line; do
      _fail "$plugin_name: hook safety" "$line (causes cross-fire in teams)"
    done <<< "$bad_hooks"
  else
    _ok "$plugin_name: hook safety"
  fi
done

# ── Check 4: Agent frontmatter uses tools: not allowed-tools: ────────────────
echo ""
echo "  Checking frontmatter field names..."
for agent_file in "$PLUGINS_DIR"/*/agents/*.md; do
  [ -f "$agent_file" ] || continue
  plugin_name="$(basename "$(dirname "$(dirname "$agent_file")")")"
  agent_name="$(basename "$agent_file" .md)"

  # Check for allowed-tools: in frontmatter
  bad=$(awk '/^---$/{n++; next} n==1 && /^allowed-tools:/{print "uses allowed-tools: instead of tools:"; exit}' "$agent_file")
  if [ -n "$bad" ]; then
    _fail "$plugin_name/$agent_name: frontmatter" "$bad"
  fi
done
for cmd_file in "$PLUGINS_DIR"/*/commands/*.md; do
  [ -f "$cmd_file" ] || continue
  plugin_name="$(basename "$(dirname "$(dirname "$cmd_file")")")"
  cmd_name="$(basename "$cmd_file" .md)"

  # Check for tools: in frontmatter (commands should use allowed-tools:)
  bad=$(awk '/^---$/{n++; next} n==1 && /^tools:/{print "uses tools: instead of allowed-tools:"; exit}' "$cmd_file")
  if [ -n "$bad" ]; then
    _fail "$plugin_name/$cmd_name: frontmatter" "$bad"
  fi
done
_ok "frontmatter field names"

# ── Check 5: CHANGELOG version entries match plugin.json ─────────────────────
echo ""
echo "  Checking CHANGELOG plugin version entries..."
changelog="$ROOT/CHANGELOG.md"
if [ -f "$changelog" ]; then
  # Extract [Unreleased] plugin version lines like: - `plugin-name`: X.Y.Z → A.B.C
  while IFS= read -r line; do
    # Match: - `plugin-name`: old → new
    if [[ "$line" =~ ^-\ \`([a-z][-a-z0-9]*)\`:.+→\ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
      pname="${BASH_REMATCH[1]}"
      expected_ver="${BASH_REMATCH[2]}"
      pjson="$PLUGINS_DIR/$pname/.claude-plugin/plugin.json"
      if [ -f "$pjson" ]; then
        actual_ver=$(python3 -c "import json; print(json.load(open('$pjson'))['version'])" 2>/dev/null)
        if [ "$actual_ver" != "$expected_ver" ]; then
          _fail "$pname: changelog version" "CHANGELOG says $expected_ver, plugin.json says $actual_ver"
        fi
      fi
    fi
  done < <(awk '/^## \[Unreleased\]/{found=1; next} /^## \[/{exit} found{print}' "$changelog")
  _ok "CHANGELOG version entries"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "  ──────────────────────────────────────"
echo "  Results: $PASS passed, $WARN warned, $FAIL failed"
echo ""

[ "$FAIL" -eq 0 ]

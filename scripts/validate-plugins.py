#!/usr/bin/env python3
"""validate-plugins.py — Tier 1 structural validation for claude-kit plugins.

Fast, deterministic, no Claude. Checks JSON syntax, field names, companion
existence, and hook script references.

Exit codes:
  0 — all checks pass
  1 — one or more FATAL failures
  2 — warnings only (use --strict to promote warnings to failures)
"""

import sys
import os
import json
import re
import argparse
import subprocess
import pathlib

REPO_ROOT   = pathlib.Path(__file__).parent.parent.resolve()
PLUGINS_DIR = REPO_ROOT / "plugins"

VALID_PLUGIN_JSON_FIELDS = {"name", "description", "version"}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
VALID_ROLES = {
    "engineer", "grader", "tester", "knowledge",
    "system", "debugger", "core",
}
SKILL_MD_LINE_LIMIT = 500


def _frontmatter_keys(path: pathlib.Path) -> set:
    """Return the set of top-level frontmatter key names from a markdown file."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return set()
    if not lines or lines[0].strip() != "---":
        return set()
    keys = set()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith(" "):
            keys.add(line.split(":", 1)[0].strip())
    return keys


# ── Changed-plugin detection ──────────────────────────────────────────────────

def find_changed_plugins() -> list:
    """Return plugin names modified since HEAD~1 (used in push CI)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        names = set()
        for line in result.stdout.splitlines():
            parts = line.split("/")
            if len(parts) >= 2 and parts[0] == "plugins":
                names.add(parts[1])
        return sorted(names)
    except Exception as e:
        print(f"Error finding changed plugins: {e}", file=sys.stderr)
        return []


# ── Single-plugin validator ───────────────────────────────────────────────────

def validate_plugin(plugin_dir: pathlib.Path, strict: bool) -> dict:
    """Run all Tier 1 checks on one plugin directory. Returns a result dict."""
    name = plugin_dir.name
    findings = []

    def fatal(check_id: int, message: str) -> None:
        findings.append({
            "tier": 1, "level": "FATAL",
            "check_id": check_id, "message": message,
        })

    def warn(check_id: int, message: str) -> None:
        level = "FATAL" if strict else "WARN"
        findings.append({
            "tier": 1, "level": level,
            "check_id": check_id, "message": message,
        })

    # ── Check 1: plugin.json exists and is valid JSON ─────────────────────────
    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        fatal(1, ".claude-plugin/plugin.json does not exist")
        return {"plugin": name, "status": "fail", "findings": findings}

    try:
        plugin_json = json.loads(plugin_json_path.read_text())
    except json.JSONDecodeError as e:
        fatal(1, f".claude-plugin/plugin.json is not valid JSON: {e}")
        return {"plugin": name, "status": "fail", "findings": findings}

    # ── Check 2: plugin.json has ONLY allowed fields ──────────────────────────
    extra_fields = set(plugin_json.keys()) - VALID_PLUGIN_JSON_FIELDS
    if extra_fields:
        fatal(2, (
            f"plugin.json has extra field(s): {', '.join(sorted(extra_fields))} "
            f"(only 'name', 'description', 'version' are allowed — "
            f"put 'role'/'companions' in ctl.json)"
        ))

    # ── Check 3: plugin.json.name matches directory name ─────────────────────
    json_name = plugin_json.get("name", "")
    if json_name != name:
        fatal(3, (
            f"plugin.json 'name' is '{json_name}' "
            f"but directory name is '{name}'"
        ))

    # ── Check 4: version is valid semver (x.y.z) ─────────────────────────────
    version = plugin_json.get("version", "")
    if version and not SEMVER_RE.match(str(version)):
        fatal(4, (
            f"plugin.json 'version' is '{version}' — "
            f"must match x.y.z format (e.g. 0.1.0)"
        ))

    # ── Check 5: ctl.json is valid JSON; companions exist ────────────────────
    ctl_path = plugin_dir / ".claude-plugin" / "ctl.json"
    ctl_data = None
    if ctl_path.exists():
        try:
            ctl_data = json.loads(ctl_path.read_text())
        except json.JSONDecodeError as e:
            fatal(5, f".claude-plugin/ctl.json is not valid JSON: {e}")
            ctl_data = None

        if ctl_data is not None:
            for comp in ctl_data.get("companions", []):
                comp_dir = PLUGINS_DIR / comp
                if not comp_dir.is_dir():
                    fatal(5, f"companion '{comp}' not found in plugins/")

    # ── Check 6 & 7: hooks/hooks.json ────────────────────────────────────────
    hooks_path = plugin_dir / "hooks" / "hooks.json"
    if hooks_path.exists():
        try:
            hooks_data = json.loads(hooks_path.read_text())
        except json.JSONDecodeError as e:
            fatal(6, f"hooks/hooks.json is not valid JSON: {e}")
            hooks_data = None

        if hooks_data is not None:
            hooks_root = hooks_data.get("hooks", hooks_data)

            # Check 6: must use event-based dict, not flat array
            if isinstance(hooks_root, list):
                fatal(6, (
                    "hooks/hooks.json uses a flat array — "
                    "must use event-based keys (PreToolUse, PostToolUse, Stop, …)"
                ))
            elif isinstance(hooks_root, dict):
                # Check 7: every referenced script must exist
                for event_name, event_hooks in hooks_root.items():
                    if not isinstance(event_hooks, list):
                        continue
                    for entry in event_hooks:
                        if not isinstance(entry, dict):
                            continue
                        inner_hooks = entry.get("hooks", [])
                        if not isinstance(inner_hooks, list):
                            continue
                        for hook in inner_hooks:
                            if not isinstance(hook, dict):
                                continue
                            if hook.get("type") != "command":
                                continue
                            cmd = hook.get("command", "").strip()
                            if not cmd:
                                continue
                            # Only check commands that reference CLAUDE_PLUGIN_ROOT.
                            # Inline shell expressions (echo, if, git, etc.) are valid
                            # and should not be treated as file paths.
                            if "${CLAUDE_PLUGIN_ROOT}" not in cmd:
                                continue
                            expanded = cmd.replace(
                                "${CLAUDE_PLUGIN_ROOT}", str(plugin_dir)
                            )
                            # First token is the script path
                            script_path = pathlib.Path(expanded.split()[0])
                            if not script_path.exists():
                                fatal(7, (
                                    f"hook script not found: {cmd}"
                                ))

    # ── Warning 8: description is empty or too short (<20 chars) ─────────────
    desc = plugin_json.get("description", "")
    if not desc or len(desc) < 20:
        warn(8, (
            f"plugin.json 'description' is empty or very short "
            f"({len(desc)} chars, minimum 20)"
        ))

    # ── Check 10: SKILL.md files must not exceed 500 lines ───────────────────
    skills_dir = plugin_dir / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                n = len(skill_md.read_text().splitlines())
                if n > SKILL_MD_LINE_LIMIT:
                    warn(10, (
                        f"skills/{skill_dir.name}/SKILL.md exceeds {SKILL_MD_LINE_LIMIT} lines "
                        f"({n} lines) — split overflow into reference.md or other companion files"
                    ))

    # ── Check 11: agent files must use 'tools:' not 'allowed-tools:' ─────────
    agents_dir = plugin_dir / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            if "allowed-tools" in _frontmatter_keys(f):
                fatal(11, (
                    f"agents/{f.name}: uses 'allowed-tools:' frontmatter key — "
                    f"agents must use 'tools:' (silent load failure)"
                ))

    # ── Check 12: command files must use 'allowed-tools:' not 'tools:' ───────
    commands_dir = plugin_dir / "commands"
    if commands_dir.exists():
        for f in sorted(commands_dir.glob("*.md")):
            if "tools" in _frontmatter_keys(f):
                fatal(12, (
                    f"commands/{f.name}: uses 'tools:' frontmatter key — "
                    f"commands must use 'allowed-tools:' (silent load failure)"
                ))

    # ── Check 13: ctl.json role must be a known value ─────────────────────────
    if ctl_data is not None:
        role = ctl_data.get("role")
        if role is not None and role not in VALID_ROLES:
            warn(13, (
                f"ctl.json 'role' is '{role}' — "
                f"expected one of: {', '.join(sorted(VALID_ROLES))}"
            ))

    # ── Check 14: ctl.json domain must be a string if present ────────────────
    if ctl_data is not None:
        domain = ctl_data.get("domain")
        if domain is not None and not isinstance(domain, str):
            fatal(14, (
                f"ctl.json 'domain' must be a string, "
                f"got {type(domain).__name__}"
            ))

    # ── Check 15: README version badge must match plugin.json version ─────────
    readme_path = plugin_dir / "README.md"
    if readme_path.exists() and version and SEMVER_RE.match(str(version)):
        readme_lines = readme_path.read_text().splitlines()
        badge_match = None
        for line in readme_lines[:5]:
            m = re.search(r"\*\*Version:\*\*\s*(\d+\.\d+\.\d+)", line)
            if m:
                badge_match = m.group(1)
                break
        if badge_match is None:
            warn(15, "README.md missing version badge in first 5 lines")
        elif badge_match != version:
            fatal(15, (
                f"README.md version badge ({badge_match}) "
                f"does not match plugin.json version ({version})"
            ))

    # ── Warning 9: knowledge plugins must not have agents/ or commands/ ───────
    is_knowledge = (
        ctl_data is not None and ctl_data.get("role") == "knowledge"
    )
    if is_knowledge:
        for dirname in ("agents", "commands"):
            d = plugin_dir / dirname
            if d.exists() and any(d.iterdir()):
                warn(9, (
                    f"knowledge plugin (role: knowledge) "
                    f"has non-empty {dirname}/ directory"
                ))

    # ── Determine overall status ──────────────────────────────────────────────
    has_fatal = any(f["level"] == "FATAL" for f in findings)
    has_warn  = any(f["level"] == "WARN"  for f in findings)

    if has_fatal:
        status = "fail"
    elif has_warn:
        status = "warn"
    else:
        status = "pass"

    return {"plugin": name, "status": status, "findings": findings}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Validate every plugin in plugins/",
    )
    group.add_argument(
        "--plugin", metavar="NAME",
        help="Validate a single plugin by directory name",
    )
    group.add_argument(
        "--changed", action="store_true",
        help="Validate only plugins with changes since HEAD~1",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable JSON output",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as fatal failures (exit code 1)",
    )
    args = parser.parse_args()

    # ── Collect plugin directories to check ──────────────────────────────────
    if args.all:
        if not PLUGINS_DIR.exists():
            print(f"Error: {PLUGINS_DIR} does not exist", file=sys.stderr)
            sys.exit(1)
        plugins = sorted(
            [d for d in PLUGINS_DIR.iterdir() if d.is_dir()],
            key=lambda d: d.name,
        )

    elif args.plugin:
        plugin_dir = PLUGINS_DIR / args.plugin
        if not plugin_dir.is_dir():
            print(
                f"Error: Plugin '{args.plugin}' not found in {PLUGINS_DIR}",
                file=sys.stderr,
            )
            sys.exit(1)
        plugins = [plugin_dir]

    elif args.changed:
        changed_names = find_changed_plugins()
        if not changed_names:
            _emit_empty(args.json)
            sys.exit(0)
        plugins = [PLUGINS_DIR / n for n in changed_names if (PLUGINS_DIR / n).is_dir()]
        if not plugins:
            _emit_empty(args.json)
            sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)

    if not plugins:
        _emit_empty(args.json)
        sys.exit(0)

    # ── Run validation ────────────────────────────────────────────────────────
    results = [validate_plugin(d, strict=args.strict) for d in plugins]

    passed  = sum(1 for r in results if r["status"] == "pass")
    warned  = sum(1 for r in results if r["status"] == "warn")
    failed  = sum(1 for r in results if r["status"] == "fail")
    total   = len(results)

    exit_code = 1 if failed > 0 else (2 if warned > 0 else 0)

    if args.json:
        print(json.dumps({
            "summary": {
                "plugins_checked": total,
                "passed": passed,
                "warned": warned,
                "failed": failed,
                "exit_code": exit_code,
            },
            "results": results,
        }, indent=2))
    else:
        for r in results:
            pname    = r["plugin"]
            status   = r["status"]
            findings = r["findings"]
            tag = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[status]
            print(f"  {tag}  {pname}")
            for f in findings:
                print(f"        [{f['level']}] (check {f['check_id']}) {f['message']}")

        print()
        print(
            f"Results: {passed} passed, {warned} warned, {failed} failed"
            f"  ({total} checked)"
        )

    sys.exit(exit_code)


def _emit_empty(as_json: bool) -> None:
    if as_json:
        print(json.dumps({
            "summary": {
                "plugins_checked": 0, "passed": 0,
                "warned": 0, "failed": 0, "exit_code": 0,
            },
            "results": [],
        }, indent=2))
    else:
        print("No plugins to validate.")


if __name__ == "__main__":
    main()

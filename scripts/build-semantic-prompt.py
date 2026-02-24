#!/usr/bin/env python3
"""Build a focused semantic review prompt for changed plugins.

Usage:
    python3 build-semantic-prompt.py plugin-name-1 plugin-name-2 ...

Reads each plugin's metadata, agent frontmatter, and skill structure to
give Claude Haiku enough context for a fast semantic review.  The output
is a self-contained prompt that can be piped straight into `claude -p`.
"""

import json
import pathlib
import sys
import textwrap

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
PLUGINS_DIR = REPO_ROOT / "plugins"

MAX_AGENT_LINES = 30   # first N lines of each agent file
MAX_SKILL_LINES = 20   # first N lines of each SKILL.md


def read_head(path: pathlib.Path, n: int) -> str:
    """Read first *n* lines of a file, or empty string if missing."""
    try:
        lines = path.read_text().splitlines()[:n]
        return "\n".join(lines)
    except OSError:
        return ""


def collect_plugin(name: str) -> dict | None:
    """Gather metadata + truncated content for one plugin."""
    plugin_dir = PLUGINS_DIR / name
    if not plugin_dir.is_dir():
        return None

    pjson_path = plugin_dir / ".claude-plugin" / "plugin.json"
    try:
        pjson = json.loads(pjson_path.read_text())
    except Exception:
        return None

    ctl = {}
    ctl_path = plugin_dir / ".claude-plugin" / "ctl.json"
    if ctl_path.exists():
        try:
            ctl = json.loads(ctl_path.read_text())
        except Exception:
            pass

    agents = {}
    agents_dir = plugin_dir / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            agents[f.stem] = read_head(f, MAX_AGENT_LINES)

    skills = {}
    skills_dir = plugin_dir / "skills"
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir():
                skill_md = d / "SKILL.md"
                skills[d.name] = read_head(skill_md, MAX_SKILL_LINES)

    hooks_path = plugin_dir / "hooks" / "hooks.json"
    hooks_summary = ""
    if hooks_path.exists():
        try:
            hdata = json.loads(hooks_path.read_text())
            hooks_obj = hdata.get("hooks", hdata)
            parts = []
            for event, entries in hooks_obj.items():
                types = set()
                for entry in entries:
                    for h in entry.get("hooks", []):
                        types.add(h.get("type", "?"))
                parts.append(f"{event}: {', '.join(sorted(types))}")
            hooks_summary = " | ".join(parts)
        except Exception:
            hooks_summary = "(parse error)"

    commands = []
    cmds_dir = plugin_dir / "commands"
    if cmds_dir.exists():
        commands = sorted(f.stem for f in cmds_dir.glob("*.md"))

    return {
        "name": name,
        "description": pjson.get("description", ""),
        "version": pjson.get("version", "?"),
        "role": ctl.get("role", "unknown"),
        "companions": ctl.get("companions", []),
        "agents": agents,
        "skills": skills,
        "commands": commands,
        "hooks": hooks_summary,
    }


def build_prompt(plugins: list[dict]) -> str:
    """Assemble the full review prompt."""
    sections = []
    for p in plugins:
        agent_blocks = []
        for aname, ahead in p["agents"].items():
            agent_blocks.append(f"#### Agent: {aname}\n```\n{ahead}\n```")
        agents_str = "\n".join(agent_blocks) if agent_blocks else "(no agents)"

        skill_blocks = []
        for sname, shead in p["skills"].items():
            first_line = shead.splitlines()[0] if shead else "(empty)"
            skill_blocks.append(f"- **{sname}**: {first_line}")
        skills_str = "\n".join(skill_blocks) if skill_blocks else "(no skills)"

        sections.append(
            f"### {p['name']}\n"
            f"- **Role:** {p['role']}  **Version:** {p['version']}\n"
            f"- **Description:** {p['description']}\n"
            f"- **Companions:** {', '.join(p['companions']) or 'none'}\n"
            f"- **Commands:** {', '.join(p['commands']) or 'none'}\n"
            f"- **Hooks:** {p['hooks'] or 'none'}\n\n"
            f"**Agents** ({len(p['agents'])}):\n{agents_str}\n\n"
            f"**Skills** ({len(p['skills'])}):\n{skills_str}\n"
        )

    plugins_block = "\n---\n".join(sections)

    return (
        "You are a senior plugin reviewer. Perform a FAST semantic review of the\n"
        "changed plugins below.  Focus ONLY on issues that deterministic scripts\n"
        "cannot catch.  Do NOT re-check JSON syntax, file existence, or frontmatter\n"
        "key names -- those are already verified by Tier 1 validation.\n\n"
        "## What to check\n\n"
        "1. **Identity coherence** -- does the agent name match its system prompt?\n"
        "   Would renaming the agent change nothing about its prompt?  Red flag.\n"
        "2. **Domain specificity** -- does a 'Zephyr' plugin demonstrate Zephyr\n"
        "   knowledge, or is it generic enough for any RTOS?\n"
        "3. **Content depth** -- are skills substantive (100+ lines of real domain\n"
        "   material) or hollow stubs?  Are agent prompts detailed enough?\n"
        "4. **Cross-agent contradictions** -- do two agents in the same plugin give\n"
        "   conflicting instructions?\n"
        "5. **Hook appropriateness** -- do hook events/types make sense for the role?\n"
        "   A debugger with write hooks is suspicious.\n\n"
        "## What to SKIP\n\n"
        "- JSON syntax, file existence, frontmatter field names (Tier 1)\n"
        "- README formatting, version badge matching (consistency checks)\n"
        "- Companion skill prefix conventions (consistency checks)\n"
        "- Code style or prose quality (out of scope)\n\n"
        "## Changed plugins\n\n"
        f"{plugins_block}\n\n"
        "## Output format\n\n"
        "For each plugin output exactly:\n\n"
        "```\n"
        "## <plugin-name>\n"
        "**Status:** PASS | WARN\n\n"
        "- [WARN] <finding>\n"
        "- [NOTE] <observation>\n\n"
        "**Summary:** 1-2 sentences.\n"
        "```\n\n"
        "Then: `---\\n**Overall: X/Y plugins PASS**`\n\n"
        "Be concise.  If a plugin looks good, say PASS and move on.\n"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: build-semantic-prompt.py <plugin-name> ...", file=sys.stderr)
        sys.exit(1)

    names = sys.argv[1:]
    plugins = []
    for name in names:
        name = name.strip()
        if not name:
            continue
        p = collect_plugin(name)
        if p:
            plugins.append(p)

    if not plugins:
        print("No valid plugins found to review.", file=sys.stderr)
        sys.exit(0)

    print(build_prompt(plugins))


if __name__ == "__main__":
    main()

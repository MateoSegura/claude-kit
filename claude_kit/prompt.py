"""System prompt builder from loaded plugins."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_kit.models import Plugin

# Regex to strip YAML frontmatter (--- delimited block at start).
_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n.*?\n---\s*\n?",
    re.DOTALL,
)


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from a skill file."""
    return _FRONTMATTER_RE.sub("", content).strip()


def _read_skills(plugin_path: Path) -> list[str]:
    """Read all SKILL.md files from a plugin's skills/ dir."""
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return []

    parts: list[str] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_file.is_file():
            raw = skill_file.read_text()
            body = _strip_frontmatter(raw)
            if body:
                parts.append(body)
    return parts


def build_system_prompt(plugins: list[Plugin]) -> str:
    """Build a system prompt from loaded plugins.

    Reads SKILL.md files from each plugin's skills/ directory,
    strips YAML frontmatter, and concatenates the content into
    a single string suitable for the Anthropic Messages API.

    Args:
        plugins: List of Plugin objects with valid paths.

    Returns:
        Concatenated skill content, or empty string if no
        skills are found.
    """
    sections: list[str] = []
    for plugin in plugins:
        parts = _read_skills(plugin.path)
        sections.extend(parts)

    return "\n\n".join(sections)

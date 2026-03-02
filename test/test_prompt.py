"""Tests for claude_kit.prompt — system prompt builder.

TDD Phase 7: These tests define the contract for building system
prompts from Plugin objects. The builder reads skill content from
each plugin's skills/ directory and concatenates it.
"""

from __future__ import annotations

import json
from pathlib import Path

from claude_kit import Plugin
from claude_kit.prompt import build_system_prompt


def _make_plugin(
    tmp_path: Path,
    name: str,
    skills: dict[str, str] | None = None,
) -> Plugin:
    """Create a minimal plugin directory with optional skills."""
    plugin_dir = tmp_path / name
    meta_dir = plugin_dir / ".claude-plugin"
    meta_dir.mkdir(parents=True)
    (meta_dir / "plugin.json").write_text(
        json.dumps(
            {
                "name": name,
                "description": f"Test {name}",
                "version": "0.0.1",
            }
        )
    )

    if skills:
        for skill_name, content in skills.items():
            skill_dir = plugin_dir / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(content)

    return Plugin(
        name=name,
        path=plugin_dir,
        version="0.0.1",
        role="knowledge",
        domain="universal",
    )


def test_build_system_prompt_importable():
    """build_system_prompt is importable from claude_kit.prompt."""
    assert callable(build_system_prompt)


def test_empty_plugins_returns_empty():
    """No plugins should produce an empty prompt."""
    result = build_system_prompt([])
    assert result == ""


def test_single_plugin_single_skill(tmp_path: Path):
    """A plugin with one skill includes its content."""
    skill_content = (
        "---\nname: test-skill\n"
        "description: A test\n---\n\n"
        "# Test Skill\n\nSome guidance."
    )
    plugin = _make_plugin(
        tmp_path,
        "test-plugin",
        skills={"test-skill": skill_content},
    )

    result = build_system_prompt([plugin])
    assert "# Test Skill" in result
    assert "Some guidance." in result


def test_skill_frontmatter_stripped(tmp_path: Path):
    """YAML frontmatter should be stripped from skill content."""
    skill_content = (
        "---\nname: my-skill\ndescription: desc\nuser-invocable: false\n---\n\n# Body"
    )
    plugin = _make_plugin(
        tmp_path,
        "test-plugin",
        skills={"my-skill": skill_content},
    )

    result = build_system_prompt([plugin])
    assert "user-invocable" not in result
    assert "# Body" in result


def test_multiple_skills_concatenated(tmp_path: Path):
    """Multiple skills in one plugin should all appear."""
    skills = {
        "alpha": ("---\nname: alpha\ndescription: a\n---\n\n# Alpha Content"),
        "beta": ("---\nname: beta\ndescription: b\n---\n\n# Beta Content"),
    }
    plugin = _make_plugin(tmp_path, "test-plugin", skills=skills)

    result = build_system_prompt([plugin])
    assert "# Alpha Content" in result
    assert "# Beta Content" in result


def test_multiple_plugins(tmp_path: Path):
    """Skills from multiple plugins should all appear."""
    p1 = _make_plugin(
        tmp_path,
        "plugin-a",
        skills={"skill-a": ("---\nname: a\ndescription: a\n---\n\n# From Plugin A")},
    )
    p2 = _make_plugin(
        tmp_path,
        "plugin-b",
        skills={"skill-b": ("---\nname: b\ndescription: b\n---\n\n# From Plugin B")},
    )

    result = build_system_prompt([p1, p2])
    assert "# From Plugin A" in result
    assert "# From Plugin B" in result


def test_plugin_without_skills(tmp_path: Path):
    """Plugin with no skills/ directory should not error."""
    plugin = _make_plugin(tmp_path, "no-skills")
    result = build_system_prompt([plugin])
    assert isinstance(result, str)


def test_returns_string(tmp_path: Path):
    """build_system_prompt must always return a string."""
    plugin = _make_plugin(
        tmp_path,
        "test-plugin",
        skills={"s": ("---\nname: s\ndescription: d\n---\n\nContent")},
    )
    result = build_system_prompt([plugin])
    assert isinstance(result, str)

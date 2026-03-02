"""Tests for claude_kit.hooks_generator — HooksGenerator contracts.

Validates hooks.json generation: directory creation, JSON structure,
session ID embedding in paths, temp file lifecycle, and history dir lookup.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

# ── Import & Construction ────────────────────────────────────────────────


def test_hooks_generator_importable():
    from claude_kit.hooks_generator import HooksGenerator  # noqa: F401


def test_hooks_generator_exported_from_package():
    from claude_kit import HooksGenerator  # noqa: F401


def test_hooks_generator_instantiation():
    from claude_kit.hooks_generator import HooksGenerator

    gen = HooksGenerator()
    assert gen is not None


# ── Directory Creation ───────────────────────────────────────────────────


def test_generate_creates_history_directory(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-001")

    expected_dir = history_base / "sess-001" / "compact-snapshots"
    assert expected_dir.is_dir()
    # Clean up temp file
    hooks_path.unlink(missing_ok=True)


def test_generate_creates_nested_parent_dirs(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / "deep" / "nested" / "history"
    assert not history_base.exists()

    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-002")

    assert history_base.exists()
    assert (history_base / "sess-002" / "compact-snapshots").is_dir()
    hooks_path.unlink(missing_ok=True)


def test_generate_idempotent_on_existing_dir(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    target_dir = history_base / "sess-003" / "compact-snapshots"
    target_dir.mkdir(parents=True)

    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        # Should not raise even though dir already exists
        hooks_path = gen.generate_history_hooks("sess-003")

    assert target_dir.is_dir()
    hooks_path.unlink(missing_ok=True)


# ── JSON Format Correctness ─────────────────────────────────────────────


def test_generated_file_is_valid_json(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-json")

    content = hooks_path.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)
    hooks_path.unlink(missing_ok=True)


def test_generated_file_ends_with_newline(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-nl")

    content = hooks_path.read_text()
    assert content.endswith("\n")
    hooks_path.unlink(missing_ok=True)


def test_generated_json_is_indented(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-indent")

    content = hooks_path.read_text()
    # indent=2 produces multi-line output with leading spaces
    assert "\n" in content.rstrip("\n")
    assert "  " in content
    hooks_path.unlink(missing_ok=True)


# ── Hooks Structure ─────────────────────────────────────────────────────


def test_hooks_json_has_hooks_key(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-key")

    parsed = json.loads(hooks_path.read_text())
    assert "hooks" in parsed
    assert isinstance(parsed["hooks"], list)
    hooks_path.unlink(missing_ok=True)


def test_hooks_contains_single_precompact_hook(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-hook")

    parsed = json.loads(hooks_path.read_text())
    hooks = parsed["hooks"]
    assert len(hooks) == 1
    assert hooks[0]["type"] == "PreCompact"
    hooks_path.unlink(missing_ok=True)


def test_hook_has_command_field(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-cmd")

    parsed = json.loads(hooks_path.read_text())
    hook = parsed["hooks"][0]
    assert "command" in hook
    assert isinstance(hook["command"], str)
    hooks_path.unlink(missing_ok=True)


# ── Session ID Embedding ────────────────────────────────────────────────


def test_session_id_embedded_in_command_path(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("my-unique-session-42")

    parsed = json.loads(hooks_path.read_text())
    command = parsed["hooks"][0]["command"]
    assert "my-unique-session-42" in command
    hooks_path.unlink(missing_ok=True)


def test_command_targets_compact_snapshots_subdir(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-snap")

    parsed = json.loads(hooks_path.read_text())
    command = parsed["hooks"][0]["command"]
    assert "compact-snapshots" in command
    hooks_path.unlink(missing_ok=True)


def test_command_uses_cat_redirect(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-cat")

    parsed = json.loads(hooks_path.read_text())
    command = parsed["hooks"][0]["command"]
    assert command.startswith("cat > ")
    hooks_path.unlink(missing_ok=True)


def test_command_uses_date_timestamp(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-date")

    parsed = json.loads(hooks_path.read_text())
    command = parsed["hooks"][0]["command"]
    # The command uses shell date expansion for unique filenames
    assert "$(date +%s)" in command
    assert command.endswith(".json")
    hooks_path.unlink(missing_ok=True)


def test_different_session_ids_produce_different_paths(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        path_a = gen.generate_history_hooks("session-alpha")
        path_b = gen.generate_history_hooks("session-beta")

    parsed_a = json.loads(path_a.read_text())
    parsed_b = json.loads(path_b.read_text())
    cmd_a = parsed_a["hooks"][0]["command"]
    cmd_b = parsed_b["hooks"][0]["command"]
    assert "session-alpha" in cmd_a
    assert "session-beta" in cmd_b
    assert cmd_a != cmd_b
    path_a.unlink(missing_ok=True)
    path_b.unlink(missing_ok=True)


# ── Temp File Properties ────────────────────────────────────────────────


def test_returns_path_object(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-path")

    assert isinstance(hooks_path, Path)
    hooks_path.unlink(missing_ok=True)


def test_temp_file_exists_on_disk(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-exists")

    assert hooks_path.exists()
    assert hooks_path.is_file()
    hooks_path.unlink(missing_ok=True)


def test_temp_file_has_json_suffix(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-suffix")

    assert hooks_path.suffix == ".json"
    hooks_path.unlink(missing_ok=True)


def test_temp_file_has_ck_hooks_prefix(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-prefix")

    assert hooks_path.name.startswith("ck-hooks-")
    hooks_path.unlink(missing_ok=True)


def test_temp_file_persists_after_close(tmp_path: Path):
    """Verifies delete=False — the file must survive after the generator returns."""
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-persist")

    # File should still be readable after the method returned
    content = hooks_path.read_text()
    assert len(content) > 0
    hooks_path.unlink(missing_ok=True)


def test_cleanup_of_temp_file(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        hooks_path = gen.generate_history_hooks("sess-cleanup")

    assert hooks_path.exists()
    hooks_path.unlink()
    assert not hooks_path.exists()


def test_multiple_generates_produce_distinct_files(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        gen = HooksGenerator()
        path_1 = gen.generate_history_hooks("sess-multi")
        path_2 = gen.generate_history_hooks("sess-multi")

    # Each call creates a new temp file even for the same session ID
    assert path_1 != path_2
    assert path_1.exists()
    assert path_2.exists()
    path_1.unlink(missing_ok=True)
    path_2.unlink(missing_ok=True)


# ── history_dir Static Method ────────────────────────────────────────────


def test_history_dir_returns_path(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        result = HooksGenerator.history_dir("sess-static")

    assert isinstance(result, Path)


def test_history_dir_includes_session_id(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        result = HooksGenerator.history_dir("my-session-id")

    assert result.name == "my-session-id"
    assert str(result).endswith("my-session-id")


def test_history_dir_uses_history_base(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        result = HooksGenerator.history_dir("sess-base")

    assert result.parent == history_base


def test_history_dir_different_sessions(tmp_path: Path):
    from claude_kit.hooks_generator import HooksGenerator

    history_base = tmp_path / ".claude-kit" / "history"
    with patch("claude_kit.hooks_generator._HISTORY_BASE", history_base):
        dir_a = HooksGenerator.history_dir("alpha")
        dir_b = HooksGenerator.history_dir("beta")

    assert dir_a != dir_b
    assert dir_a.name == "alpha"
    assert dir_b.name == "beta"

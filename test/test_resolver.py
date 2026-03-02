"""Tests for claude_kit.resolver — PluginResolver contracts.

TDD: These tests define the expected behavior of the PluginResolver
before implementation. All tests use tmp_path fixtures to build
minimal plugin directory trees.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_plugin(
    base: Path,
    name: str,
    *,
    role: str = "knowledge",
    domain: str = "universal",
    companions: list[str] | None = None,
    version: str = "0.1.0",
) -> Path:
    """Helper: create a minimal plugin directory structure."""
    plugin_dir = base / name
    meta_dir = plugin_dir / ".claude-plugin"
    meta_dir.mkdir(parents=True)
    (meta_dir / "plugin.json").write_text(
        json.dumps({"name": name, "version": version, "description": f"Test {name}"})
    )
    (meta_dir / "ctl.json").write_text(
        json.dumps(
            {
                "role": role,
                "domain": domain,
                "companions": companions or [],
            }
        )
    )
    return plugin_dir


# ── Import & Construction ────────────────────────────────────────────────


def test_resolver_importable():
    from claude_kit.resolver import PluginResolver  # noqa: F401


def test_resolver_stores_plugins_dirs(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    dirs = [tmp_path / "a", tmp_path / "b"]
    r = PluginResolver(plugins_dirs=dirs)
    assert r.plugins_dirs == dirs


def test_resolver_accepts_optional_telemetry():
    from claude_kit.resolver import PluginResolver

    from claude_kit.telemetry import TelemetryEmitter

    tel = TelemetryEmitter(level="debug")
    r = PluginResolver(plugins_dirs=[], telemetry=tel)
    assert r.telemetry is tel


def test_resolver_telemetry_defaults_to_none():
    from claude_kit.resolver import PluginResolver

    r = PluginResolver(plugins_dirs=[])
    assert r.telemetry is None


# ── find() ───────────────────────────────────────────────────────────────


def test_find_existing_plugin(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "test-plugin", role="knowledge", domain="universal")
    r = PluginResolver(plugins_dirs=[tmp_path])
    plugin = r.find("test-plugin")
    assert plugin.name == "test-plugin"
    assert plugin.role == "knowledge"
    assert plugin.domain == "universal"
    assert plugin.version == "0.1.0"


def test_find_returns_plugin_dataclass(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.models import Plugin

    _make_plugin(tmp_path, "my-plugin")
    r = PluginResolver(plugins_dirs=[tmp_path])
    plugin = r.find("my-plugin")
    assert isinstance(plugin, Plugin)


def test_find_nonexistent_raises(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.exceptions import PluginNotFoundError

    r = PluginResolver(plugins_dirs=[tmp_path])
    with pytest.raises(PluginNotFoundError):
        r.find("no-such-plugin")


def test_find_checks_multiple_dirs(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    _make_plugin(dir_b, "in-second-dir")
    r = PluginResolver(plugins_dirs=[dir_a, dir_b])
    plugin = r.find("in-second-dir")
    assert plugin.name == "in-second-dir"


def test_find_first_dir_wins(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    _make_plugin(dir_a, "dup-plugin", version="1.0.0")
    _make_plugin(dir_b, "dup-plugin", version="2.0.0")
    r = PluginResolver(plugins_dirs=[dir_a, dir_b])
    plugin = r.find("dup-plugin")
    assert plugin.version == "1.0.0"


def test_find_reads_companions(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "eng", companions=["core-kit", "knowledge"])
    r = PluginResolver(plugins_dirs=[tmp_path])
    plugin = r.find("eng")
    assert plugin.companions == ["core-kit", "knowledge"]


def test_find_handles_missing_ctl_json(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    plugin_dir = tmp_path / "bare-plugin"
    meta_dir = plugin_dir / ".claude-plugin"
    meta_dir.mkdir(parents=True)
    (meta_dir / "plugin.json").write_text(
        json.dumps({"name": "bare-plugin", "version": "0.0.1", "description": "bare"})
    )
    # No ctl.json
    r = PluginResolver(plugins_dirs=[tmp_path])
    plugin = r.find("bare-plugin")
    assert plugin.name == "bare-plugin"
    assert plugin.role == ""
    assert plugin.domain == ""
    assert plugin.companions == []


def test_find_handles_nonexistent_dirs():
    from claude_kit.resolver import PluginResolver

    from claude_kit.exceptions import PluginNotFoundError

    r = PluginResolver(plugins_dirs=[Path("/nonexistent/path")])
    with pytest.raises(PluginNotFoundError):
        r.find("anything")


# ── resolve_prefix() ─────────────────────────────────────────────────────


def test_resolve_prefix_expands_team(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "team-engineer", role="engineer")
    _make_plugin(tmp_path, "team-tester", role="tester")
    _make_plugin(tmp_path, "team-knowledge", role="knowledge")
    _make_plugin(tmp_path, "other-plugin", role="knowledge")
    r = PluginResolver(plugins_dirs=[tmp_path])
    names = r.resolve_prefix("team")
    assert sorted(names) == ["team-engineer", "team-knowledge", "team-tester"]
    assert "other-plugin" not in names


def test_resolve_prefix_returns_empty_for_no_match(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "alpha-plugin")
    r = PluginResolver(plugins_dirs=[tmp_path])
    assert r.resolve_prefix("beta") == []


def test_resolve_prefix_searches_all_dirs(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    _make_plugin(dir_a, "team-alpha")
    _make_plugin(dir_b, "team-beta")
    r = PluginResolver(plugins_dirs=[dir_a, dir_b])
    names = r.resolve_prefix("team")
    assert "team-alpha" in names
    assert "team-beta" in names


# ── resolve_companions() ─────────────────────────────────────────────────


def test_resolve_companions_returns_plugins(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.models import Plugin

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "my-engineer",
        role="engineer",
        companions=["core-kit"],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    parent = r.find("my-engineer")
    companions = r.resolve_companions(parent)
    assert len(companions) == 1
    assert isinstance(companions[0], Plugin)
    assert companions[0].name == "core-kit"


def test_resolve_companions_skips_missing(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(
        tmp_path,
        "my-engineer",
        role="engineer",
        companions=["nonexistent-companion"],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    parent = r.find("my-engineer")
    companions = r.resolve_companions(parent)
    assert companions == []


def test_resolve_companions_empty_list(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "standalone", companions=[])
    r = PluginResolver(plugins_dirs=[tmp_path])
    parent = r.find("standalone")
    assert r.resolve_companions(parent) == []


# ── resolve_core_plugins() ───────────────────────────────────────────────


def test_resolve_core_universal(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(tmp_path, "core-spec", role="system", domain="universal")
    _make_plugin(tmp_path, "core-embedded", role="knowledge", domain="embedded")
    r = PluginResolver(plugins_dirs=[tmp_path])
    cores = r.resolve_core_plugins("backend")
    core_names = [p.name for p in cores]
    assert "core-kit" in core_names
    assert "core-spec" in core_names
    assert "core-embedded" not in core_names


def test_resolve_core_domain_match(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(tmp_path, "core-embedded", role="knowledge", domain="embedded")
    _make_plugin(tmp_path, "core-frontend", role="knowledge", domain="frontend")
    r = PluginResolver(plugins_dirs=[tmp_path])
    cores = r.resolve_core_plugins("embedded")
    core_names = [p.name for p in cores]
    assert "core-kit" in core_names
    assert "core-embedded" in core_names
    assert "core-frontend" not in core_names


def test_resolve_core_no_matches(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "not-core", role="engineer", domain="backend")
    r = PluginResolver(plugins_dirs=[tmp_path])
    assert r.resolve_core_plugins("backend") == []


# ── expand_kit() ─────────────────────────────────────────────────────────


def test_expand_kit_single_plugin(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "simple-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    result = r.expand_kit("simple-engineer")
    names = [p.name for p in result]
    assert "simple-engineer" in names
    assert "core-kit" in names


def test_expand_kit_prefix_expands_team(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "myteam-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    _make_plugin(
        tmp_path,
        "myteam-tester",
        role="tester",
        domain="backend",
        companions=["core-kit"],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    result = r.expand_kit("myteam")
    names = [p.name for p in result]
    assert "myteam-engineer" in names
    assert "myteam-tester" in names
    assert "core-kit" in names


def test_expand_kit_deduplicates(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "alpha-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    _make_plugin(
        tmp_path,
        "alpha-tester",
        role="tester",
        domain="backend",
        companions=["core-kit"],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    result = r.expand_kit("alpha")
    names = [p.name for p in result]
    # core-kit should only appear once despite being referenced twice
    assert names.count("core-kit") == 1


def test_expand_kit_core_before_team(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(tmp_path, "core-spec", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "myteam-engineer",
        role="engineer",
        domain="backend",
        companions=[],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    result = r.expand_kit("myteam-engineer")
    names = [p.name for p in result]
    # Core plugins come before team plugins
    core_idx = max(names.index("core-kit"), names.index("core-spec"))
    team_idx = names.index("myteam-engineer")
    assert core_idx < team_idx


def test_expand_kit_nonexistent_raises(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.exceptions import PluginNotFoundError

    r = PluginResolver(plugins_dirs=[tmp_path])
    with pytest.raises(PluginNotFoundError):
        r.expand_kit("does-not-exist")


def test_expand_kit_includes_domain_core(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(tmp_path, "core-backend", role="knowledge", domain="backend")
    _make_plugin(tmp_path, "core-frontend", role="knowledge", domain="frontend")
    _make_plugin(
        tmp_path,
        "api-engineer",
        role="engineer",
        domain="backend",
        companions=[],
    )
    r = PluginResolver(plugins_dirs=[tmp_path])
    result = r.expand_kit("api-engineer")
    names = [p.name for p in result]
    assert "core-kit" in names
    assert "core-backend" in names
    assert "core-frontend" not in names


# ── Telemetry Integration ────────────────────────────────────────────────


def test_expand_kit_emits_plugin_loaded(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.telemetry import TelemetryEmitter

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "tel-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    captured: list[dict] = []
    tel = TelemetryEmitter(level="debug", on_emit=captured.append)
    r = PluginResolver(plugins_dirs=[tmp_path], telemetry=tel)
    r.expand_kit("tel-engineer")

    loaded_events = [e for e in captured if e["event_type"] == "plugin.loaded"]
    assert len(loaded_events) >= 2
    loaded_names = [e["payload"]["plugin"] for e in loaded_events]
    assert "core-kit" in loaded_names
    assert "tel-engineer" in loaded_names


def test_find_does_not_emit_telemetry(tmp_path: Path):
    from claude_kit.resolver import PluginResolver

    from claude_kit.telemetry import TelemetryEmitter

    _make_plugin(tmp_path, "quiet-plugin")
    captured: list[dict] = []
    tel = TelemetryEmitter(level="debug", on_emit=captured.append)
    r = PluginResolver(plugins_dirs=[tmp_path], telemetry=tel)
    r.find("quiet-plugin")
    assert captured == []


# ── Export from claude_kit ────────────────────────────────────────────────


def test_resolver_exported_from_package():
    from claude_kit import PluginResolver  # noqa: F401

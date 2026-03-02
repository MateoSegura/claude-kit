"""Tests for claude_kit.session — SessionManager contracts.

TDD: These tests define the expected behavior of the SessionManager
before implementation. Uses tmp_path fixtures to build plugin trees.
"""

from __future__ import annotations

import json
from pathlib import Path


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


def test_session_manager_importable():
    from claude_kit.session import SessionManager  # noqa: F401


def test_session_manager_exported_from_package():
    from claude_kit import SessionManager  # noqa: F401


def test_session_manager_requires_resolver(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    assert mgr.resolver is resolver


def test_session_manager_accepts_telemetry(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver
    from claude_kit.telemetry import TelemetryEmitter

    tel = TelemetryEmitter(level="debug")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver, telemetry=tel)
    assert mgr.telemetry is tel


def test_session_manager_telemetry_defaults_to_none(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    assert mgr.telemetry is None


# ── prepare() ────────────────────────────────────────────────────────────


def test_prepare_returns_session(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.models import Session
    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert isinstance(session, Session)


def test_prepare_populates_plugins(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert len(session.plugins) >= 1
    assert session.plugins[0].name == "core-kit"


def test_prepare_generates_session_id(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert session.session_id
    assert len(session.session_id) == 36  # UUID format


def test_prepare_session_ids_unique(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    s1 = mgr.prepare(kit_names=["core-kit"])
    s2 = mgr.prepare(kit_names=["core-kit"])
    assert s1.session_id != s2.session_id


def test_prepare_sets_ck_plugins_env(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert "CK_PLUGINS" in session.env_vars
    assert "core-kit" in session.env_vars["CK_PLUGINS"]


def test_prepare_sets_session_id_env(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert "CLAUDE_KIT_SESSION_ID" in session.env_vars
    assert session.env_vars["CLAUDE_KIT_SESSION_ID"] == session.session_id


def test_prepare_multiple_kits(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "team-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    _make_plugin(
        tmp_path,
        "team-tester",
        role="tester",
        domain="backend",
        companions=["core-kit"],
    )
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["team-engineer", "team-tester"])
    plugin_names = [p.name for p in session.plugins]
    assert "team-engineer" in plugin_names
    assert "team-tester" in plugin_names
    assert "core-kit" in plugin_names


def test_prepare_deduplicates_across_kits(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(
        tmp_path,
        "team-engineer",
        role="engineer",
        domain="backend",
        companions=["core-kit"],
    )
    _make_plugin(
        tmp_path,
        "team-tester",
        role="tester",
        domain="backend",
        companions=["core-kit"],
    )
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["team-engineer", "team-tester"])
    names = [p.name for p in session.plugins]
    assert names.count("core-kit") == 1


def test_prepare_sets_started_at(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    assert session.started_at
    assert "T" in session.started_at  # ISO 8601


# ── Telemetry Integration ────────────────────────────────────────────────


def test_prepare_emits_session_start(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver
    from claude_kit.telemetry import TelemetryEmitter

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    captured: list[dict] = []
    tel = TelemetryEmitter(level="debug", on_emit=captured.append)
    resolver = PluginResolver(plugins_dirs=[tmp_path], telemetry=tel)
    mgr = SessionManager(resolver=resolver, telemetry=tel)
    mgr.prepare(kit_names=["core-kit"])
    starts = [e for e in captured if e["event_type"] == "session.start"]
    assert len(starts) == 1
    assert "core-kit" in starts[0]["payload"]["plugins"]


def test_prepare_emits_cli_version(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver
    from claude_kit.telemetry import TelemetryEmitter

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    captured: list[dict] = []
    tel = TelemetryEmitter(level="debug", on_emit=captured.append)
    resolver = PluginResolver(plugins_dirs=[tmp_path], telemetry=tel)
    mgr = SessionManager(resolver=resolver, telemetry=tel)
    mgr.prepare(kit_names=["core-kit"], cli_version="0.14.0")
    starts = [e for e in captured if e["event_type"] == "session.start"]
    assert starts[0]["payload"]["cli_version"] == "0.14.0"


def test_no_telemetry_no_crash(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    # Should not raise
    mgr.finalize(session)


# ── finalize() ───────────────────────────────────────────────────────────


def test_finalize_emits_session_end(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver
    from claude_kit.telemetry import TelemetryEmitter

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    captured: list[dict] = []
    tel = TelemetryEmitter(level="debug", on_emit=captured.append)
    resolver = PluginResolver(plugins_dirs=[tmp_path], telemetry=tel)
    mgr = SessionManager(resolver=resolver, telemetry=tel)
    session = mgr.prepare(kit_names=["core-kit"])
    mgr.finalize(session)
    ends = [e for e in captured if e["event_type"] == "session.end"]
    assert len(ends) == 1


def test_finalize_sets_ended_at(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    mgr.finalize(session)
    assert session.ended_at
    assert "T" in session.ended_at


def test_finalize_cleans_decrypted_dirs(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    # Simulate a decrypted temp dir
    temp = tmp_path / "ck-temp"
    temp.mkdir()
    session.decrypted_dirs.append(temp)
    mgr.finalize(session)
    assert not temp.exists()


# ── build_env_vars() ─────────────────────────────────────────────────────


def test_build_env_vars_has_plugins(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    _make_plugin(tmp_path, "my-eng", role="engineer", domain="backend")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit", "my-eng"])
    env = mgr.build_env_vars(session)
    assert "CK_PLUGINS" in env
    assert "core-kit" in env["CK_PLUGINS"]
    assert "my-eng" in env["CK_PLUGINS"]


def test_build_env_vars_has_session_id(tmp_path: Path):
    from claude_kit.session import SessionManager

    from claude_kit.resolver import PluginResolver

    _make_plugin(tmp_path, "core-kit", role="system", domain="universal")
    resolver = PluginResolver(plugins_dirs=[tmp_path])
    mgr = SessionManager(resolver=resolver)
    session = mgr.prepare(kit_names=["core-kit"])
    env = mgr.build_env_vars(session)
    assert env["CLAUDE_KIT_SESSION_ID"] == session.session_id

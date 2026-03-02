"""Tests for claude_kit.models — data model contracts.

TDD: These tests define the expected API surface and behavior of the
Plugin, Session, and TelemetryEvent dataclasses before implementation.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path


def test_plugin_is_dataclass():
    from claude_kit.models import Plugin

    assert dataclasses.is_dataclass(Plugin)


def test_plugin_required_fields():
    from claude_kit.models import Plugin

    p = Plugin(
        name="core-kit",
        path=Path("/tmp/plugins/core-kit"),
        version="0.1.0",
        role="system",
        domain="universal",
    )
    assert p.name == "core-kit"
    assert p.path == Path("/tmp/plugins/core-kit")
    assert p.version == "0.1.0"
    assert p.role == "system"
    assert p.domain == "universal"


def test_plugin_companions_default_empty():
    from claude_kit.models import Plugin

    p = Plugin(
        name="test",
        path=Path("/tmp"),
        version="0.1.0",
        role="knowledge",
        domain="universal",
    )
    assert p.companions == []


def test_plugin_companions_explicit():
    from claude_kit.models import Plugin

    p = Plugin(
        name="embedded-zephyr-engineer",
        path=Path("/tmp"),
        version="0.1.0",
        role="engineer",
        domain="embedded",
        companions=["embedded-zephyr-knowledge", "core-kit"],
    )
    assert p.companions == ["embedded-zephyr-knowledge", "core-kit"]


def test_plugin_instances_are_independent():
    """Verify mutable default (companions list) is not shared."""
    from claude_kit.models import Plugin

    p1 = Plugin(name="a", path=Path("/a"), version="1", role="r", domain="d")
    p2 = Plugin(name="b", path=Path("/b"), version="1", role="r", domain="d")
    p1.companions.append("x")
    assert p2.companions == []


def test_session_is_dataclass():
    from claude_kit.models import Session

    assert dataclasses.is_dataclass(Session)


def test_session_required_fields():
    from claude_kit.models import Session

    s = Session(session_id="abc-123")
    assert s.session_id == "abc-123"
    assert s.plugins == []
    assert s.env_vars == {}
    assert s.decrypted_dirs == []


def test_session_with_plugins():
    from claude_kit.models import Plugin, Session

    p = Plugin(
        name="core-kit",
        path=Path("/tmp"),
        version="0.1.0",
        role="system",
        domain="universal",
    )
    s = Session(session_id="test", plugins=[p])
    assert len(s.plugins) == 1
    assert s.plugins[0].name == "core-kit"


def test_session_env_vars():
    from claude_kit.models import Session

    s = Session(
        session_id="test",
        env_vars={"CK_PLUGINS": "core-kit", "CK_MODE": "dev"},
    )
    assert s.env_vars["CK_PLUGINS"] == "core-kit"
    assert s.env_vars["CK_MODE"] == "dev"


def test_session_mutable_defaults_independent():
    """Verify mutable defaults are not shared between instances."""
    from claude_kit.models import Session

    s1 = Session(session_id="a")
    s2 = Session(session_id="b")
    s1.plugins.append("x")
    s1.env_vars["key"] = "val"
    assert s2.plugins == []
    assert s2.env_vars == {}


def test_telemetry_event_is_dataclass():
    from claude_kit.models import TelemetryEvent

    assert dataclasses.is_dataclass(TelemetryEvent)


def test_telemetry_event_required_fields():
    from claude_kit.models import TelemetryEvent

    e = TelemetryEvent(
        event_type="session.start",
        timestamp="2026-03-01T00:00:00+00:00",
        session_id="abc-123",
    )
    assert e.event_type == "session.start"
    assert e.timestamp == "2026-03-01T00:00:00+00:00"
    assert e.session_id == "abc-123"
    assert e.payload == {}
    assert e.schema_version == 1


def test_telemetry_event_with_payload():
    from claude_kit.models import TelemetryEvent

    e = TelemetryEvent(
        event_type="plugin.loaded",
        timestamp="2026-03-01T00:00:00+00:00",
        session_id="abc",
        payload={"plugin": "core-kit", "role": "system"},
    )
    assert e.payload["plugin"] == "core-kit"
    assert e.payload["role"] == "system"


def test_telemetry_event_custom_schema_version():
    from claude_kit.models import TelemetryEvent

    e = TelemetryEvent(
        event_type="test",
        timestamp="now",
        session_id="x",
        schema_version=2,
    )
    assert e.schema_version == 2


def test_telemetry_event_to_dict():
    """TelemetryEvent should be convertible to a dict via dataclasses.asdict."""
    from claude_kit.models import TelemetryEvent

    e = TelemetryEvent(
        event_type="session.start",
        timestamp="2026-03-01T00:00:00+00:00",
        session_id="abc-123",
        payload={"plugins": ["core-kit"]},
    )
    d = dataclasses.asdict(e)
    assert d["event_type"] == "session.start"
    assert d["payload"]["plugins"] == ["core-kit"]
    assert d["schema_version"] == 1

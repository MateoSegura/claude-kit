"""Tests for claude_kit.telemetry — TelemetryEmitter contracts.

TDD: These tests define the expected behavior of the TelemetryEmitter
before extracting it from the CLI into the library.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Construction & Configuration ─────────────────────────────────────────


def test_emitter_importable():
    from claude_kit.telemetry import TelemetryEmitter  # noqa: F401


def test_emitter_default_is_off():
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter()
    assert e.level == "off"
    assert not e.active


def test_emitter_valid_levels():
    from claude_kit.telemetry import TelemetryEmitter

    for level in ("off", "debug", "local", "full"):
        e = TelemetryEmitter(level=level)
        assert e.level == level


def test_emitter_invalid_level_defaults_to_off():
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="garbage")
    assert e.level == "off"


def test_emitter_has_session_id():
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="debug")
    assert e.session_id
    assert isinstance(e.session_id, str)
    assert len(e.session_id) == 36  # UUID format


def test_emitter_session_ids_are_unique():
    from claude_kit.telemetry import TelemetryEmitter

    e1 = TelemetryEmitter(level="debug")
    e2 = TelemetryEmitter(level="debug")
    assert e1.session_id != e2.session_id


def test_emitter_active_property():
    from claude_kit.telemetry import TelemetryEmitter

    assert not TelemetryEmitter(level="off").active
    assert TelemetryEmitter(level="debug").active
    assert TelemetryEmitter(level="local").active
    assert TelemetryEmitter(level="full").active


# ── Off Mode ─────────────────────────────────────────────────────────────


def test_off_produces_no_jsonl(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="off", telemetry_dir=tmp_path)
    e.emit("test.event", {"key": "value"})
    assert list(tmp_path.iterdir()) == []


def test_off_does_not_buffer():
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="off")
    e.emit("test.event", {"key": "value"})
    assert e.flush_buffer() == []


def test_off_does_not_call_on_emit():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="off", on_emit=captured.append)
    e.emit("test.event", {"key": "value"})
    assert captured == []


# ── Debug Mode ───────────────────────────────────────────────────────────


def test_debug_calls_on_emit():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="debug", on_emit=captured.append)
    e.emit("test.event", {"key": "value"})
    assert len(captured) == 1
    assert captured[0]["event_type"] == "test.event"
    assert captured[0]["payload"]["key"] == "value"
    assert captured[0]["session_id"] == e.session_id


def test_debug_does_not_write_jsonl(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="debug", telemetry_dir=tmp_path)
    e.emit("test.event", {"key": "value"})
    assert list(tmp_path.glob("*.jsonl")) == []


def test_debug_does_not_buffer():
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="debug")
    e.emit("test.event")
    assert e.flush_buffer() == []


# ── Local Mode ───────────────────────────────────────────────────────────


def test_local_writes_jsonl(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="local", telemetry_dir=tmp_path)
    e.emit("test.event", {"key": "value"})
    e.close()
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1


def test_local_jsonl_is_valid_json(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="local", telemetry_dir=tmp_path)
    e.emit("first.event", {"a": 1})
    e.emit("second.event", {"b": 2})
    e.close()

    jsonl_file = next(tmp_path.glob("*.jsonl"))
    lines = jsonl_file.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        event = json.loads(line)
        assert "event_type" in event
        assert "timestamp" in event
        assert "session_id" in event
        assert "payload" in event
        assert "schema_version" in event


def test_local_jsonl_filename_is_session_id(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="local", telemetry_dir=tmp_path)
    e.emit("test.event")
    e.close()

    jsonl_file = next(tmp_path.glob("*.jsonl"))
    assert jsonl_file.stem == e.session_id


def test_local_calls_on_emit(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="local", telemetry_dir=tmp_path, on_emit=captured.append)
    e.emit("test.event")
    e.close()
    assert len(captured) == 1


def test_local_does_not_buffer(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="local", telemetry_dir=tmp_path)
    e.emit("test.event")
    assert e.flush_buffer() == []


# ── Full Mode ────────────────────────────────────────────────────────────


def test_full_writes_jsonl_and_buffers(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="full", telemetry_dir=tmp_path)
    e.emit("test.event", {"x": 1})
    assert len(e.flush_buffer()) == 1
    e.close()
    assert len(list(tmp_path.glob("*.jsonl"))) == 1


def test_full_flush_clears_buffer(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    e = TelemetryEmitter(level="full", telemetry_dir=tmp_path)
    e.emit("a")
    e.emit("b")
    batch = e.flush_buffer()
    assert len(batch) == 2
    assert e.flush_buffer() == []


# ── Event Schema ─────────────────────────────────────────────────────────


def test_event_has_required_fields():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="debug", on_emit=captured.append)
    e.emit("plugin.loaded", {"plugin": "core-kit"})

    event = captured[0]
    assert event["schema_version"] == 1
    assert event["event_type"] == "plugin.loaded"
    assert isinstance(event["timestamp"], str)
    assert event["session_id"] == e.session_id
    assert event["payload"]["plugin"] == "core-kit"


def test_emit_with_none_payload():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="debug", on_emit=captured.append)
    e.emit("test.event")
    assert captured[0]["payload"] == {}


# ── Session Events ───────────────────────────────────────────────────────


def test_emit_session_start():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="debug", on_emit=captured.append)
    e.emit_session_start(
        plugins=["core-kit", "core-git"],
        cli_version="0.14.0",
    )
    event = captured[0]
    assert event["event_type"] == "session.start"
    assert event["payload"]["plugins"] == ["core-kit", "core-git"]
    assert event["payload"]["cli_version"] == "0.14.0"


def test_emit_session_end():
    from claude_kit.telemetry import TelemetryEmitter

    captured: list[dict] = []
    e = TelemetryEmitter(level="debug", on_emit=captured.append)
    e.emit("plugin.loaded", {"plugin": "core-kit"})
    e.emit("skill.invoked", {"skill": "routing"})
    e.emit("skill.invoked", {"skill": "routing"})
    e.emit("hook.fired", {"hook_event": "PostToolUse"})
    e.emit("autorouter.match", {"intent": "test"})
    e.emit("autorouter.miss", {"intent": "test2"})
    e.emit_session_end()

    end_event = [ev for ev in captured if ev["event_type"] == "session.end"][0]
    payload = end_event["payload"]
    assert payload["plugins_loaded"] == 1
    assert payload["skills_invoked"] == {"routing": 2}
    assert payload["hooks_fired"] == {"PostToolUse": 1}
    assert payload["autorouter_matches"] == 1
    assert payload["autorouter_misses"] == 1
    assert isinstance(payload["duration_s"], float)


# ── Telemetry Dir Creation ───────────────────────────────────────────────


def test_telemetry_dir_created_on_init(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    subdir = tmp_path / "deep" / "nested" / "telemetry"
    assert not subdir.exists()
    TelemetryEmitter(level="local", telemetry_dir=subdir)
    assert subdir.exists()


def test_telemetry_dir_not_created_when_off(tmp_path: Path):
    from claude_kit.telemetry import TelemetryEmitter

    subdir = tmp_path / "should" / "not" / "exist"
    TelemetryEmitter(level="off", telemetry_dir=subdir)
    assert not subdir.exists()

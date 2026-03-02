"""Tests for claude_kit.ci_output — JsonlWriter contracts.

Validates structured JSONL event output: format correctness, timestamp
precision, payload merging, stream flushing, and multi-event sequencing.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from io import StringIO

# ── Import & Construction ────────────────────────────────────────────────


def test_jsonl_writer_importable():
    from claude_kit.ci_output import JsonlWriter  # noqa: F401


def test_jsonl_writer_exported_from_package():
    from claude_kit import JsonlWriter  # noqa: F401


def test_default_stream_is_stdout():
    from claude_kit.ci_output import JsonlWriter

    writer = JsonlWriter()
    assert writer._stream is sys.stdout


def test_custom_stream_receives_output():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event")
    output = buf.getvalue()
    assert len(output) > 0


# ── Output Format ────────────────────────────────────────────────────────


def test_output_is_valid_json_per_line():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("event.one", {"key": "value"})
    line = buf.getvalue().strip()
    parsed = json.loads(line)
    assert isinstance(parsed, dict)


def test_output_ends_with_newline():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event")
    assert buf.getvalue().endswith("\n")


# ── Timestamp Field ──────────────────────────────────────────────────────


def test_ts_field_is_iso8601_utc():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event")
    record = json.loads(buf.getvalue().strip())
    ts = record["ts"]
    # Must parse as a valid ISO 8601 datetime
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None
    # UTC offset should be +00:00
    assert parsed.utcoffset().total_seconds() == 0


def test_ts_field_is_recent():
    from claude_kit.ci_output import JsonlWriter

    before = datetime.now(timezone.utc)
    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event")
    after = datetime.now(timezone.utc)

    record = json.loads(buf.getvalue().strip())
    ts = datetime.fromisoformat(record["ts"])
    assert before <= ts <= after


# ── Type Field ───────────────────────────────────────────────────────────


def test_type_field_matches_event_type():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("session.start")
    record = json.loads(buf.getvalue().strip())
    assert record["type"] == "session.start"


def test_type_field_with_various_event_types():
    from claude_kit.ci_output import JsonlWriter

    for event_type in ("session.start", "plugin.loaded", "hook.fired", "error"):
        buf = StringIO()
        writer = JsonlWriter(stream=buf)
        writer.write_event(event_type)
        record = json.loads(buf.getvalue().strip())
        assert record["type"] == event_type


# ── Payload Handling ─────────────────────────────────────────────────────


def test_payload_fields_merged_into_record():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("plugin.loaded", {"name": "core-kit", "version": "0.1.0"})
    record = json.loads(buf.getvalue().strip())
    assert record["name"] == "core-kit"
    assert record["version"] == "0.1.0"
    # ts and type are still present alongside payload fields
    assert "ts" in record
    assert record["type"] == "plugin.loaded"


def test_none_payload_produces_no_extra_fields():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event", None)
    record = json.loads(buf.getvalue().strip())
    assert set(record.keys()) == {"ts", "type"}


def test_omitted_payload_produces_no_extra_fields():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event")
    record = json.loads(buf.getvalue().strip())
    assert set(record.keys()) == {"ts", "type"}


def test_empty_dict_payload_produces_no_extra_fields():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test.event", {})
    record = json.loads(buf.getvalue().strip())
    # Empty dict is falsy, so no extra fields
    assert set(record.keys()) == {"ts", "type"}


# ── Serialization ────────────────────────────────────────────────────────


def test_non_serializable_objects_use_str_fallback():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    obj = object()
    writer.write_event("test.event", {"thing": obj})
    record = json.loads(buf.getvalue().strip())
    # default=str converts non-serializable objects to their str() repr
    assert record["thing"] == str(obj)


def test_datetime_in_payload_serialized_via_str():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    writer.write_event("test.event", {"created": dt})
    record = json.loads(buf.getvalue().strip())
    assert record["created"] == str(dt)


def test_pathlib_path_serialized_via_str():
    from pathlib import Path

    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    p = Path("/tmp/test/output.json")
    writer.write_event("test.event", {"path": p})
    record = json.loads(buf.getvalue().strip())
    assert record["path"] == str(p)


# ── Stream Flushing ──────────────────────────────────────────────────────


def test_stream_is_flushed_after_each_write():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    flush_count = 0
    original_flush = buf.flush

    def counting_flush():
        nonlocal flush_count
        flush_count += 1
        original_flush()

    buf.flush = counting_flush
    writer = JsonlWriter(stream=buf)
    writer.write_event("event.one")
    assert flush_count == 1
    writer.write_event("event.two")
    assert flush_count == 2


# ── Multiple Events ──────────────────────────────────────────────────────


def test_multiple_events_produce_multiple_lines():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("event.one", {"n": 1})
    writer.write_event("event.two", {"n": 2})
    writer.write_event("event.three", {"n": 3})

    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 3


def test_each_line_is_independently_parseable():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("first", {"a": 1})
    writer.write_event("second", {"b": 2})
    writer.write_event("third", {"c": 3})

    lines = buf.getvalue().strip().splitlines()
    records = [json.loads(line) for line in lines]
    assert records[0]["type"] == "first"
    assert records[0]["a"] == 1
    assert records[1]["type"] == "second"
    assert records[1]["b"] == 2
    assert records[2]["type"] == "third"
    assert records[2]["c"] == 3


def test_timestamps_are_monotonically_ordered():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    for i in range(5):
        writer.write_event("tick", {"seq": i})

    lines = buf.getvalue().strip().splitlines()
    timestamps = [datetime.fromisoformat(json.loads(line)["ts"]) for line in lines]
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1]


# ── Edge Cases ───────────────────────────────────────────────────────────


def test_event_type_with_special_characters():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("session/start:v2")
    record = json.loads(buf.getvalue().strip())
    assert record["type"] == "session/start:v2"


def test_payload_with_nested_dict():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test", {"meta": {"nested": {"deep": True}}})
    record = json.loads(buf.getvalue().strip())
    assert record["meta"]["nested"]["deep"] is True


def test_payload_with_list_value():
    from claude_kit.ci_output import JsonlWriter

    buf = StringIO()
    writer = JsonlWriter(stream=buf)
    writer.write_event("test", {"plugins": ["a", "b", "c"]})
    record = json.loads(buf.getvalue().strip())
    assert record["plugins"] == ["a", "b", "c"]

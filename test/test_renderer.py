"""Tests for TerminalRenderer and JsonlWriter."""

from __future__ import annotations

import io
import json

from claude_kit.ci_output import JsonlWriter
from claude_kit.renderer import TerminalRenderer


class TestTerminalRenderer:
    """TerminalRenderer produces ANSI-formatted output."""

    def _make(self, **kwargs) -> tuple[TerminalRenderer, io.StringIO]:
        buf = io.StringIO()
        renderer = TerminalRenderer(stream=buf, **kwargs)
        return renderer, buf

    def test_header(self) -> None:
        r, buf = self._make()
        r.render_header("autonomous", ["core-kit"])
        out = buf.getvalue()
        assert "claude-kit" in out
        assert "autonomous" in out
        assert "core-kit" in out

    def test_assistant_text(self) -> None:
        r, buf = self._make()
        r.render_assistant_text("Hello world")
        out = buf.getvalue()
        assert "Claude" in out
        assert "Hello world" in out

    def test_tool_use_hidden_by_default(self) -> None:
        r, buf = self._make(show_tools=False)
        r.render_tool_use("Bash", "ls -la")
        assert buf.getvalue() == ""

    def test_tool_use_shown_when_enabled(self) -> None:
        r, buf = self._make(show_tools=True)
        r.render_tool_use("Bash", "ls -la")
        out = buf.getvalue()
        assert "Bash" in out
        assert "ls -la" in out

    def test_tool_result_hidden_by_default(self) -> None:
        r, buf = self._make(show_tools=False)
        r.render_tool_result("t1", False, "output")
        assert buf.getvalue() == ""

    def test_tool_result_error(self) -> None:
        r, buf = self._make(show_tools=True)
        r.render_tool_result("t1", True, "command failed")
        out = buf.getvalue()
        assert "error" in out
        assert "command failed" in out

    def test_human_response(self) -> None:
        r, buf = self._make()
        r.render_human_response("Yes, go ahead.")
        out = buf.getvalue()
        assert "auto-reply" in out
        assert "Yes, go ahead." in out

    def test_compact(self) -> None:
        r, buf = self._make()
        r.render_compact(tokens_before=128000)
        out = buf.getvalue()
        assert "compact" in out
        assert "128K" in out

    def test_compact_no_tokens(self) -> None:
        r, buf = self._make()
        r.render_compact()
        assert "compact" in buf.getvalue()

    def test_session_end(self) -> None:
        r, buf = self._make()
        r.render_session_end(
            turns=5,
            cost=0.18,
            tokens_in=52000,
            tokens_out=8000,
            elapsed=134.0,
        )
        out = buf.getvalue()
        assert "session complete" in out
        assert "Turns: 5" in out
        assert "$0.18" in out
        assert "52K in" in out
        assert "8K out" in out
        assert "2m 14s" in out

    def test_session_end_no_cost(self) -> None:
        r, buf = self._make()
        r.render_session_end(
            turns=1,
            cost=None,
            tokens_in=1000,
            tokens_out=500,
            elapsed=5.0,
        )
        out = buf.getvalue()
        assert "$" not in out
        assert "5s" in out

    def test_no_color(self) -> None:
        r, buf = self._make(color=False)
        r.render_assistant_text("plain text")
        out = buf.getvalue()
        assert "\033[" not in out
        assert "plain text" in out


class TestJsonlWriter:
    """JsonlWriter produces one JSON object per line."""

    def test_write_event(self) -> None:
        buf = io.StringIO()
        w = JsonlWriter(stream=buf)
        w.write_event("session.start", {"plugins": ["core-kit"]})
        line = buf.getvalue().strip()
        data = json.loads(line)
        assert data["type"] == "session.start"
        assert data["plugins"] == ["core-kit"]
        assert "ts" in data

    def test_write_event_no_payload(self) -> None:
        buf = io.StringIO()
        w = JsonlWriter(stream=buf)
        w.write_event("session.end")
        line = buf.getvalue().strip()
        data = json.loads(line)
        assert data["type"] == "session.end"

    def test_multiple_events(self) -> None:
        buf = io.StringIO()
        w = JsonlWriter(stream=buf)
        w.write_event("a", {"x": 1})
        w.write_event("b", {"y": 2})
        lines = buf.getvalue().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["type"] == "a"
        assert json.loads(lines[1])["type"] == "b"

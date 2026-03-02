"""Tests for SessionDriver display callbacks (on_event).

Verifies that SessionDriver fires on_event at the correct points with
expected event types and payload fields, without affecting existing behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from claude_kit.driver_config import DriverMode, SessionDriverConfig
from test.engine.config import EvalScenario, RunConfig, Transcript

# --- Mock SDK types (same pattern as test_session_driver.py) ---


@dataclass
class MockTextBlock:
    text: str
    type: str = "text"


@dataclass
class MockToolUseBlock:
    name: str
    id: str
    input: dict[str, Any] = field(default_factory=dict)
    type: str = "tool_use"


@dataclass
class MockToolResultBlock:
    tool_use_id: str
    content: str = ""
    is_error: bool = False
    type: str = "tool_result"


@dataclass
class MockAssistantMessage:
    content: list[Any] = field(default_factory=list)
    model: str = "claude-sonnet-4-20250514"


@dataclass
class MockSystemMessage:
    subtype: str = ""
    data: Any = None


@dataclass
class MockResultMessage:
    num_turns: int = 1
    total_cost_usd: float = 0.01
    usage: dict[str, int] | None = None
    session_id: str = "test-session"
    duration_ms: int = 1000
    duration_api_ms: int = 800
    is_error: bool = False
    result: str = ""


# --- Helpers ---


def _make_patched_modules():
    """Create a dict of patches for SDK modules used by driver.py."""
    return {
        "ClaudeSDKClient": MagicMock,
        "query": MagicMock(),
        "_original_parse": MagicMock(),
        "AssistantMessage": MockAssistantMessage,
        "SystemMessage": MockSystemMessage,
        "ResultMessage": MockResultMessage,
        "TextBlock": MockTextBlock,
        "ToolUseBlock": MockToolUseBlock,
        "ToolResultBlock": MockToolResultBlock,
        "ThinkingBlock": None,
        "ClaudeCodeOptions": MagicMock,
    }


@pytest.fixture()
def scenario() -> EvalScenario:
    return EvalScenario(
        name="test-scenario",
        description="Test scenario",
        prompt="Write a hello world function",
        configs=[RunConfig(name="raw", plugins=[])],
        max_turns=10,
    )


@pytest.fixture()
def driver_config() -> SessionDriverConfig:
    return SessionDriverConfig(
        mode=DriverMode.AUTONOMOUS,
        model="claude-sonnet-4-20250514",
        max_turns=10,
    )


# --- Tests ---


class TestOnEventParameter:
    """Test that SessionDriver accepts and stores on_event."""

    def test_accepts_on_event(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            assert driver._on_event is recorder

    def test_defaults_to_noop(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            # Should not raise — no-op lambda
            driver._on_event("test.event", {"key": "value"})


class TestAssistantTextEvent:
    """Test on_event fires for assistant text messages."""

    def test_fires_assistant_text(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[MockTextBlock(text="Hello world")],
                model="claude-sonnet-4-20250514",
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            # Find the assistant.text call
            calls = [c for c in recorder.call_args_list if c[0][0] == "assistant.text"]
            assert len(calls) == 1
            payload = calls[0][0][1]
            assert payload["text"] == "Hello world"
            assert payload["model"] == "claude-sonnet-4-20250514"

    def test_no_text_no_assistant_event(self, scenario: EvalScenario) -> None:
        """When message has only tool use blocks, no assistant.text fires."""
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolUseBlock(name="Bash", id="t1", input={"cmd": "ls"}),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            text_calls = [
                c for c in recorder.call_args_list if c[0][0] == "assistant.text"
            ]
            assert len(text_calls) == 0


class TestToolUseEvent:
    """Test on_event fires for tool use blocks."""

    def test_fires_tool_use(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolUseBlock(
                        name="Bash", id="tool-1", input={"command": "ls -la"}
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "tool.use"]
            assert len(calls) == 1
            payload = calls[0][0][1]
            assert payload["name"] == "Bash"
            assert "input_preview" in payload


class TestToolResultEvent:
    """Test on_event fires for tool result blocks."""

    def test_fires_tool_result(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolResultBlock(
                        tool_use_id="tool-1",
                        content="file.txt",
                        is_error=False,
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "tool.result"]
            assert len(calls) == 1
            payload = calls[0][0][1]
            assert payload["tool_use_id"] == "tool-1"
            assert payload["is_error"] is False
            assert "preview" in payload

    def test_tool_result_error_flag(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolResultBlock(
                        tool_use_id="tool-2",
                        content="permission denied",
                        is_error=True,
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "tool.result"]
            assert len(calls) == 1
            assert calls[0][0][1]["is_error"] is True


class TestCompactEvent:
    """Test on_event fires for compact system messages."""

    def test_fires_session_compact(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockSystemMessage(subtype="auto_compact", data="compacted")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            driver._process_system_message(msg, 0, transcript, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "session.compact"]
            assert len(calls) == 1
            assert calls[0][0][1]["subtype"] == "auto_compact"

    def test_non_compact_no_event(self, scenario: EvalScenario) -> None:
        """Non-compact system messages should not fire session.compact."""
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockSystemMessage(subtype="info", data="some info")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            driver._process_system_message(msg, 0, transcript, events)

            compact_calls = [
                c for c in recorder.call_args_list if c[0][0] == "session.compact"
            ]
            assert len(compact_calls) == 0


class TestNoopDefault:
    """Verify that on_event=None does not break any existing behavior."""

    def test_process_assistant_without_callback(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                # on_event not provided — defaults to no-op
            )
            msg = MockAssistantMessage(
                content=[MockTextBlock(text="Hello")],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            # Should not raise
            tc, mc, turn, text = driver._process_assistant_message(
                msg, 0, transcript, responses, events
            )
            assert text == "Hello"
            assert turn == 1

    def test_process_system_without_callback(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockSystemMessage(subtype="auto_compact", data="data")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            # Should not raise
            count = driver._process_system_message(msg, 0, transcript, events)
            assert count == 1


class TestEventPayloadFields:
    """Verify event payloads contain expected fields."""

    def test_assistant_text_payload_fields(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[MockTextBlock(text="Test output")],
                model="claude-opus-4-20250514",
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "assistant.text"]
            payload = calls[0][0][1]
            assert "text" in payload
            assert "model" in payload
            assert payload["model"] == "claude-opus-4-20250514"

    def test_tool_use_payload_fields(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolUseBlock(name="Read", id="t-99", input={"path": "/tmp/x"}),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "tool.use"]
            payload = calls[0][0][1]
            assert "name" in payload
            assert "input_preview" in payload
            assert payload["name"] == "Read"

    def test_tool_result_payload_fields(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolResultBlock(
                        tool_use_id="t-99",
                        content="output data",
                        is_error=False,
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            driver._process_assistant_message(msg, 0, transcript, responses, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "tool.result"]
            payload = calls[0][0][1]
            assert "tool_use_id" in payload
            assert "is_error" in payload
            assert "preview" in payload

    def test_compact_payload_fields(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            recorder = MagicMock()
            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                on_event=recorder,
            )
            msg = MockSystemMessage(subtype="auto_compact", data="compacted")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            driver._process_system_message(msg, 0, transcript, events)

            calls = [c for c in recorder.call_args_list if c[0][0] == "session.compact"]
            payload = calls[0][0][1]
            assert "subtype" in payload
            assert payload["subtype"] == "auto_compact"

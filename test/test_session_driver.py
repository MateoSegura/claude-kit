"""Tests for SessionDriver — multi-turn session executor.

Tests use mocked SDK types to verify the driver logic without requiring
the actual Claude Code SDK or API access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_kit.driver_config import DriverMode, SessionDriverConfig
from test.engine.config import EvalScenario, RunConfig, Transcript

# --- Mock SDK types for testing ---


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


# --- Fixtures ---


@pytest.fixture()
def scenario() -> EvalScenario:
    return EvalScenario(
        name="test-scenario",
        description="Test scenario",
        prompt="Write a hello world function",
        configs=[
            RunConfig(name="raw", plugins=[]),
            RunConfig(name="kit", plugins=["core-kit"]),
        ],
        max_turns=10,
    )


@pytest.fixture()
def driver_config() -> SessionDriverConfig:
    return SessionDriverConfig(
        mode=DriverMode.AUTONOMOUS,
        model="claude-sonnet-4-20250514",
        max_turns=10,
    )


# --- Helper to run the driver with mocked SDK ---


def _make_patched_modules():
    """Create a dict of patches for SDK modules used by driver.py."""
    return {
        "ClaudeSDKClient": MagicMock,
        "query": AsyncMock,
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


class TestSessionDriverInit:
    """Test SessionDriver construction."""

    def test_creates_with_defaults(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            assert driver.scenario is scenario

    def test_accepts_custom_config(
        self,
        scenario: EvalScenario,
        driver_config: SessionDriverConfig,
    ) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
                driver_config=driver_config,
            )
            assert driver._config.mode == DriverMode.AUTONOMOUS


class TestBuildSystemPrompt:
    """Test system prompt construction from plugins."""

    def test_uses_config_system_prompt(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            config = RunConfig(name="test", plugins=[], system_prompt="custom prompt")
            prompt, events = driver._build_system_prompt(config)
            assert prompt == "custom prompt"
            assert any(e["event_type"] == "session.start" for e in events)

    def test_no_plugins_returns_none(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            config = RunConfig(name="raw", plugins=[])
            prompt, events = driver._build_system_prompt(config)
            assert prompt is None
            assert any(e["event_type"] == "session.start" for e in events)


class TestProcessAssistantMessage:
    """Test assistant message processing extracts telemetry correctly."""

    def test_text_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockAssistantMessage(
                content=[MockTextBlock(text="Hello world")],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            tc, mc, turn, text = driver._process_assistant_message(
                msg, 0, transcript, responses, events
            )

            assert tc == 0
            assert mc == 0
            assert turn == 1
            assert text == "Hello world"
            assert responses == ["Hello world"]
            assert any(e["event_type"] == "message.assistant" for e in events)
            assert any(e["event_type"] == "turn.completed" for e in events)

    def test_tool_use_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolUseBlock(
                        name="Bash",
                        id="tool-1",
                        input={"command": "ls"},
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            tc, mc, turn, text = driver._process_assistant_message(
                msg, 0, transcript, responses, events
            )

            assert tc == 1
            assert mc == 0
            assert text == ""
            assert any(e["event_type"] == "tool.used" for e in events)

    def test_mcp_tool_counted(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockAssistantMessage(
                content=[
                    MockToolUseBlock(
                        name="mcp__server__method",
                        id="tool-2",
                    ),
                ],
            )
            transcript: list[Transcript] = []
            responses: list[str] = []
            events: list[dict[str, Any]] = []

            tc, mc, _, _ = driver._process_assistant_message(
                msg, 0, transcript, responses, events
            )

            assert tc == 1
            assert mc == 1
            tool_event = next(e for e in events if e["event_type"] == "tool.used")
            assert tool_event["payload"]["is_mcp"] is True


class TestProcessSystemMessage:
    """Test system message processing."""

    def test_compact_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockSystemMessage(subtype="auto_compact", data="compacted")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            count = driver._process_system_message(msg, 0, transcript, events)

            assert count == 1
            assert any(e["event_type"] == "session.compact" for e in events)

    def test_non_compact_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            msg = MockSystemMessage(subtype="info", data="some info")
            transcript: list[Transcript] = []
            events: list[dict[str, Any]] = []

            count = driver._process_system_message(msg, 0, transcript, events)

            assert count == 0
            assert any(e["event_type"] == "message.system" for e in events)


class TestBuildRunResult:
    """Test RunResult construction from collected data."""

    def test_with_result_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            result_msg = MockResultMessage(
                num_turns=3,
                total_cost_usd=0.05,
                usage={"input_tokens": 1000, "output_tokens": 500},
                session_id="sess-123",
                duration_ms=5000,
                duration_api_ms=4000,
            )
            config = RunConfig(name="test", plugins=[])
            events: list[dict[str, Any]] = []

            result = driver._build_run_result(
                config=config,
                responses=["hello"],
                transcript=[],
                telemetry_events=events,
                result_msg=result_msg,
                turn_number=3,
                tool_counter=5,
                mcp_counter=1,
                compact_counter=0,
                elapsed=5.0,
            )

            assert result.config_name == "test"
            assert result.turns == 3
            assert result.cost_usd == 0.05
            assert result.total_tokens_in == 1000
            assert result.total_tokens_out == 500
            assert result.session_id == "sess-123"
            assert result.tool_use_count == 5
            assert result.mcp_call_count == 1

    def test_without_result_message(self, scenario: EvalScenario) -> None:
        from test.engine.input_strategies import TerminalInput

        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.driver import SessionDriver

            driver = SessionDriver(
                scenario=scenario,
                input_strategy=TerminalInput(),
            )
            config = RunConfig(name="test", plugins=[])
            events: list[dict[str, Any]] = []

            result = driver._build_run_result(
                config=config,
                responses=["hello", "world"],
                transcript=[],
                telemetry_events=events,
                result_msg=None,
                turn_number=2,
                tool_counter=0,
                mcp_counter=0,
                compact_counter=0,
                elapsed=2.0,
            )

            # Falls back to len(responses) for turns
            assert result.turns == 2
            assert result.cost_usd is None

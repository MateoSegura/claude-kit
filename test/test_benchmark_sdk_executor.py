"""Tests for SdkExecutor — drives benchmark conversations via Claude Code SDK.

Mocks claude_code_sdk.query to avoid real API calls. Mirrors the pattern
from test_engine_executor.py.
"""

from __future__ import annotations

import pytest

try:
    import claude_code_sdk  # noqa: F401
except ModuleNotFoundError:
    claude_code_sdk = None  # type: ignore[assignment]

from unittest.mock import patch

from test.engine.config import (
    EvalScenario,
    RunConfig,
    RunResult,
)
from test.engine.sdk_executor import SdkExecutor

skip_no_sdk = pytest.mark.skipif(
    claude_code_sdk is None,
    reason="claude-code-sdk not installed",
)


# ── Helpers ──────────────────────────────────────────────


def _make_scenario(**overrides) -> EvalScenario:
    defaults = {
        "name": "test",
        "description": "test scenario",
        "prompt": "Say hello",
        "configs": [RunConfig(name="raw", plugins=[])],
        "max_turns": 1,
    }
    defaults.update(overrides)
    return EvalScenario(**defaults)


def _make_assistant_message(text: str):
    """Create a mock AssistantMessage with a TextBlock."""
    from claude_code_sdk.types import AssistantMessage, TextBlock

    return AssistantMessage(
        content=[TextBlock(text=text)],
        model="claude-haiku-4-5-20251001",
    )


def _make_result_message(**overrides):
    """Create a mock ResultMessage."""
    from claude_code_sdk.types import ResultMessage

    defaults = {
        "subtype": "result",
        "duration_ms": 1500,
        "duration_api_ms": 1200,
        "is_error": False,
        "num_turns": 1,
        "session_id": "test-session-123",
        "total_cost_usd": 0.001,
        "usage": {"input_tokens": 100, "output_tokens": 50},
        "result": None,
    }
    defaults.update(overrides)
    return ResultMessage(**defaults)


async def _mock_query_generator(messages):
    """Async generator that yields mock messages."""
    for msg in messages:
        yield msg


# ── Construction ─────────────────────────────────────────


def test_sdk_executor_importable():
    """SdkExecutor is importable."""
    assert callable(SdkExecutor)


def test_sdk_executor_accepts_scenario():
    """Executor accepts an EvalScenario."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)
    assert executor.scenario is scenario


# ── Single run execution ─────────────────────────────────


@skip_no_sdk
def test_execute_returns_run_result():
    """execute returns a RunResult dataclass."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hello!")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert isinstance(result, RunResult)
    assert result.config_name == "raw"
    assert result.turns == 1
    assert len(result.responses) == 1
    assert result.responses[0] == "Hello!"


@skip_no_sdk
def test_execute_captures_cost():
    """execute captures real cost from ResultMessage."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hi!")
    result_msg = _make_result_message(total_cost_usd=0.0042)

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.cost_usd == 0.0042
    assert result.estimated_cost_usd == 0.0042


@skip_no_sdk
def test_execute_captures_tokens():
    """execute extracts token counts from ResultMessage.usage."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hello!")
    result_msg = _make_result_message(
        usage={"input_tokens": 200, "output_tokens": 75},
    )

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.total_tokens_in == 200
    assert result.total_tokens_out == 75


@skip_no_sdk
def test_execute_handles_no_response():
    """execute returns 0 turns when SDK yields no assistant messages."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    # Simulate a session that produces a result but no assistant text
    result_msg = _make_result_message(
        num_turns=0,
        is_error=True,
        result="No response generated",
    )

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.turns == 0
    assert len(result.responses) == 0
    # Session error recorded in telemetry
    error_events = [
        e for e in result.telemetry_events if e.get("event_type") == "session.error"
    ]
    assert len(error_events) == 1


@skip_no_sdk
def test_execute_raw_no_system_prompt():
    """Raw config sends no system_prompt in options."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hello!")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        executor.execute(RunConfig(name="raw", plugins=[]))

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.system_prompt is None


@skip_no_sdk
def test_execute_with_system_prompt():
    """Config with system_prompt passes it through to options."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hello!")
    result_msg = _make_result_message()
    config = RunConfig(name="kit", plugins=[], system_prompt="Be helpful.")

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        executor.execute(config)

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.system_prompt == "Be helpful."


@skip_no_sdk
def test_execute_builds_transcript():
    """execute builds a transcript with user and assistant entries."""
    scenario = _make_scenario(prompt="What is 2+2?")
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Four.")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert len(result.transcript) == 2
    assert result.transcript[0].role == "user"
    assert result.transcript[0].content == "What is 2+2?"
    assert result.transcript[1].role == "assistant"
    assert result.transcript[1].content == "Four."


@skip_no_sdk
def test_execute_records_telemetry_events():
    """execute emits session.start and session.end telemetry."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hi!")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    event_types = [e["event_type"] for e in result.telemetry_events]
    assert "session.end" in event_types


@skip_no_sdk
def test_execute_model_passed_to_options():
    """execute passes the scenario model to ClaudeCodeOptions."""
    scenario = _make_scenario(model="claude-haiku-4-5-20251001")
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hi!")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        executor.execute(RunConfig(name="raw", plugins=[]))

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.model == "claude-haiku-4-5-20251001"


# ── Per-message telemetry ────────────────────────────────


def _make_tool_use_block(name: str, tool_id: str, input_data: dict | None = None):
    """Create a mock ToolUseBlock."""
    from claude_code_sdk.types import ToolUseBlock

    return ToolUseBlock(name=name, id=tool_id, input=input_data or {})


def _make_tool_result_block(
    tool_use_id: str, content: str = "ok", is_error: bool = False
):
    """Create a mock ToolResultBlock."""
    from claude_code_sdk.types import ToolResultBlock

    return ToolResultBlock(tool_use_id=tool_use_id, content=content, is_error=is_error)


def _make_system_message(subtype: str, data: str | None = None):
    """Create a mock SystemMessage."""
    from claude_code_sdk.types import SystemMessage

    return SystemMessage(subtype=subtype, data=data)


def _make_assistant_with_tools(text: str, tools: list):
    """Create a mock AssistantMessage with text and tool blocks."""
    from claude_code_sdk.types import AssistantMessage, TextBlock

    content = [TextBlock(text=text)] + tools
    return AssistantMessage(content=content, model="claude-haiku-4-5-20251001")


@skip_no_sdk
def test_execute_emits_turn_completed():
    """turn.completed events are emitted per assistant message."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    a1 = _make_assistant_message("First")
    a2 = _make_assistant_message("Second")
    result_msg = _make_result_message(num_turns=2)

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([a1, a2, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    turn_events = [
        e for e in result.telemetry_events if e.get("event_type") == "turn.completed"
    ]
    assert len(turn_events) == 2
    assert turn_events[0]["payload"]["turn"] == 1
    assert turn_events[1]["payload"]["turn"] == 2


@skip_no_sdk
def test_execute_emits_tool_used():
    """tool.used events are emitted from ToolUseBlock."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    tool_block = _make_tool_use_block("Read", "tu-1", {"path": "/tmp/x"})
    assistant = _make_assistant_with_tools("Reading file", [tool_block])
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    tool_events = [
        e for e in result.telemetry_events if e.get("event_type") == "tool.used"
    ]
    assert len(tool_events) == 1
    assert tool_events[0]["payload"]["tool_name"] == "Read"
    assert tool_events[0]["payload"]["tool_use_id"] == "tu-1"
    assert tool_events[0]["payload"]["is_mcp"] is False
    assert result.tool_use_count == 1


@skip_no_sdk
def test_execute_detects_mcp_calls():
    """mcp__ prefix is detected and parsed into server/method."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    mcp_block = _make_tool_use_block("mcp__github__get_issue", "tu-mcp", {"number": 42})
    assistant = _make_assistant_with_tools("Checking issue", [mcp_block])
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    tool_events = [
        e for e in result.telemetry_events if e.get("event_type") == "tool.used"
    ]
    assert len(tool_events) == 1
    assert tool_events[0]["payload"]["is_mcp"] is True
    assert tool_events[0]["payload"]["mcp_server"] == "github"
    assert tool_events[0]["payload"]["mcp_method"] == "get_issue"
    assert result.mcp_call_count == 1
    assert result.tool_use_count == 1


@skip_no_sdk
def test_execute_emits_session_result():
    """session.result event contains full usage dict."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hello!")
    result_msg = _make_result_message(
        usage={"input_tokens": 300, "output_tokens": 100},
        total_cost_usd=0.005,
        session_id="sess-xyz",
        duration_ms=2000,
        duration_api_ms=1800,
    )

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    result_events = [
        e for e in result.telemetry_events if e.get("event_type") == "session.result"
    ]
    assert len(result_events) == 1
    payload = result_events[0]["payload"]
    assert payload["usage"]["input_tokens"] == 300
    assert payload["cost_usd"] == 0.005
    assert payload["session_id"] == "sess-xyz"
    assert payload["duration_ms"] == 2000
    assert payload["duration_api_ms"] == 1800


@skip_no_sdk
def test_execute_tracks_compact():
    """SystemMessage with compact subtype emits session.compact."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hi!")
    sys_msg = _make_system_message(subtype="auto_compact", data="reduced")
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator(
            [assistant, sys_msg, result_msg]
        )
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    compact_events = [
        e for e in result.telemetry_events if e.get("event_type") == "session.compact"
    ]
    assert len(compact_events) == 1
    assert compact_events[0]["payload"]["subtype"] == "auto_compact"
    assert result.compact_count == 1


@skip_no_sdk
def test_execute_populates_usage_dict():
    """RunResult.usage is populated from ResultMessage."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    assistant = _make_assistant_message("Hi!")
    result_msg = _make_result_message(
        usage={
            "input_tokens": 500,
            "output_tokens": 200,
            "cache_read_input_tokens": 50,
        },
    )

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.usage["input_tokens"] == 500
    assert result.usage["output_tokens"] == 200
    assert result.usage["cache_read_input_tokens"] == 50
    assert result.session_id == "test-session-123"
    assert result.duration_ms == 1500


@skip_no_sdk
def test_execute_transcript_includes_tools():
    """Transcript includes tool_use and tool_result entries."""
    scenario = _make_scenario()
    executor = SdkExecutor(scenario)

    tool_block = _make_tool_use_block("Bash", "tu-2", {"command": "ls"})
    assistant = _make_assistant_with_tools("Running ls", [tool_block])
    result_msg = _make_result_message()

    with patch("test.engine.sdk_executor.query") as mock_query:
        mock_query.return_value = _mock_query_generator([assistant, result_msg])
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    tool_entries = [t for t in result.transcript if t.role == "tool_use"]
    assert len(tool_entries) == 1
    assert tool_entries[0].tool_name == "Bash"
    assert tool_entries[0].tool_use_id == "tu-2"

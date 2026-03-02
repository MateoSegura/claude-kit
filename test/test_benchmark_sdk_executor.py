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

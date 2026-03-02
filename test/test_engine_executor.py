"""Tests for ConversationExecutor — drives benchmark conversations.

TDD: Ports the benchmark runner tests to the engine layer.
The executor drives a conversation via the Anthropic SDK,
uses the HumanSimulator when Claude needs input, captures
telemetry via the claude_kit library, and returns structured
results for comparison.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from test.engine.config import (
    EvalScenario,
    RunConfig,
    RunResult,
)
from test.engine.executor import ConversationExecutor

# ── Construction ─────────────────────────────────────────


def test_executor_importable():
    """ConversationExecutor is importable."""
    assert callable(ConversationExecutor)


def test_executor_accepts_scenario():
    """Executor accepts an EvalScenario."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
    )
    executor = ConversationExecutor(scenario)
    assert executor.scenario is scenario


def test_executor_creates_human_simulator():
    """Executor creates a HumanSimulator internally."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
    )
    executor = ConversationExecutor(scenario)
    assert executor.human is not None


# ── Single run execution ─────────────────────────────────


def test_execute_returns_run_result():
    """execute returns a RunResult dataclass."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Say hello",
        configs=[RunConfig(name="raw", plugins=[])],
        max_turns=1,
    )
    executor = ConversationExecutor(scenario)

    # Mock the Anthropic client
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Hello!")]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 5

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert isinstance(result, RunResult)
    assert result.config_name == "raw"
    assert result.turns >= 1
    assert len(result.responses) >= 1


def test_execute_raw_no_system_prompt():
    """Raw Claude config sends no system prompt."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Say hello",
        configs=[RunConfig(name="raw", plugins=[])],
        max_turns=1,
    )
    executor = ConversationExecutor(scenario)

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Hello!")]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 5

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        executor.execute(RunConfig(name="raw", plugins=[]))

        call_kwargs = client.messages.create.call_args
        # Should NOT have system prompt for raw config
        assert "system" not in call_kwargs.kwargs


def test_execute_kit_has_system_prompt(tmp_path):
    """Kit config builds a system prompt from plugins."""
    import json

    # Create a minimal plugin with a skill
    plugin_dir = tmp_path / "test-plugin"
    meta = plugin_dir / ".claude-plugin"
    meta.mkdir(parents=True)
    (meta / "plugin.json").write_text(
        json.dumps(
            {
                "name": "test-plugin",
                "description": "t",
                "version": "0.0.1",
            }
        )
    )
    (meta / "ctl.json").write_text(
        json.dumps(
            {
                "role": "knowledge",
                "domain": "universal",
            }
        )
    )
    skill_dir = plugin_dir / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test\ndescription: t\n---\n\n# Test Skill\n\nBe excellent."
    )

    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Say hello",
        configs=[
            RunConfig(
                name="kit",
                plugins=["test-plugin"],
            ),
        ],
        max_turns=1,
    )
    executor = ConversationExecutor(scenario, plugins_dirs=[tmp_path])

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Hello!")]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 5

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        result = executor.execute(
            RunConfig(
                name="kit",
                plugins=["test-plugin"],
            )
        )

        call_kwargs = client.messages.create.call_args
        # SHOULD have system prompt for kit config
        assert "system" in call_kwargs.kwargs
        assert "Test Skill" in call_kwargs.kwargs["system"]

    assert result.config_name == "kit"
    assert len(result.telemetry_events) > 0


def test_execute_respects_max_turns():
    """Executor stops after max_turns even if conversation continues."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Keep talking",
        configs=[RunConfig(name="raw", plugins=[])],
        max_turns=2,
    )
    executor = ConversationExecutor(scenario)

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="What should I do next?")]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 5

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.turns <= 2


def test_execute_tracks_tokens():
    """Executor accumulates token counts across turns."""
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Hi",
        configs=[RunConfig(name="raw", plugins=[])],
        max_turns=1,
    )
    executor = ConversationExecutor(scenario)

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Hello!")]
    mock_msg.usage.input_tokens = 100
    mock_msg.usage.output_tokens = 50

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        result = executor.execute(RunConfig(name="raw", plugins=[]))

    assert result.total_tokens_in == 100
    assert result.total_tokens_out == 50

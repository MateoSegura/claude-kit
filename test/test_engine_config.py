"""Tests for engine configuration and data models.

TDD: Ports the benchmark config tests to the engine layer,
using the unified types: EvalScenario (was BenchmarkScenario),
RunConfig, RunResult, BenchmarkResult, and Transcript.
"""

from __future__ import annotations

from test.engine.config import (
    BenchmarkResult,
    EvalScenario,
    RunConfig,
    RunResult,
    Transcript,
)

# ── EvalScenario ────────────────────────────────────────


def test_scenario_has_required_fields():
    """Scenario must have name, prompt, and configs."""
    s = EvalScenario(
        name="test",
        description="A test scenario",
        prompt="Add a /health endpoint",
        configs=[
            RunConfig(name="raw", plugins=[]),
        ],
    )
    assert s.name == "test"
    assert s.prompt == "Add a /health endpoint"
    assert len(s.configs) == 1


def test_scenario_defaults():
    """Scenario should have sensible defaults."""
    s = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
    )
    assert s.model == "claude-sonnet-4-20250514"
    assert s.max_turns == 20
    assert s.runs == 1


def test_scenario_custom_values():
    """Scenario accepts custom model, max_turns, runs."""
    s = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
        model="claude-haiku-4-5-20251001",
        max_turns=5,
        runs=3,
    )
    assert s.model == "claude-haiku-4-5-20251001"
    assert s.max_turns == 5
    assert s.runs == 3


def test_scenario_max_tokens_default():
    """EvalScenario has a max_tokens field with default 4096."""
    s = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
    )
    assert s.max_tokens == 4096


def test_scenario_max_tokens_custom():
    """EvalScenario accepts a custom max_tokens value."""
    s = EvalScenario(
        name="test",
        description="test",
        prompt="do something",
        configs=[RunConfig(name="raw", plugins=[])],
        max_tokens=8192,
    )
    assert s.max_tokens == 8192


# ── RunConfig ────────────────────────────────────────────


def test_run_config_raw_claude():
    """A raw Claude config has no plugins."""
    rc = RunConfig(name="raw-claude", plugins=[])
    assert rc.name == "raw-claude"
    assert rc.plugins == []


def test_run_config_with_plugins():
    """A kit config has plugin names."""
    rc = RunConfig(
        name="cloud-python",
        plugins=["cloud-python-engineer"],
    )
    assert rc.plugins == ["cloud-python-engineer"]


def test_run_config_system_prompt_override():
    """Config can have an optional system prompt override."""
    rc = RunConfig(
        name="custom",
        plugins=[],
        system_prompt="You are a helpful assistant.",
    )
    assert rc.system_prompt == "You are a helpful assistant."


# ── Transcript ──────────────────────────────────────────


def test_transcript_basic():
    """Transcript stores role and content."""
    t = Transcript(role="user", content="Hello")
    assert t.role == "user"
    assert t.content == "Hello"
    assert t.tokens_in == 0
    assert t.tokens_out == 0


def test_transcript_with_tokens():
    """Transcript stores token counts for assistant turns."""
    t = Transcript(
        role="assistant",
        content="Hi there!",
        tokens_in=50,
        tokens_out=10,
    )
    assert t.tokens_in == 50
    assert t.tokens_out == 10


# ── RunResult ────────────────────────────────────────────


def test_run_result_stores_basics():
    """RunResult captures config, responses, and metrics."""
    result = RunResult(
        config_name="raw-claude",
        responses=["Hello world"],
        turns=1,
        total_tokens_in=100,
        total_tokens_out=50,
        wall_clock_s=1.5,
    )
    assert result.config_name == "raw-claude"
    assert result.turns == 1
    assert result.total_tokens_in == 100


def test_run_result_telemetry_events():
    """RunResult stores in-memory telemetry events."""
    result = RunResult(
        config_name="kit",
        responses=[],
        turns=0,
        total_tokens_in=0,
        total_tokens_out=0,
        wall_clock_s=0,
        telemetry_events=[
            {"event_type": "session.start"},
        ],
    )
    assert len(result.telemetry_events) == 1


def test_run_result_cost_estimate():
    """RunResult computes estimated cost."""
    result = RunResult(
        config_name="test",
        responses=[],
        turns=1,
        total_tokens_in=1_000_000,
        total_tokens_out=100_000,
        wall_clock_s=10.0,
        model="claude-sonnet-4-20250514",
    )
    assert result.estimated_cost_usd > 0


# ── BenchmarkResult ──────────────────────────────────────


def test_benchmark_result_groups_by_config():
    """BenchmarkResult groups run results by config name."""
    r1 = RunResult(
        config_name="raw",
        responses=[],
        turns=1,
        total_tokens_in=100,
        total_tokens_out=50,
        wall_clock_s=1.0,
    )
    r2 = RunResult(
        config_name="kit",
        responses=[],
        turns=2,
        total_tokens_in=200,
        total_tokens_out=100,
        wall_clock_s=2.0,
    )
    br = BenchmarkResult(
        scenario_name="test",
        results=[r1, r2],
    )
    assert br.scenario_name == "test"
    assert len(br.results) == 2


def test_benchmark_result_summary():
    """BenchmarkResult produces a per-config summary."""
    r1 = RunResult(
        config_name="raw",
        responses=["hi"],
        turns=1,
        total_tokens_in=100,
        total_tokens_out=50,
        wall_clock_s=1.0,
    )
    r2 = RunResult(
        config_name="raw",
        responses=["hello"],
        turns=2,
        total_tokens_in=200,
        total_tokens_out=100,
        wall_clock_s=2.0,
    )
    br = BenchmarkResult(
        scenario_name="test",
        results=[r1, r2],
    )
    summary = br.summary()
    assert "raw" in summary
    assert summary["raw"]["runs"] == 2
    assert summary["raw"]["avg_turns"] == 1.5

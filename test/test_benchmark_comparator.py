"""Tests for benchmark comparator and rewritten runner.

Replaces test_benchmark_conversation.py with tests adapted
to the new architecture: engine + scoring + comparator.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from test.benchmark.comparator import (
    PairwiseComparator,
    PairwiseReport,
)
from test.benchmark.runner import BenchmarkRunner, ScoredRun
from test.engine.config import (
    EvalScenario,
    RunConfig,
    RunResult,
)
from test.scoring.base import ScoringResult
from test.scoring.statistical import (
    StatisticalAnalyzer,
)

# ── Helpers ──────────────────────────────────────────────


def _mock_msg(text: str, tokens_in: int = 50, tokens_out: int = 25):
    """Create a mock Anthropic message response."""
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    msg.usage.input_tokens = tokens_in
    msg.usage.output_tokens = tokens_out
    return msg


def _scenario(prompt: str, max_turns: int = 10, plugins: list | None = None):
    """Build an EvalScenario with sensible defaults."""
    return EvalScenario(
        name="test-scenario",
        description="Test scenario",
        prompt=prompt,
        configs=[RunConfig(name="raw", plugins=plugins or [])],
        max_turns=max_turns,
    )


def _result(**kwargs) -> RunResult:
    defaults = {
        "config_name": "test",
        "responses": ["Hello"],
        "turns": 1,
        "total_tokens_in": 100,
        "total_tokens_out": 50,
        "wall_clock_s": 1.0,
        "model": "claude-sonnet-4-20250514",
    }
    defaults.update(kwargs)
    return RunResult(**defaults)


# ── ScoredRun ────────────────────────────────────────────


def test_scored_run_overall_score():
    r = _result()
    scores = [
        ScoringResult(scorer_name="a", dimension="x", score=8.0),
        ScoringResult(scorer_name="b", dimension="y", score=6.0),
    ]
    sr = ScoredRun(result=r, scores=scores)
    assert sr.overall_score == 7.0


def test_scored_run_empty_scores():
    sr = ScoredRun(result=_result(), scores=[])
    assert sr.overall_score == 0.0


# ── BenchmarkRunner ─────────────────────────────────────


def test_runner_accepts_scenario():
    scenario = _scenario("do something")
    runner = BenchmarkRunner(scenario)
    assert runner.scenario is scenario


def test_runner_has_default_scorers():
    runner = BenchmarkRunner(_scenario("test"))
    assert len(runner.scorers) == 5


def test_runner_custom_scorers():
    from test.scoring.deterministic import NoErrorScorer

    runner = BenchmarkRunner(
        _scenario("test"),
        scorers=[NoErrorScorer()],
    )
    assert len(runner.scorers) == 1


def test_run_single_returns_scored_run():
    scenario = _scenario("Say hello", max_turns=1)
    runner = BenchmarkRunner(scenario)

    mock_msg = _mock_msg("Hello!")

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = mock_msg
        scored = runner.run_single(RunConfig(name="raw", plugins=[]))

    assert isinstance(scored, ScoredRun)
    assert scored.result.config_name == "raw"
    assert scored.result.turns >= 1
    assert len(scored.scores) == 5  # default scorers


def test_run_single_raw_no_system_prompt():
    scenario = _scenario("Say hello", max_turns=1)
    runner = BenchmarkRunner(scenario)

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = _mock_msg("Hello!")
        runner.run_single(RunConfig(name="raw", plugins=[]))

        call_kwargs = client.messages.create.call_args
        assert "system" not in call_kwargs.kwargs


def test_run_all_executes_all_configs():
    scenario = EvalScenario(
        name="test",
        description="test",
        prompt="Hi",
        configs=[
            RunConfig(name="raw", plugins=[]),
            RunConfig(name="kit", plugins=[]),
        ],
        max_turns=1,
        runs=2,
    )
    runner = BenchmarkRunner(scenario)

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = _mock_msg("Hello!")
        benchmark = runner.run_all()

    assert len(benchmark.results) == 4  # 2 configs * 2 runs
    assert len(runner.scored_runs) == 4


def test_run_single_with_human_interaction():
    scenario = _scenario(
        "Implement auth for our service",
        max_turns=5,
    )
    runner = BenchmarkRunner(scenario)

    plan = _mock_msg("Shall I proceed with JWT auth?")
    approval = _mock_msg("Yes, proceed.")
    done = _mock_msg("Auth implemented.")

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.side_effect = [plan, approval, done]
        scored = runner.run_single(RunConfig(name="raw", plugins=[]))

    assert scored.result.turns >= 2


def test_telemetry_captured_in_scored_run(tmp_path):
    _create_test_plugin(tmp_path)

    scenario = _scenario(
        "Add health check",
        max_turns=3,
        plugins=["test-plugin"],
    )
    runner = BenchmarkRunner(scenario, plugins_dirs=[tmp_path])

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = _mock_msg("Done.")
        scored = runner.run_single(
            RunConfig(name="kit", plugins=["test-plugin"]),
        )

    assert len(scored.result.telemetry_events) > 0
    event_types = [e["event_type"] for e in scored.result.telemetry_events]
    assert "turn.completed" in event_types
    assert "session.end" in event_types


def test_cost_estimation_across_runs():
    scenario = EvalScenario(
        name="cost-test",
        description="Cost test",
        prompt="Do something",
        configs=[RunConfig(name="raw", plugins=[])],
        model="claude-sonnet-4-20250514",
        max_turns=1,
        runs=3,
    )
    runner = BenchmarkRunner(scenario)

    with patch("test.engine.executor.anthropic") as mock_api:
        client = mock_api.Anthropic.return_value
        client.messages.create.return_value = _mock_msg(
            "Done.",
            tokens_in=500,
            tokens_out=200,
        )
        benchmark = runner.run_all()

    for result in benchmark.results:
        assert result.estimated_cost_usd > 0
        assert result.model == "claude-sonnet-4-20250514"


# ── PairwiseComparator ───────────────────────────────────


def test_comparator_basic():
    comparator = PairwiseComparator(
        analyzer=StatisticalAnalyzer(seed=42),
    )
    raw_results = [
        (
            _result(config_name="raw"),
            [
                ScoringResult(
                    scorer_name="test",
                    dimension="quality",
                    score=5.0,
                ),
            ],
        )
        for _ in range(5)
    ]
    kit_results = [
        (
            _result(config_name="kit"),
            [
                ScoringResult(
                    scorer_name="test",
                    dimension="quality",
                    score=9.0,
                ),
            ],
        )
        for _ in range(5)
    ]

    report = comparator.compare(
        raw_results,
        kit_results,
        scenario_name="test",
    )

    assert isinstance(report, PairwiseReport)
    assert report.scenario_name == "test"
    assert len(report.dimensions) == 1
    assert report.dimensions[0].dimension == "quality"


def test_comparator_significant_difference():
    comparator = PairwiseComparator(
        analyzer=StatisticalAnalyzer(seed=42),
    )
    raw = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="q",
                    score=2.0,
                ),
            ],
        )
        for _ in range(5)
    ]
    kit = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="q",
                    score=9.0,
                ),
            ],
        )
        for _ in range(5)
    ]

    report = comparator.compare(raw, kit, scenario_name="test")
    assert report.kit_wins is True


def test_comparator_no_significant_difference():
    comparator = PairwiseComparator(
        analyzer=StatisticalAnalyzer(seed=42),
    )
    raw_scores = [5.0, 5.1, 4.9, 5.2, 4.8]
    kit_scores = [4.9, 5.2, 5.0, 4.8, 5.1]
    raw = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="q",
                    score=s,
                ),
            ],
        )
        for s in raw_scores
    ]
    kit = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="q",
                    score=s,
                ),
            ],
        )
        for s in kit_scores
    ]

    report = comparator.compare(raw, kit, scenario_name="test")
    assert report.kit_wins is False


def test_comparator_multiple_dimensions():
    comparator = PairwiseComparator(
        analyzer=StatisticalAnalyzer(seed=42),
    )
    raw = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="quality",
                    score=5.0,
                ),
                ScoringResult(
                    scorer_name="t",
                    dimension="efficiency",
                    score=6.0,
                ),
            ],
        )
        for _ in range(3)
    ]
    kit = [
        (
            _result(),
            [
                ScoringResult(
                    scorer_name="t",
                    dimension="quality",
                    score=8.0,
                ),
                ScoringResult(
                    scorer_name="t",
                    dimension="efficiency",
                    score=9.0,
                ),
            ],
        )
        for _ in range(3)
    ]

    report = comparator.compare(raw, kit, scenario_name="test")
    assert len(report.dimensions) == 2
    dim_names = [d.dimension for d in report.dimensions]
    assert "quality" in dim_names
    assert "efficiency" in dim_names


# ── Test Plugin Fixture ──────────────────────────────────


def _create_test_plugin(base_path):
    """Create a minimal plugin directory for testing."""
    plugin_dir = base_path / "test-plugin"
    meta = plugin_dir / ".claude-plugin"
    meta.mkdir(parents=True)
    (meta / "plugin.json").write_text(
        json.dumps(
            {
                "name": "test-plugin",
                "description": "Test plugin",
                "version": "0.0.1",
            },
        ),
    )
    (meta / "ctl.json").write_text(
        json.dumps(
            {"role": "knowledge", "domain": "universal"},
        ),
    )
    skill_dir = plugin_dir / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test\ndescription: test\n---\n\n"
        "# Test Skill\n\nYou are an excellent engineer.",
    )

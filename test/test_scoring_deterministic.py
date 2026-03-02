"""Tests for deterministic scorers — all offline, no API calls."""

from __future__ import annotations

from test.engine.config import RunResult
from test.scoring.base import ScoringResult
from test.scoring.deterministic import (
    ContainsScorer,
    NoErrorScorer,
    TelemetryCompletenessScorer,
    TelemetrySchemaScorer,
    TokenEfficiencyScorer,
)


def _result(**kwargs) -> RunResult:
    """Create a RunResult with sensible defaults."""
    defaults = {
        "config_name": "test",
        "responses": ["Hello world"],
        "turns": 1,
        "total_tokens_in": 100,
        "total_tokens_out": 50,
        "wall_clock_s": 1.0,
        "model": "claude-sonnet-4-20250514",
    }
    defaults.update(kwargs)
    return RunResult(**defaults)


# -- ContainsScorer --------------------------------------------------------


def test_contains_all_found():
    scorer = ContainsScorer()
    r = _result(responses=["The capital of France is Paris"])
    result = scorer.score(r, expected_strings=["Paris", "France"])
    assert result.score == 10.0
    assert result.details["ratio"] == 1.0


def test_contains_partial():
    scorer = ContainsScorer()
    r = _result(responses=["Hello world"])
    result = scorer.score(r, expected_strings=["Hello", "Goodbye"])
    assert result.score == 5.0


def test_contains_none_found():
    scorer = ContainsScorer()
    r = _result(responses=["Something else"])
    result = scorer.score(r, expected_strings=["Paris", "France"])
    assert result.score == 0.0


def test_contains_no_expected():
    scorer = ContainsScorer()
    r = _result()
    result = scorer.score(r)
    assert result.score == 10.0


def test_contains_case_insensitive():
    scorer = ContainsScorer()
    r = _result(responses=["PARIS is great"])
    result = scorer.score(r, expected_strings=["paris"])
    assert result.score == 10.0


def test_contains_across_responses():
    scorer = ContainsScorer()
    r = _result(responses=["First response about Paris", "Second about London"])
    result = scorer.score(r, expected_strings=["Paris", "London"])
    assert result.score == 10.0


def test_contains_scorer_metadata():
    scorer = ContainsScorer()
    assert scorer.name == "contains"
    assert scorer.dimension == "task_completion"


# -- NoErrorScorer ---------------------------------------------------------


def test_no_error_clean_run():
    scorer = NoErrorScorer()
    r = _result()
    result = scorer.score(r)
    assert result.score == 10.0


def test_no_error_with_error():
    scorer = NoErrorScorer()
    r = _result(error="API timeout")
    result = scorer.score(r)
    assert result.score == 0.0
    assert result.details["error"] == "API timeout"


def test_no_error_scorer_metadata():
    scorer = NoErrorScorer()
    assert scorer.name == "no_error"
    assert scorer.dimension == "correctness"


# -- TelemetrySchemaScorer -------------------------------------------------


def test_schema_valid_events():
    scorer = TelemetrySchemaScorer()
    r = _result(
        telemetry_events=[
            {"event_type": "session.start"},
            {"event_type": "turn.completed", "payload": {"turn": 1}},
            {"event_type": "session.end", "payload": {"total_turns": 1}},
        ]
    )
    result = scorer.score(r)
    assert result.score == 10.0


def test_schema_missing_event_type():
    scorer = TelemetrySchemaScorer()
    r = _result(telemetry_events=[{"payload": {"data": 1}}])
    result = scorer.score(r)
    assert result.score == 0.0


def test_schema_missing_payload():
    scorer = TelemetrySchemaScorer()
    r = _result(
        telemetry_events=[
            {"event_type": "session.start"},
            {"event_type": "turn.completed"},  # missing payload
        ]
    )
    result = scorer.score(r)
    assert result.score == 5.0


def test_schema_no_events():
    scorer = TelemetrySchemaScorer()
    r = _result(telemetry_events=[])
    result = scorer.score(r)
    assert result.score == 0.0


def test_schema_scorer_metadata():
    scorer = TelemetrySchemaScorer()
    assert scorer.name == "telemetry_schema"
    assert scorer.dimension == "telemetry"


# -- TelemetryCompletenessScorer -------------------------------------------


def test_completeness_all_present():
    scorer = TelemetryCompletenessScorer()
    r = _result(
        telemetry_events=[
            {"event_type": "session.start"},
            {"event_type": "turn.completed", "payload": {"turn": 1}},
            {"event_type": "session.result", "payload": {"usage": {}}},
            {"event_type": "session.end", "payload": {"total_turns": 1}},
        ]
    )
    result = scorer.score(r)
    assert result.score == 10.0


def test_completeness_partial():
    scorer = TelemetryCompletenessScorer()
    r = _result(
        telemetry_events=[
            {"event_type": "session.start"},
        ]
    )
    result = scorer.score(r)
    assert 0.0 < result.score < 10.0
    assert "turn.completed" in result.details["missing"]


def test_completeness_none():
    scorer = TelemetryCompletenessScorer()
    r = _result(telemetry_events=[])
    result = scorer.score(r)
    assert result.score == 0.0


def test_completeness_scorer_metadata():
    scorer = TelemetryCompletenessScorer()
    assert scorer.name == "telemetry_completeness"
    assert scorer.dimension == "telemetry"


# -- TokenEfficiencyScorer -------------------------------------------------


def test_efficiency_excellent():
    scorer = TokenEfficiencyScorer()
    r = _result(total_tokens_in=200, total_tokens_out=100, turns=1)
    result = scorer.score(r)
    assert result.score == 10.0


def test_efficiency_poor():
    scorer = TokenEfficiencyScorer()
    r = _result(total_tokens_in=3000, total_tokens_out=3000, turns=1)
    result = scorer.score(r)
    assert result.score < 2.0


def test_efficiency_zero_turns():
    scorer = TokenEfficiencyScorer()
    r = _result(turns=0)
    result = scorer.score(r)
    assert result.score == 0.0


def test_efficiency_linear_scale():
    scorer = TokenEfficiencyScorer()
    # Midpoint between 500 and 5000 = 2750 tokens/turn -> ~5.0
    r = _result(total_tokens_in=2000, total_tokens_out=750, turns=1)
    result = scorer.score(r)
    assert 4.0 <= result.score <= 6.0


def test_efficiency_scorer_metadata():
    scorer = TokenEfficiencyScorer()
    assert scorer.name == "token_efficiency"
    assert scorer.dimension == "efficiency"


# -- ScoringResult ---------------------------------------------------------


def test_scoring_result_fields():
    r = ScoringResult(scorer_name="test", dimension="quality", score=7.5)
    assert r.scorer_name == "test"
    assert r.dimension == "quality"
    assert r.score == 7.5
    assert r.confidence == 1.0
    assert r.details == {}


def test_scoring_result_with_details():
    r = ScoringResult(
        scorer_name="test",
        dimension="quality",
        score=8.0,
        confidence=0.9,
        details={"key": "value"},
        raw_output="some output",
    )
    assert r.confidence == 0.9
    assert r.details["key"] == "value"
    assert r.raw_output == "some output"

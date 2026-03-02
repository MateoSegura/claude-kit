"""Tests for multi-turn conversation scorers."""

from __future__ import annotations

from test.engine.config import RunResult, Transcript
from test.scoring.multi_turn import (
    CompactionResilienceScorer,
    ConversationCoherenceScorer,
    HumanSimulatorQualityScorer,
)


def _make_result(**kwargs) -> RunResult:
    """Create a minimal RunResult with defaults."""
    defaults = {
        "config_name": "test",
        "responses": ["hello"],
        "turns": 1,
        "total_tokens_in": 100,
        "total_tokens_out": 50,
        "wall_clock_s": 1.0,
    }
    defaults.update(kwargs)
    return RunResult(**defaults)


class TestHumanSimulatorQualityScorer:
    """Tests for HumanSimulatorQualityScorer."""

    def test_no_human_interaction(self) -> None:
        scorer = HumanSimulatorQualityScorer()
        result = _make_result(
            transcript=[
                Transcript(role="user", content="Hello"),
                Transcript(role="assistant", content="Hi there"),
            ],
        )
        sr = scorer.score(result)
        assert sr.score == 10.0
        assert sr.dimension == "interaction_quality"
        assert "no human interaction" in sr.details["reason"]

    def test_with_human_interaction_no_anthropic(self) -> None:
        scorer = HumanSimulatorQualityScorer()
        result = _make_result(
            transcript=[
                Transcript(role="user", content="Hello"),
                Transcript(role="assistant", content="Question?"),
                Transcript(role="human_sim", content="Yes"),
            ],
        )
        # Without anthropic, falls back to score 5.0
        sr = scorer.score(result)
        assert sr.scorer_name == "human_sim_quality"
        # Score depends on whether anthropic is available
        assert 0.0 <= sr.score <= 10.0

    def test_scorer_properties(self) -> None:
        scorer = HumanSimulatorQualityScorer()
        assert scorer.name == "human_sim_quality"
        assert scorer.dimension == "interaction_quality"


class TestConversationCoherenceScorer:
    """Tests for ConversationCoherenceScorer."""

    def test_single_turn(self) -> None:
        scorer = ConversationCoherenceScorer()
        result = _make_result(turns=1)
        sr = scorer.score(result)
        assert sr.score == 10.0
        assert "single-turn" in sr.details["reason"]

    def test_multi_turn_no_anthropic(self) -> None:
        scorer = ConversationCoherenceScorer()
        result = _make_result(
            turns=3,
            transcript=[
                Transcript(role="user", content="Build a service"),
                Transcript(role="assistant", content="I'll help."),
                Transcript(role="human_sim", content="Go ahead."),
                Transcript(role="assistant", content="Done."),
            ],
        )
        sr = scorer.score(result)
        assert sr.scorer_name == "conversation_coherence"
        assert 0.0 <= sr.score <= 10.0

    def test_scorer_properties(self) -> None:
        scorer = ConversationCoherenceScorer()
        assert scorer.name == "conversation_coherence"
        assert scorer.dimension == "coherence"


class TestCompactionResilienceScorer:
    """Tests for CompactionResilienceScorer."""

    def test_no_compaction(self) -> None:
        scorer = CompactionResilienceScorer()
        result = _make_result(compact_count=0)
        sr = scorer.score(result)
        assert sr.score == 10.0
        assert "no compaction" in sr.details["reason"]

    def test_with_compaction_retains_context(self) -> None:
        scorer = CompactionResilienceScorer()
        result = _make_result(
            compact_count=1,
            transcript=[
                Transcript(
                    role="user",
                    content="Implement authentication service with JWT tokens",
                ),
                Transcript(
                    role="assistant",
                    content="I'll implement authentication.",
                ),
                Transcript(
                    role="system",
                    content="compacted",
                    subtype="auto_compact",
                ),
                Transcript(
                    role="assistant",
                    content=(
                        "Continuing with the authentication service and JWT tokens."
                    ),
                ),
            ],
        )
        sr = scorer.score(result)
        assert sr.score > 0.0
        assert sr.dimension == "context_preservation"
        assert "retention_ratio" in sr.details

    def test_with_compaction_loses_context(self) -> None:
        scorer = CompactionResilienceScorer()
        result = _make_result(
            compact_count=1,
            transcript=[
                Transcript(
                    role="user",
                    content="Implement authentication service with JWT tokens",
                ),
                Transcript(
                    role="assistant",
                    content="Working on it.",
                ),
                Transcript(
                    role="system",
                    content="compacted",
                    subtype="auto_compact",
                ),
                Transcript(
                    role="assistant",
                    content="Here is a hello world program.",
                ),
            ],
        )
        sr = scorer.score(result)
        # Should score lower since post-compact text doesn't retain keywords
        assert sr.score < 10.0

    def test_scorer_properties(self) -> None:
        scorer = CompactionResilienceScorer()
        assert scorer.name == "compaction_resilience"
        assert scorer.dimension == "context_preservation"

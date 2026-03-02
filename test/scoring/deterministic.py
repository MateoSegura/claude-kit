"""Deterministic scorers — no LLM calls required."""

from __future__ import annotations

from typing import Any

from test.engine.config import RunResult
from test.scoring.base import Scorer, ScoringResult


class ContainsScorer(Scorer):
    """Check if response contains expected strings."""

    @property
    def name(self) -> str:
        return "contains"

    @property
    def dimension(self) -> str:
        return "task_completion"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        expected: list[str] = kwargs.get("expected_strings", [])
        if not expected:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=10.0,
                details={"reason": "no expected strings specified"},
            )

        combined = " ".join(result.responses).lower()
        found = [s for s in expected if s.lower() in combined]
        missing = [s for s in expected if s.lower() not in combined]
        ratio = len(found) / len(expected) if expected else 1.0

        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=round(ratio * 10.0, 1),
            details={"found": found, "missing": missing, "ratio": ratio},
        )


class NoErrorScorer(Scorer):
    """Check that no errors occurred during the run."""

    @property
    def name(self) -> str:
        return "no_error"

    @property
    def dimension(self) -> str:
        return "correctness"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        has_error = result.error is not None
        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=0.0 if has_error else 10.0,
            details={"error": result.error} if has_error else {},
        )


class TelemetrySchemaScorer(Scorer):
    """Validate telemetry events have correct schema structure."""

    REQUIRED_FIELDS = {"event_type"}
    PAYLOAD_EVENTS = {
        "turn.completed",
        "human.responded",
        "session.end",
        "tool.used",
        "tool.result",
        "message.assistant",
        "message.system",
        "session.result",
        "session.compact",
    }

    @property
    def name(self) -> str:
        return "telemetry_schema"

    @property
    def dimension(self) -> str:
        return "telemetry"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        events = result.telemetry_events
        if not events:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=0.0,
                details={"reason": "no telemetry events"},
            )

        valid = 0
        issues: list[str] = []
        for i, event in enumerate(events):
            # Check required fields
            missing = self.REQUIRED_FIELDS - set(event.keys())
            if missing:
                issues.append(f"event[{i}]: missing fields {missing}")
                continue

            # Check payload events have payload
            event_type = event.get("event_type", "")
            if event_type in self.PAYLOAD_EVENTS and "payload" not in event:
                issues.append(f"event[{i}]: {event_type} missing payload")
                continue

            valid += 1

        ratio = valid / len(events) if events else 0.0
        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=round(ratio * 10.0, 1),
            details={"valid": valid, "total": len(events), "issues": issues},
        )


class TelemetryCompletenessScorer(Scorer):
    """Validate that essential telemetry events are present."""

    ESSENTIAL_EVENTS = {
        "session.start",
        "session.end",
        "turn.completed",
        "session.result",
    }

    @property
    def name(self) -> str:
        return "telemetry_completeness"

    @property
    def dimension(self) -> str:
        return "telemetry"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        events = result.telemetry_events
        if not events:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=0.0,
                details={"reason": "no telemetry events"},
            )

        event_types = {e.get("event_type") for e in events}
        found = self.ESSENTIAL_EVENTS & event_types
        missing = self.ESSENTIAL_EVENTS - event_types
        ratio = len(found) / len(self.ESSENTIAL_EVENTS)

        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=round(ratio * 10.0, 1),
            details={"found": sorted(found), "missing": sorted(missing)},
        )


class TokenEfficiencyScorer(Scorer):
    """Score based on tokens-per-turn ratio (lower is better)."""

    # Thresholds: tokens_per_turn -> score mapping
    # Under 500 tokens/turn = excellent (10), over 5000 = poor (0)
    EXCELLENT_THRESHOLD = 500
    POOR_THRESHOLD = 5000

    @property
    def name(self) -> str:
        return "token_efficiency"

    @property
    def dimension(self) -> str:
        return "efficiency"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        if result.turns == 0:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=0.0,
                details={"reason": "no turns recorded"},
            )

        total_tokens = result.total_tokens_in + result.total_tokens_out
        tokens_per_turn = total_tokens / result.turns

        # Linear interpolation between thresholds
        if tokens_per_turn <= self.EXCELLENT_THRESHOLD:
            raw_score = 10.0
        elif tokens_per_turn >= self.POOR_THRESHOLD:
            raw_score = 0.0
        else:
            # Linear scale from 10 to 0
            range_size = self.POOR_THRESHOLD - self.EXCELLENT_THRESHOLD
            position = tokens_per_turn - self.EXCELLENT_THRESHOLD
            raw_score = 10.0 * (1.0 - position / range_size)

        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=round(raw_score, 1),
            details={
                "tokens_per_turn": round(tokens_per_turn, 1),
                "total_tokens": total_tokens,
                "turns": result.turns,
            },
        )

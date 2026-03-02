"""BenchmarkRunner — orchestrates benchmark runs with scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from test.engine.config import (
    BenchmarkResult,
    EvalScenario,
    RunConfig,
    RunResult,
)
from test.engine.executor import ConversationExecutor
from test.engine.human import HumanSimulator
from test.scoring.base import Scorer, ScoringResult
from test.scoring.deterministic import (
    ContainsScorer,
    NoErrorScorer,
    TelemetryCompletenessScorer,
    TelemetrySchemaScorer,
    TokenEfficiencyScorer,
)


@dataclass
class ScoredRun:
    """A RunResult paired with its scoring results."""

    result: RunResult
    scores: list[ScoringResult] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Average of all dimension scores."""
        if not self.scores:
            return 0.0
        return sum(s.score for s in self.scores) / len(self.scores)


class BenchmarkRunner:
    """Orchestrates benchmark runs with scoring pipeline.

    Drives conversations via ConversationExecutor, applies scorers,
    and aggregates results for comparison.
    """

    def __init__(
        self,
        scenario: EvalScenario,
        plugins_dirs: list[Path | str] | None = None,
        scorers: list[Scorer] | None = None,
    ) -> None:
        self.scenario = scenario
        self._plugins_dirs = [
            Path(d) if isinstance(d, str) else d for d in (plugins_dirs or [])
        ]
        self.scorers = scorers or self._default_scorers()
        self.human = HumanSimulator()

    def _default_scorers(self) -> list[Scorer]:
        return [
            ContainsScorer(),
            NoErrorScorer(),
            TelemetrySchemaScorer(),
            TelemetryCompletenessScorer(),
            TokenEfficiencyScorer(),
        ]

    def run_single(
        self,
        config: RunConfig,
        score_kwargs: dict[str, Any] | None = None,
    ) -> ScoredRun:
        """Execute a single run and score it.

        Args:
            config: The RunConfig to execute.
            score_kwargs: Extra kwargs passed to each scorer.

        Returns:
            ScoredRun with result and scores.
        """
        executor = ConversationExecutor(
            scenario=self.scenario,
            plugins_dirs=self._plugins_dirs or None,
            human=self.human,
        )

        result = executor.execute(config)

        # Apply scorers
        kwargs = score_kwargs or {}
        scores: list[ScoringResult] = []
        for scorer in self.scorers:
            scores.append(scorer.score(result, **kwargs))

        return ScoredRun(result=result, scores=scores)

    def run_all(
        self,
        score_kwargs: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        """Run all configs the specified number of times.

        Args:
            score_kwargs: Extra kwargs passed to each scorer.

        Returns:
            BenchmarkResult with all RunResults.
        """
        results: list[RunResult] = []
        self._scored_runs: list[ScoredRun] = []

        for config in self.scenario.configs:
            for _ in range(self.scenario.runs):
                self.human.response_count = 0
                scored = self.run_single(config, score_kwargs)
                results.append(scored.result)
                self._scored_runs.append(scored)

        return BenchmarkResult(
            scenario_name=self.scenario.name,
            results=results,
        )

    @property
    def scored_runs(self) -> list[ScoredRun]:
        """Access scored runs after run_all()."""
        return getattr(self, "_scored_runs", [])

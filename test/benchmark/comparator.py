"""PairwiseComparator — compare kit vs raw benchmark results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from test.engine.config import RunResult
from test.scoring.base import ScoringResult
from test.scoring.statistical import (
    ComparisonResult,
    StatisticalAnalyzer,
)


@dataclass
class DimensionComparison:
    """Comparison results for a single scoring dimension."""

    dimension: str
    comparison: ComparisonResult
    raw_scores: list[float]
    kit_scores: list[float]


@dataclass
class PairwiseReport:
    """Complete pairwise comparison report."""

    scenario_name: str
    raw_config: str
    kit_config: str
    dimensions: list[DimensionComparison]
    overall: ComparisonResult
    pairwise_judge: dict[str, Any] = field(
        default_factory=dict,
    )
    multi_turn_metrics: dict[str, Any] = field(
        default_factory=dict,
    )
    conversation_samples: list[dict[str, Any]] = field(
        default_factory=list,
    )

    @property
    def kit_wins(self) -> bool:
        """True if kit significantly outperforms raw."""
        return self.overall.significant and self.overall.diff_mean > 0


class PairwiseComparator:
    """Compare kit and raw benchmark results statistically.

    Takes scored runs from two configs, extracts dimension scores,
    and runs statistical analysis to determine significance.
    """

    def __init__(
        self,
        analyzer: StatisticalAnalyzer | None = None,
    ) -> None:
        self.analyzer = analyzer or StatisticalAnalyzer()

    def compare(
        self,
        raw_results: list[tuple[RunResult, list[ScoringResult]]],
        kit_results: list[tuple[RunResult, list[ScoringResult]]],
        scenario_name: str = "",
        raw_config: str = "raw",
        kit_config: str = "kit",
    ) -> PairwiseReport:
        """Compare raw and kit scored results.

        Args:
            raw_results: List of (RunResult, scores) for raw config.
            kit_results: List of (RunResult, scores) for kit config.
            scenario_name: Name of the scenario being compared.
            raw_config: Label for the raw config.
            kit_config: Label for the kit config.

        Returns:
            PairwiseReport with per-dimension and overall comparisons.
        """
        # Collect scores by dimension
        raw_by_dim = self._group_by_dimension(raw_results)
        kit_by_dim = self._group_by_dimension(kit_results)

        # All dimensions present in either group
        all_dims = sorted(
            set(raw_by_dim.keys()) | set(kit_by_dim.keys()),
        )

        dimensions: list[DimensionComparison] = []
        all_raw_scores: list[float] = []
        all_kit_scores: list[float] = []

        for dim in all_dims:
            raw_scores = raw_by_dim.get(dim, [])
            kit_scores = kit_by_dim.get(dim, [])

            comparison = self.analyzer.compare(
                raw_scores,
                kit_scores,
            )
            dimensions.append(
                DimensionComparison(
                    dimension=dim,
                    comparison=comparison,
                    raw_scores=raw_scores,
                    kit_scores=kit_scores,
                ),
            )

            all_raw_scores.extend(raw_scores)
            all_kit_scores.extend(kit_scores)

        # Overall comparison (average across dimensions)
        raw_avgs = self._per_run_averages(raw_results)
        kit_avgs = self._per_run_averages(kit_results)
        overall = self.analyzer.compare(raw_avgs, kit_avgs)

        # Multi-turn metrics
        multi_turn = self._compute_multi_turn_metrics(
            raw_results, kit_results, raw_config, kit_config
        )
        samples = self._collect_conversation_samples(
            raw_results, kit_results, raw_config, kit_config
        )

        return PairwiseReport(
            scenario_name=scenario_name,
            raw_config=raw_config,
            kit_config=kit_config,
            dimensions=dimensions,
            overall=overall,
            multi_turn_metrics=multi_turn,
            conversation_samples=samples,
        )

    def _group_by_dimension(
        self,
        results: list[tuple[RunResult, list[ScoringResult]]],
    ) -> dict[str, list[float]]:
        """Group scores by dimension name."""
        groups: dict[str, list[float]] = {}
        for _, scores in results:
            for s in scores:
                groups.setdefault(s.dimension, []).append(s.score)
        return groups

    def _per_run_averages(
        self,
        results: list[tuple[RunResult, list[ScoringResult]]],
    ) -> list[float]:
        """Compute average score per run."""
        avgs: list[float] = []
        for _, scores in results:
            if scores:
                avg = sum(s.score for s in scores) / len(scores)
                avgs.append(avg)
        return avgs

    def _compute_multi_turn_metrics(
        self,
        raw_results: list[tuple[RunResult, list[ScoringResult]]],
        kit_results: list[tuple[RunResult, list[ScoringResult]]],
        raw_config: str,
        kit_config: str,
    ) -> dict[str, Any]:
        """Compute multi-turn conversation metrics for both configs."""

        def _avg(vals: list[float]) -> float:
            return sum(vals) / len(vals) if vals else 0.0

        def _metrics(
            results: list[tuple[RunResult, list[ScoringResult]]],
        ) -> dict[str, float]:
            turns = [float(r.turns) for r, _ in results]
            human = [float(r.human_response_count) for r, _ in results]
            tools = [float(r.tool_use_count) for r, _ in results]
            compacts = [float(r.compact_count) for r, _ in results]
            return {
                "avg_turns": round(_avg(turns), 1),
                "avg_human_responses": round(_avg(human), 1),
                "avg_tool_calls": round(_avg(tools), 1),
                "avg_compaction_events": round(_avg(compacts), 1),
            }

        return {
            raw_config: _metrics(raw_results),
            kit_config: _metrics(kit_results),
        }

    def _collect_conversation_samples(
        self,
        raw_results: list[tuple[RunResult, list[ScoringResult]]],
        kit_results: list[tuple[RunResult, list[ScoringResult]]],
        raw_config: str,
        kit_config: str,
    ) -> list[dict[str, Any]]:
        """Collect human simulator interaction samples from both configs."""
        samples: list[dict[str, Any]] = []

        for config_name, results in [
            (raw_config, raw_results),
            (kit_config, kit_results),
        ]:
            for result, _ in results[:2]:  # Cap at 2 runs per config
                for i, entry in enumerate(result.transcript):
                    if entry.role != "human_sim":
                        continue
                    # Find preceding assistant message
                    question = ""
                    for j in range(i - 1, -1, -1):
                        prev = result.transcript[j]
                        if prev.role == "assistant":
                            question = prev.content[:200]
                            break
                    samples.append(
                        {
                            "config": config_name,
                            "turn": i,
                            "question": question,
                            "response": entry.content[:200],
                        },
                    )

        return samples

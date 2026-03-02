"""Rubric definitions for LLM-as-Judge scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # CI: PyYAML not installed
    yaml = None  # type: ignore[assignment]


@dataclass
class Dimension:
    """A single quality dimension with weight and description."""

    name: str
    weight: float
    description: str
    scoring_guide: str = ""


@dataclass
class Rubric:
    """A complete scoring rubric with weighted dimensions."""

    name: str
    description: str
    dimensions: list[Dimension]

    @property
    def total_weight(self) -> float:
        return sum(d.weight for d in self.dimensions)

    def weighted_score(self, scores: dict[str, float]) -> float:
        """Compute weighted average score from dimension scores.

        Args:
            scores: Mapping of dimension name to score (0-10).

        Returns:
            Weighted average score (0-10).
        """
        total = 0.0
        weight_sum = 0.0
        for dim in self.dimensions:
            if dim.name in scores:
                total += scores[dim.name] * dim.weight
                weight_sum += dim.weight
        return total / weight_sum if weight_sum > 0 else 0.0


def load_rubric(path: Path) -> Rubric:
    """Load a rubric from a YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    dimensions = []
    for d in raw.get("dimensions", []):
        dimensions.append(
            Dimension(
                name=d["name"],
                weight=d["weight"],
                description=d["description"],
                scoring_guide=d.get("scoring_guide", ""),
            )
        )

    return Rubric(
        name=raw["name"],
        description=raw.get("description", ""),
        dimensions=dimensions,
    )


# Default rubric — always available without a YAML file
_TASK_GUIDE = (
    "10: Fully complete. 7: Mostly complete with minor gaps."
    " 4: Partially done. 0: Did not attempt."
)
_CORRECT_GUIDE = (
    "10: Flawless. 7: Minor issues. 4: Significant errors. 0: Completely wrong."
)
_INSTRUCT_GUIDE = (
    "10: Followed all constraints. 7: Missed minor details."
    " 4: Missed key constraints. 0: Ignored instructions."
)
_QUALITY_GUIDE = (
    "10: Clean, idiomatic, well-structured."
    " 7: Good but minor style issues."
    " 4: Hard to read or maintain. 0: Unmaintainable."
)
_DOMAIN_GUIDE = (
    "10: Expert domain knowledge evident. 7: Good awareness."
    " 4: Basic awareness. 0: No domain knowledge."
)
_EFFICIENCY_GUIDE = (
    "10: Minimal, efficient approach. 7: Mostly efficient."
    " 4: Some unnecessary work. 0: Extremely wasteful."
)

DEFAULT_DIMENSIONS: list[Dimension] = [
    Dimension(
        name="task_completion",
        weight=1.5,
        description="Did it finish the requested task?",
        scoring_guide=_TASK_GUIDE,
    ),
    Dimension(
        name="correctness",
        weight=2.0,
        description="Is the code/answer technically correct?",
        scoring_guide=_CORRECT_GUIDE,
    ),
    Dimension(
        name="instruction_adherence",
        weight=1.5,
        description="Did it follow constraints and instructions?",
        scoring_guide=_INSTRUCT_GUIDE,
    ),
    Dimension(
        name="code_quality",
        weight=1.0,
        description="Is the code idiomatic and maintainable?",
        scoring_guide=_QUALITY_GUIDE,
    ),
    Dimension(
        name="domain_awareness",
        weight=1.0,
        description="Does it show domain knowledge?",
        scoring_guide=_DOMAIN_GUIDE,
    ),
    Dimension(
        name="efficiency",
        weight=0.5,
        description="Did it avoid unnecessary steps?",
        scoring_guide=_EFFICIENCY_GUIDE,
    ),
]

DEFAULT_RUBRIC = Rubric(
    name="default",
    description="Standard quality rubric for benchmark evaluations",
    dimensions=DEFAULT_DIMENSIONS,
)

"""Base types for the scoring pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from test.engine.config import RunResult


@dataclass
class ScoringResult:
    """Result from a single scorer evaluation."""

    scorer_name: str
    dimension: str
    score: float  # 0.0 to 10.0
    confidence: float = 1.0  # 0.0 to 1.0
    details: dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""


class Scorer(ABC):
    """Abstract base class for all scorers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this scorer."""

    @property
    @abstractmethod
    def dimension(self) -> str:
        """Which quality dimension this scorer measures."""

    @abstractmethod
    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        """Score a single RunResult."""

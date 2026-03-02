"""Statistical analysis for benchmark comparisons — stdlib only."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class BootstrapResult:
    """Result of a bootstrap confidence interval estimation."""

    mean: float
    ci_lower: float
    ci_upper: float
    n_samples: int
    std_dev: float = 0.0


@dataclass
class ComparisonResult:
    """Result of comparing two groups of scores."""

    group_a: BootstrapResult
    group_b: BootstrapResult
    diff_mean: float
    diff_ci_lower: float
    diff_ci_upper: float
    significant: bool  # True if CI excludes zero
    cohens_d: float
    cv_a: float  # coefficient of variation for group A
    cv_b: float  # coefficient of variation for group B


class StatisticalAnalyzer:
    """Bootstrap-based statistical analysis for benchmark comparisons.

    Uses resampling (random.choices) instead of parametric assumptions.
    All computations use stdlib only — no numpy or scipy.
    """

    def __init__(
        self,
        n_bootstrap: int = 10_000,
        ci_level: float = 0.95,
        seed: int | None = None,
    ) -> None:
        self.n_bootstrap = n_bootstrap
        self.ci_level = ci_level
        self._rng = random.Random(seed)

    def bootstrap_ci(self, values: list[float]) -> BootstrapResult:
        """Compute bootstrap confidence interval for the mean."""
        if not values:
            return BootstrapResult(mean=0.0, ci_lower=0.0, ci_upper=0.0, n_samples=0)

        n = len(values)
        observed_mean = sum(values) / n

        if n == 1:
            return BootstrapResult(
                mean=observed_mean,
                ci_lower=observed_mean,
                ci_upper=observed_mean,
                n_samples=1,
                std_dev=0.0,
            )

        # Bootstrap resampling
        boot_means: list[float] = []
        for _ in range(self.n_bootstrap):
            sample = self._rng.choices(values, k=n)
            boot_means.append(sum(sample) / n)

        boot_means.sort()

        alpha = 1.0 - self.ci_level
        lower_idx = int(alpha / 2 * self.n_bootstrap)
        upper_idx = int((1.0 - alpha / 2) * self.n_bootstrap) - 1
        lower_idx = max(0, min(lower_idx, len(boot_means) - 1))
        upper_idx = max(0, min(upper_idx, len(boot_means) - 1))

        variance = sum((x - observed_mean) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance)

        return BootstrapResult(
            mean=observed_mean,
            ci_lower=boot_means[lower_idx],
            ci_upper=boot_means[upper_idx],
            n_samples=n,
            std_dev=std_dev,
        )

    def coefficient_of_variation(self, values: list[float]) -> float:
        """Compute coefficient of variation (std_dev / mean).

        Returns 0.0 if the mean is zero or values are empty.
        """
        if not values:
            return 0.0
        n = len(values)
        mean = sum(values) / n
        if mean == 0.0:
            return 0.0
        if n < 2:
            return 0.0
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        return math.sqrt(variance) / abs(mean)

    def cohens_d(self, group_a: list[float], group_b: list[float]) -> float:
        """Compute Cohen's d effect size between two groups.

        Uses pooled standard deviation. Returns 0.0 if either group
        has fewer than 2 values.
        """
        n_a, n_b = len(group_a), len(group_b)
        if n_a < 2 or n_b < 2:
            return 0.0

        mean_a = sum(group_a) / n_a
        mean_b = sum(group_b) / n_b

        var_a = sum((x - mean_a) ** 2 for x in group_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in group_b) / (n_b - 1)

        # Pooled standard deviation
        pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
        pooled_std = math.sqrt(pooled_var)

        if pooled_std == 0.0:
            return 0.0

        return (mean_b - mean_a) / pooled_std

    def compare(
        self,
        group_a: list[float],
        group_b: list[float],
    ) -> ComparisonResult:
        """Compare two groups and determine if the difference is significant.

        Uses bootstrap CI on the paired differences. The difference is
        significant if the CI does not contain zero.
        """
        ci_a = self.bootstrap_ci(group_a)
        ci_b = self.bootstrap_ci(group_b)

        # Bootstrap the differences
        n = min(len(group_a), len(group_b))
        if n == 0:
            return ComparisonResult(
                group_a=ci_a,
                group_b=ci_b,
                diff_mean=0.0,
                diff_ci_lower=0.0,
                diff_ci_upper=0.0,
                significant=False,
                cohens_d=0.0,
                cv_a=0.0,
                cv_b=0.0,
            )

        # For paired comparison, compute differences
        diffs = [group_b[i] - group_a[i] for i in range(n)]
        diff_ci = self.bootstrap_ci(diffs)

        # Significant if CI excludes zero
        significant = diff_ci.ci_lower > 0 or diff_ci.ci_upper < 0

        return ComparisonResult(
            group_a=ci_a,
            group_b=ci_b,
            diff_mean=diff_ci.mean,
            diff_ci_lower=diff_ci.ci_lower,
            diff_ci_upper=diff_ci.ci_upper,
            significant=significant,
            cohens_d=self.cohens_d(group_a, group_b),
            cv_a=self.coefficient_of_variation(group_a),
            cv_b=self.coefficient_of_variation(group_b),
        )

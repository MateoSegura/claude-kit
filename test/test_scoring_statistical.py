"""Tests for statistical analysis — known-distribution tests."""

from __future__ import annotations

from test.scoring.statistical import (
    BootstrapResult,
    ComparisonResult,
    StatisticalAnalyzer,
)


def _analyzer(seed: int = 42) -> StatisticalAnalyzer:
    return StatisticalAnalyzer(n_bootstrap=5000, seed=seed)


# -- BootstrapResult ----------------------------------------------------------


def test_bootstrap_result_fields():
    r = BootstrapResult(mean=5.0, ci_lower=4.0, ci_upper=6.0, n_samples=10)
    assert r.mean == 5.0
    assert r.ci_lower == 4.0
    assert r.ci_upper == 6.0


# -- bootstrap_ci --------------------------------------------------------------


def test_bootstrap_ci_single_value():
    analyzer = _analyzer()
    result = analyzer.bootstrap_ci([5.0])
    assert result.mean == 5.0
    assert result.ci_lower == 5.0
    assert result.ci_upper == 5.0
    assert result.n_samples == 1


def test_bootstrap_ci_empty():
    analyzer = _analyzer()
    result = analyzer.bootstrap_ci([])
    assert result.mean == 0.0
    assert result.n_samples == 0


def test_bootstrap_ci_identical_values():
    analyzer = _analyzer()
    result = analyzer.bootstrap_ci([7.0, 7.0, 7.0, 7.0, 7.0])
    assert result.mean == 7.0
    assert result.ci_lower == 7.0
    assert result.ci_upper == 7.0


def test_bootstrap_ci_known_distribution():
    """Bootstrap CI should contain the true mean for a known distribution."""
    analyzer = _analyzer()
    # Values centered around 5.0
    values = [4.5, 4.8, 5.0, 5.2, 5.5]
    result = analyzer.bootstrap_ci(values)
    assert result.ci_lower <= 5.0 <= result.ci_upper
    assert result.mean == 5.0


def test_bootstrap_ci_wider_for_spread_data():
    """More spread data should produce wider confidence intervals."""
    analyzer = _analyzer()
    tight = analyzer.bootstrap_ci([5.0, 5.0, 5.0, 5.0, 5.0])
    spread = analyzer.bootstrap_ci([1.0, 3.0, 5.0, 7.0, 9.0])
    tight_width = tight.ci_upper - tight.ci_lower
    spread_width = spread.ci_upper - spread.ci_lower
    assert spread_width > tight_width


def test_bootstrap_ci_std_dev():
    analyzer = _analyzer()
    result = analyzer.bootstrap_ci([2.0, 4.0, 6.0, 8.0, 10.0])
    assert result.std_dev > 0


# -- coefficient_of_variation --------------------------------------------------


def test_cv_identical_values():
    analyzer = _analyzer()
    assert analyzer.coefficient_of_variation([5.0, 5.0, 5.0]) == 0.0


def test_cv_spread_values():
    analyzer = _analyzer()
    cv = analyzer.coefficient_of_variation([1.0, 2.0, 3.0, 4.0, 5.0])
    assert cv > 0


def test_cv_empty():
    analyzer = _analyzer()
    assert analyzer.coefficient_of_variation([]) == 0.0


def test_cv_single():
    analyzer = _analyzer()
    assert analyzer.coefficient_of_variation([5.0]) == 0.0


# -- cohens_d ------------------------------------------------------------------


def test_cohens_d_identical_groups():
    analyzer = _analyzer()
    d = analyzer.cohens_d([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
    assert d == 0.0


def test_cohens_d_large_effect():
    """Well-separated groups should have large Cohen's d."""
    analyzer = _analyzer()
    a = [1.0, 1.1, 1.2, 0.9, 1.0]
    b = [5.0, 5.1, 5.2, 4.9, 5.0]
    d = analyzer.cohens_d(a, b)
    assert d > 2.0  # Very large effect


def test_cohens_d_small_groups():
    analyzer = _analyzer()
    d = analyzer.cohens_d([1.0], [5.0])
    assert d == 0.0  # Not enough data


def test_cohens_d_direction():
    """Positive d means group_b > group_a."""
    analyzer = _analyzer()
    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0]
    d = analyzer.cohens_d(a, b)
    assert d > 0


# -- compare -------------------------------------------------------------------


def test_compare_significant_difference():
    """Well-separated groups should produce significant result."""
    analyzer = _analyzer()
    a = [1.0, 1.5, 2.0, 1.2, 1.8]
    b = [8.0, 8.5, 9.0, 8.2, 8.8]
    result = analyzer.compare(a, b)
    assert result.significant is True
    assert result.diff_mean > 0
    assert result.diff_ci_lower > 0


def test_compare_no_significant_difference():
    """Overlapping groups should not be significant."""
    analyzer = _analyzer()
    a = [5.0, 5.5, 4.5, 5.2, 4.8]
    b = [5.1, 5.4, 4.6, 5.3, 4.7]
    result = analyzer.compare(a, b)
    assert result.significant is False


def test_compare_empty_groups():
    analyzer = _analyzer()
    result = analyzer.compare([], [])
    assert result.significant is False
    assert result.diff_mean == 0.0


def test_compare_returns_cv():
    analyzer = _analyzer()
    a = [1.0, 2.0, 3.0]
    b = [10.0, 10.0, 10.0]
    result = analyzer.compare(a, b)
    assert result.cv_a > 0
    assert result.cv_b == 0.0


def test_compare_returns_cohens_d():
    analyzer = _analyzer()
    a = [1.0, 2.0, 3.0]
    b = [7.0, 8.0, 9.0]
    result = analyzer.compare(a, b)
    assert result.cohens_d > 0


def test_comparison_result_fields():
    r = ComparisonResult(
        group_a=BootstrapResult(mean=2.0, ci_lower=1.5, ci_upper=2.5, n_samples=5),
        group_b=BootstrapResult(mean=8.0, ci_lower=7.5, ci_upper=8.5, n_samples=5),
        diff_mean=6.0,
        diff_ci_lower=5.0,
        diff_ci_upper=7.0,
        significant=True,
        cohens_d=3.0,
        cv_a=0.2,
        cv_b=0.1,
    )
    assert r.diff_mean == 6.0
    assert r.significant is True

"""Report generation — JSON and markdown output for benchmark results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from test.benchmark.comparator import PairwiseReport


def generate_markdown(report: PairwiseReport) -> str:
    """Generate a markdown comparison table from a PairwiseReport.

    Produces a table matching the plan's expected output format:
    | Metric | raw | kit | Diff |
    """
    lines: list[str] = []
    lines.append(
        f"# Benchmark: {report.scenario_name}",
    )
    lines.append("")

    # Header
    lines.append(
        f"| Metric | {report.raw_config} | {report.kit_config} | Diff |",
    )
    lines.append("|---|---|---|---|")

    # Overall
    o = report.overall
    sig = " *" if o.significant else ""
    lines.append(
        f"| Overall Quality (0-10) "
        f"| {o.group_a.mean:.1f} "
        f"[{o.group_a.ci_lower:.1f}, {o.group_a.ci_upper:.1f}] "
        f"| {o.group_b.mean:.1f} "
        f"[{o.group_b.ci_lower:.1f}, {o.group_b.ci_upper:.1f}] "
        f"| {_fmt_diff(o.diff_mean, o.diff_ci_lower, o.diff_ci_upper)}"
        f"{sig} |",
    )

    # Per-dimension
    for dim in report.dimensions:
        c = dim.comparison
        sig = " *" if c.significant else ""
        lines.append(
            f"| {dim.dimension} "
            f"| {c.group_a.mean:.1f} "
            f"[{c.group_a.ci_lower:.1f}, {c.group_a.ci_upper:.1f}] "
            f"| {c.group_b.mean:.1f} "
            f"[{c.group_b.ci_lower:.1f}, {c.group_b.ci_upper:.1f}] "
            f"| {_fmt_diff(c.diff_mean, c.diff_ci_lower, c.diff_ci_upper)}"
            f"{sig} |",
        )

    # Consistency
    lines.append("")
    lines.append(
        f"Consistency (CV): "
        f"{report.raw_config}={o.cv_a:.2f}, "
        f"{report.kit_config}={o.cv_b:.2f}",
    )

    # Significance note
    lines.append("")
    lines.append(
        "[95% bootstrap CI] [* = significant: CI excludes zero]",
    )

    # Multi-turn conversation flow
    if report.multi_turn_metrics:
        lines.append("")
        lines.append("## Conversation Flow")
        lines.append("")
        raw_m = report.multi_turn_metrics.get(report.raw_config, {})
        kit_m = report.multi_turn_metrics.get(report.kit_config, {})
        lines.append(
            f"| Metric | {report.raw_config} | {report.kit_config} |",
        )
        lines.append("|---|---|---|")
        for key, label in [
            ("avg_turns", "Avg turns"),
            ("avg_human_responses", "Avg human responses"),
            ("avg_tool_calls", "Avg tool calls"),
            ("avg_compaction_events", "Auto-compaction events"),
        ]:
            rv = raw_m.get(key, 0)
            kv = kit_m.get(key, 0)
            lines.append(f"| {label} | {rv} | {kv} |")

    # Human simulator interaction samples
    if report.conversation_samples:
        lines.append("")
        lines.append("## Human Simulator Interactions")
        lines.append("")
        lines.append("| Config | Turn | Question | Response |")
        lines.append("|---|---|---|---|")
        for s in report.conversation_samples[:10]:
            q = s.get("question", "")[:60]
            r = s.get("response", "")[:60]
            lines.append(
                f"| {s['config']} | {s['turn']} | {q} | {r} |",
            )

    # Pairwise judge results if available
    if report.pairwise_judge:
        pj = report.pairwise_judge
        lines.append("")
        lines.append(
            f"Pairwise judge: {pj.get('summary', 'N/A')}",
        )

    return "\n".join(lines)


def generate_json(report: PairwiseReport) -> dict[str, Any]:
    """Generate a JSON-serializable report dict."""
    return {
        "scenario_name": report.scenario_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_config": report.raw_config,
        "kit_config": report.kit_config,
        "overall": {
            "raw_mean": report.overall.group_a.mean,
            "kit_mean": report.overall.group_b.mean,
            "diff_mean": report.overall.diff_mean,
            "significant": report.overall.significant,
            "cohens_d": report.overall.cohens_d,
        },
        "dimensions": [
            {
                "name": d.dimension,
                "raw_mean": d.comparison.group_a.mean,
                "kit_mean": d.comparison.group_b.mean,
                "diff_mean": d.comparison.diff_mean,
                "significant": d.comparison.significant,
            }
            for d in report.dimensions
        ],
        "kit_wins": report.kit_wins,
        "pairwise_judge": report.pairwise_judge,
        "multi_turn_metrics": report.multi_turn_metrics,
        "conversation_samples": report.conversation_samples,
    }


def write_report(
    report: PairwiseReport,
    output_dir: Path,
    fmt: str = "both",
) -> list[Path]:
    """Write report files to disk.

    Args:
        report: The PairwiseReport to serialize.
        output_dir: Directory for output files.
        fmt: "json", "markdown", or "both".

    Returns:
        List of written file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ",
    )
    slug = _scenario_slug(report.scenario_name)
    paths: list[Path] = []

    if fmt in ("json", "both"):
        json_path = output_dir / f"{slug}-{timestamp}.json"
        data = generate_json(report)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.write("\n")
        paths.append(json_path)

    if fmt in ("markdown", "both"):
        md_path = output_dir / f"{slug}-{timestamp}.md"
        md = generate_markdown(report)
        with open(md_path, "w") as f:
            f.write(md)
            f.write("\n")
        paths.append(md_path)

    return paths


def _fmt_diff(
    mean: float,
    ci_lower: float,
    ci_upper: float,
) -> str:
    """Format a difference with CI."""
    sign = "+" if mean >= 0 else ""
    return (
        f"{sign}{mean:.1f} "
        f"[{'+' if ci_lower >= 0 else ''}{ci_lower:.1f}, "
        f"{'+' if ci_upper >= 0 else ''}{ci_upper:.1f}]"
    )


def _scenario_slug(name: str) -> str:
    """Convert a scenario name to a filesystem-safe slug."""
    slug = name.lower()
    safe: list[str] = []
    for ch in slug:
        if ch.isalnum() or ch == "-":
            safe.append(ch)
        elif ch in (" ", "_"):
            safe.append("-")
    result = "-".join(part for part in "".join(safe).split("-") if part)
    return result[:80]

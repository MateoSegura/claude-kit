"""Benchmark entry point — run benchmarks from the command line.

Usage:
    python -m test.benchmark <scenario.yml> [--runs N] [--model MODEL]

Examples:
    # Run with defaults
    python -m test.benchmark test/scenarios/benchmarks/health-endpoint.yml

    # Run with 5 repetitions using Haiku (cheap)
    python -m test.benchmark test/scenarios/benchmarks/bug-fix.yml \
        --runs 5 --model claude-haiku-4-5-20251001

    # Output to a specific directory
    python -m test.benchmark test/scenarios/benchmarks/auth-service.yml \
        --output test/results/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from test.benchmark.comparator import PairwiseComparator
from test.benchmark.report import generate_markdown, write_report
from test.benchmark.runner import BenchmarkRunner
from test.engine.config import EvalScenario, RunConfig
from test.scoring.statistical import StatisticalAnalyzer


def _load_scenario(path: Path, overrides: dict) -> EvalScenario:
    """Load an EvalScenario from a YAML file with optional overrides."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    configs = [
        RunConfig(
            name=c["name"],
            plugins=c.get("plugins", []),
            system_prompt=c.get("system_prompt"),
        )
        for c in raw.get("configs", [])
    ]

    # Parse human simulator config
    human_raw = raw.get("human", {})

    return EvalScenario(
        name=raw["name"],
        description=raw.get("description", ""),
        prompt=raw["prompt"],
        configs=configs,
        model=overrides.get("model", raw.get("model", "claude-sonnet-4-20250514")),
        max_turns=raw.get("max_turns", 20),
        max_tokens=raw.get("max_tokens", 4096),
        runs=overrides.get("runs", raw.get("runs", 1)),
        follow_up_prompts=raw.get("follow_ups", []),
        human_persona=human_raw.get("persona"),
        human_model=human_raw.get("model", "claude-haiku-4-5-20251001"),
        human_max_responses=human_raw.get("max_responses", 10),
        auto_respond=raw.get("auto_respond", True),
        executor_type=overrides.get("executor", raw.get("executor", "sdk")),
    )


def main() -> int:
    """Run a benchmark scenario and produce a comparison report."""
    parser = argparse.ArgumentParser(
        description="Run claude-kit benchmarks",
    )
    parser.add_argument(
        "scenario",
        type=Path,
        help="Path to a benchmark scenario YAML file",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Override number of runs per config",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model for the main conversation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("test/results"),
        help="Output directory for reports (default: test/results/)",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=Path("plugins"),
        help="Directory containing plugins (default: plugins/)",
    )
    parser.add_argument(
        "--executor",
        type=str,
        choices=["sdk", "api", "session"],
        default="sdk",
        help="Executor: sdk | api | session (multi-turn CLI)",
    )
    args = parser.parse_args()

    if not args.scenario.exists():
        print(f"Error: scenario file not found: {args.scenario}")
        return 1

    overrides: dict = {}
    if args.runs is not None:
        overrides["runs"] = args.runs
    if args.model is not None:
        overrides["model"] = args.model
    if args.executor is not None:
        overrides["executor"] = args.executor

    scenario = _load_scenario(args.scenario, overrides)

    print(f"Benchmark: {scenario.name}")
    print(f"Model: {scenario.model}")
    print(f"Configs: {[c.name for c in scenario.configs]}")
    print(f"Runs per config: {scenario.runs}")
    print()

    # Load expected strings from scenario YAML for scoring
    with open(args.scenario) as f:
        raw = yaml.safe_load(f)
    expected_strings = raw.get("expected_strings", [])
    score_kwargs = {"expected_strings": expected_strings}

    print(f"Executor: {args.executor}")

    runner = BenchmarkRunner(
        scenario=scenario,
        plugins_dirs=[args.plugins_dir],
        executor_type=args.executor,
    )

    benchmark = runner.run_all(score_kwargs=score_kwargs)
    scored_runs = runner.scored_runs

    print(f"Completed {len(benchmark.results)} total runs")
    print()

    # Summary
    summary = benchmark.summary()
    for config_name, stats in summary.items():
        print(f"  {config_name}:")
        print(f"    avg_turns: {stats['avg_turns']:.1f}")
        print(f"    avg_cost:  ${stats['avg_cost_usd']:.4f}")
        print()

    # Pairwise comparison if we have 2+ configs
    if len(scenario.configs) >= 2:
        raw_name = scenario.configs[0].name
        kit_name = scenario.configs[1].name

        raw_scored = [
            (sr.result, sr.scores)
            for sr in scored_runs
            if sr.result.config_name == raw_name
        ]
        kit_scored = [
            (sr.result, sr.scores)
            for sr in scored_runs
            if sr.result.config_name == kit_name
        ]

        comparator = PairwiseComparator(
            analyzer=StatisticalAnalyzer(seed=42),
        )
        report = comparator.compare(
            raw_scored,
            kit_scored,
            scenario_name=scenario.name,
            raw_config=raw_name,
            kit_config=kit_name,
        )

        # Print markdown
        md = generate_markdown(report)
        print(md)

        # Write reports
        paths = write_report(report, args.output)
        print()
        for p in paths:
            print(f"Report written: {p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

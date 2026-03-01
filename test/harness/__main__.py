"""Entry point for the test harness.

Usage:
    python3 -m test.harness scenarios/smoke.yml              # run single scenario
    python3 -m test.harness scenarios/ --all                  # run all .yml in dir
    python3 -m test.harness scenarios/smoke.yml --output dir/ # custom output dir
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from test.harness.runner import run_scenario
from test.harness.scenario import load_scenario, load_all_scenarios
from test.harness.report import write_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python3 -m test.harness",
        description="claude-kit test harness — run scenarios against the Anthropic API",
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to a scenario YAML file or a directory of scenarios",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Run all .yml scenarios in the given directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for JSON reports (default: test/results/)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    # Require ANTHROPIC_API_KEY
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY environment variable is not set.\n"
            "Export your API key before running the harness:\n"
            "  export ANTHROPIC_API_KEY='sk-ant-...'\n",
            file=sys.stderr,
        )
        return 1

    target = Path(args.path)
    output_dir = Path(args.output) if args.output else Path("test/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve scenario list
    if target.is_dir():
        if not args.run_all:
            print(
                f"ERROR: {target} is a directory. Use --all to run every scenario in it.",
                file=sys.stderr,
            )
            return 1
        scenarios = load_all_scenarios(target)
        if not scenarios:
            print(f"ERROR: No .yml scenario files found in {target}", file=sys.stderr)
            return 1
    elif target.is_file():
        scenarios = [load_scenario(target)]
    else:
        print(f"ERROR: {target} does not exist.", file=sys.stderr)
        return 1

    # Execute each scenario
    total = len(scenarios)
    passed = 0
    failed = 0

    for i, scenario in enumerate(scenarios, 1):
        label = f"[{i}/{total}]"
        print(f"\n{label} Running scenario: {scenario.name}")
        print(f"  Model: {scenario.model} | Turns: {len(scenario.turns)}")

        try:
            result = run_scenario(scenario)
            report_path = write_report(result, output_dir)

            status = "PASS" if result.all_passed else "FAIL"
            cost = f"${result.metrics.estimated_cost_usd:.4f}"
            tokens = (
                f"{result.metrics.total_tokens_in}in/"
                f"{result.metrics.total_tokens_out}out"
            )
            print(f"  Result: {status} | Tokens: {tokens} | Cost: {cost}")
            print(f"  Report: {report_path}")

            if result.all_passed:
                passed += 1
            else:
                failed += 1
                for v in result.validation_details:
                    if not v["passed"]:
                        print(f"    FAIL: {v['type']} — {v.get('reason', '')}")
        except Exception as exc:
            failed += 1
            print(f"  ERROR: {exc}", file=sys.stderr)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {total} total")
    print(f"{'=' * 50}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

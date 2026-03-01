"""Report generator — write JSON reports from scenario execution results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from test.harness.runner import ScenarioResult


def _build_report(result: ScenarioResult) -> dict[str, Any]:
    """Build a JSON-serializable report dictionary from a ScenarioResult.

    The report structure:
        {
            "scenario": "<name>",
            "source_path": "<original YAML path>",
            "model": "<model ID>",
            "timestamp": "<ISO 8601>",
            "metrics": { ... },
            "claude_kit_telemetry": {
                "session_id": "...",
                "events_count": N,
                "events": [...]
            },
            "validations": {
                "passed": N,
                "failed": N,
                "details": [...]
            }
        }
    """
    passed_count = sum(1 for v in result.validation_details if v.get("passed"))
    failed_count = sum(1 for v in result.validation_details if not v.get("passed"))

    return {
        "scenario": result.scenario.name,
        "source_path": result.scenario.source_path,
        "model": result.scenario.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": result.metrics.to_dict(),
        "claude_kit_telemetry": {
            "session_id": result.metrics.session_id,
            "events_count": len(result.metrics.telemetry_events),
            "events": result.metrics.telemetry_events,
        },
        "validations": {
            "passed": passed_count,
            "failed": failed_count,
            "details": result.validation_details,
        },
    }


def _scenario_slug(name: str) -> str:
    """Convert a scenario name to a filesystem-safe slug."""
    slug = name.lower()
    # Replace non-alphanumeric characters with hyphens
    safe = []
    for ch in slug:
        if ch.isalnum() or ch == "-":
            safe.append(ch)
        elif ch in (" ", "_"):
            safe.append("-")
    # Collapse consecutive hyphens and strip edges
    result = "-".join(part for part in "".join(safe).split("-") if part)
    return result[:80]  # keep filenames reasonable


def write_report(result: ScenarioResult, output_dir: Path) -> Path:
    """Write a JSON report file for a scenario execution result.

    The filename follows the pattern: <scenario-slug>-<timestamp>.json

    Args:
        result: The ScenarioResult to serialize.
        output_dir: Directory where the report file will be written.

    Returns:
        Path to the written report file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    report = _build_report(result)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _scenario_slug(result.scenario.name)
    filename = f"{slug}-{timestamp}.json"

    report_path = output_dir / filename
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
        f.write("\n")

    return report_path

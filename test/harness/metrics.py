"""Session metrics — token counting, cost estimation, and telemetry capture."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Pricing per 1M tokens (USD) as of 2025.
# Update these when Anthropic publishes new pricing.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}


@dataclass
class SessionMetrics:
    """Aggregated metrics for a single scenario execution session.

    Attributes:
        session_id: Unique identifier for this run.
        scenario_name: Name of the scenario that was executed.
        model: Model ID used for the API calls.
        total_tokens_in: Sum of input tokens across all turns.
        total_tokens_out: Sum of output tokens across all turns.
        estimated_cost_usd: Estimated cost based on MODEL_PRICING.
        wall_clock_s: Total wall clock time in seconds.
        turns: Number of API call turns executed.
        human_sim_count: Number of human_sim turns injected.
        auto_compactions: Number of auto-compaction events detected (reserved).
        files_in_project: Count of files in the project directory (context).
        lines_in_project: Count of lines across project files (context).
        telemetry_events: Raw telemetry events loaded from claude-kit JSONL.
    """

    session_id: str = ""
    scenario_name: str = ""
    model: str = ""
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    wall_clock_s: float = 0.0
    turns: int = 0
    human_sim_count: int = 0
    auto_compactions: int = 0
    files_in_project: int = 0
    lines_in_project: int = 0
    telemetry_events: list[dict[str, Any]] = field(default_factory=list)

    def add_turn_usage(self, tokens_in: int, tokens_out: int) -> None:
        """Accumulate token usage from a single turn."""
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.turns += 1

    def compute_cost(self) -> None:
        """Compute estimated_cost_usd from accumulated token counts.

        Uses MODEL_PRICING lookup. Falls back to sonnet pricing if the
        model is not in the table.
        """
        pricing = MODEL_PRICING.get(
            self.model,
            MODEL_PRICING.get(
                "claude-sonnet-4-20250514", {"input": 3.0, "output": 15.0}
            ),
        )
        input_cost = (self.total_tokens_in / 1_000_000) * pricing["input"]
        output_cost = (self.total_tokens_out / 1_000_000) * pricing["output"]
        self.estimated_cost_usd = input_cost + output_cost

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to a JSON-compatible dictionary."""
        return {
            "session_id": self.session_id,
            "scenario_name": self.scenario_name,
            "model": self.model,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "wall_clock_s": round(self.wall_clock_s, 3),
            "turns": self.turns,
            "human_sim_count": self.human_sim_count,
            "auto_compactions": self.auto_compactions,
            "files_in_project": self.files_in_project,
            "lines_in_project": self.lines_in_project,
            "telemetry_events_count": len(self.telemetry_events),
        }


def load_telemetry_events(
    session_id: str, telemetry_dir: Path | None = None
) -> list[dict[str, Any]]:
    """Load claude-kit JSONL telemetry events for a given session.

    Searches for a JSONL file matching the session_id in the telemetry
    directory. Each line in the file is a JSON object representing one
    telemetry event.

    Args:
        session_id: The CLAUDE_KIT_SESSION_ID to search for.
        telemetry_dir: Directory containing JSONL telemetry files.
                       Defaults to ~/.claude-kit/telemetry/.

    Returns:
        List of parsed telemetry event dicts. Empty list if no file found.
    """
    if not session_id:
        return []

    if telemetry_dir is None:
        telemetry_dir = Path.home() / ".claude-kit" / "telemetry"

    if not telemetry_dir.is_dir():
        return []

    events: list[dict[str, Any]] = []

    # Search for JSONL files that contain the session ID
    for jsonl_path in telemetry_dir.glob("*.jsonl"):
        try:
            with open(jsonl_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if event.get("session_id") == session_id:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue

    return events

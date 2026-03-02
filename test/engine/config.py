"""Unified configuration and result data models for benchmarks and evaluations.

Merges the data models from benchmark/config.py and harness/metrics.py
into a single coherent set of types used by the engine layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Pricing per 1M tokens (USD).
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
}


@dataclass
class RunConfig:
    """Configuration for a single benchmark run variant.

    Attributes:
        name: Identifier for this config (e.g., "raw", "kit").
        plugins: List of plugin directory names to load.
        system_prompt: Optional override; if set, used instead of
            building from plugins.
    """

    name: str
    plugins: list[str]
    system_prompt: str | None = None


@dataclass
class EvalScenario:
    """Defines a complete evaluation scenario.

    Unifies BenchmarkScenario (benchmark layer) and Scenario (harness layer)
    into a single type that supports both scripted-turn and free-form modes.

    Attributes:
        name: Human-readable scenario name.
        description: What the scenario tests.
        prompt: Initial user prompt sent to Claude.
        configs: List of RunConfig variants to compare.
        model: Model ID for the main conversation.
        max_turns: Maximum conversation turns before stopping.
        max_tokens: Maximum tokens per API call.
        runs: Number of repetitions per config.
    """

    name: str
    description: str
    prompt: str
    configs: list[RunConfig]
    model: str = "claude-sonnet-4-20250514"
    max_turns: int = 20
    max_tokens: int = 4096
    runs: int = 1

    # Multi-turn support
    follow_up_prompts: list[str] = field(default_factory=list)
    human_persona: str | None = None
    human_model: str = "claude-haiku-4-5-20251001"
    human_max_responses: int = 10
    auto_respond: bool = True
    executor_type: str = "sdk"


@dataclass
class Transcript:
    """A single message in the conversation transcript.

    Attributes:
        role: "user", "assistant", "system", "tool_use", or "tool_result".
        content: Message text.
        tokens_in: Input tokens for this turn (assistant only).
        tokens_out: Output tokens for this turn (assistant only).
        model: Which model responded (assistant messages).
        tool_name: Tool name for tool_use/tool_result entries.
        tool_use_id: Links tool_use to tool_result.
        is_error: Whether a tool_result was an error.
        subtype: System message subtype (e.g. "compact").
        content_types: Block types in this message (e.g. ["text", "tool_use"]).
    """

    role: str
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None
    tool_name: str | None = None
    tool_use_id: str | None = None
    is_error: bool = False
    subtype: str | None = None
    content_types: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    """Result from a single benchmark run.

    Attributes:
        config_name: Which RunConfig produced this result.
        responses: List of assistant response texts.
        turns: Number of API call turns.
        total_tokens_in: Sum of input tokens across all turns.
        total_tokens_out: Sum of output tokens across all turns.
        wall_clock_s: Total elapsed wall clock time in seconds.
        telemetry_events: In-memory telemetry events from claude_kit.
        model: Model ID used for the conversation.
        transcript: Full message-level transcript.
        error: Error message if the run failed.
        cost_usd: Actual cost from SDK (if available).
        usage: Full SDK usage dict (cache tokens, service tier, etc.).
        session_id: SDK session_id.
        duration_ms: SDK duration_ms.
        duration_api_ms: SDK duration_api_ms.
        tool_use_count: Total tool calls in the session.
        mcp_call_count: Tool calls starting with mcp__.
        compact_count: Auto-compact events observed.
    """

    config_name: str
    responses: list[str]
    turns: int
    total_tokens_in: int
    total_tokens_out: int
    wall_clock_s: float
    telemetry_events: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    transcript: list[Transcript] = field(default_factory=list)
    error: str | None = None
    cost_usd: float | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    duration_ms: int = 0
    duration_api_ms: int = 0
    tool_use_count: int = 0
    mcp_call_count: int = 0
    compact_count: int = 0

    # Multi-turn + history
    human_response_count: int = 0
    pre_compact_snapshots: list[dict[str, Any]] = field(default_factory=list)

    @property
    def estimated_cost_usd(self) -> float:
        """Compute estimated cost based on token counts and model pricing.

        If cost_usd is set (from real SDK data), returns that directly.
        Otherwise falls back to estimation from token counts.
        """
        if self.cost_usd is not None:
            return self.cost_usd
        rates = MODEL_PRICING.get(self.model, (3.0, 15.0))
        cost_in = self.total_tokens_in * rates[0]
        cost_out = self.total_tokens_out * rates[1]
        return (cost_in + cost_out) / 1_000_000


@dataclass
class BenchmarkResult:
    """Aggregated results from a full benchmark run.

    Attributes:
        scenario_name: Name of the scenario that was benchmarked.
        results: All RunResult instances across all configs and runs.
    """

    scenario_name: str
    results: list[RunResult]

    def summary(self) -> dict[str, Any]:
        """Produce per-config summary with averages."""
        groups: dict[str, list[RunResult]] = {}
        for r in self.results:
            groups.setdefault(r.config_name, []).append(r)

        out: dict[str, Any] = {}
        for config_name, runs in groups.items():
            n = len(runs)
            out[config_name] = {
                "runs": n,
                "avg_turns": sum(r.turns for r in runs) / n,
                "avg_tokens_in": sum(r.total_tokens_in for r in runs) / n,
                "avg_tokens_out": sum(r.total_tokens_out for r in runs) / n,
                "avg_wall_clock_s": sum(r.wall_clock_s for r in runs) / n,
                "avg_cost_usd": sum(r.estimated_cost_usd for r in runs) / n,
            }
        return out

"""Auto-runner entry point for autonomous and CI session modes.

Invoked as a subprocess by the claude-kit CLI:
    python -m test.engine.auto_runner --prompt "..." --mode autonomous ...

This module bridges the stdlib-only CLI with the SDK-dependent SessionDriver.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from claude_kit.ci_output import JsonlWriter
from claude_kit.driver_config import DriverMode, SessionDriverConfig
from claude_kit.renderer import TerminalRenderer
from test.engine.config import EvalScenario, RunConfig
from test.engine.driver import SessionDriver
from test.engine.human import HumanSimulator
from test.engine.input_strategies import SimulatedInput

# Guard anthropic import
try:
    import anthropic
except ModuleNotFoundError:  # CI: anthropic not installed
    anthropic = None  # type: ignore[assignment]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-runner for autonomous/CI sessions",
    )
    parser.add_argument("--prompt", required=True, help="Initial prompt")
    parser.add_argument("--mode", choices=["autonomous", "ci"], default="autonomous")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument("--plugin-dir", action="append", dest="plugin_dirs", default=[])
    parser.add_argument("--plugins-dir", default=None)
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--human-persona", default=None)
    parser.add_argument("--human-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--human-max-responses", type=int, default=10)
    parser.add_argument("--permission-mode", default="bypassPermissions")
    return parser.parse_args(argv)


def _make_display_callback(
    mode: str,
) -> tuple[Any, Callable[[str, dict[str, Any]], None]]:
    """Create display callback for the given mode.

    Returns (display_object, callback_fn).
    """
    if mode == "ci":
        writer = JsonlWriter()

        def ci_cb(event_type: str, payload: dict[str, Any]) -> None:
            writer.write_event(event_type, payload)

        return writer, ci_cb

    renderer = TerminalRenderer()

    def term_cb(event_type: str, payload: dict[str, Any]) -> None:
        if event_type == "assistant.text":
            renderer.render_assistant_text(
                payload.get("text", ""), payload.get("model")
            )
        elif event_type == "tool.use":
            renderer.render_tool_use(
                payload.get("name", ""), payload.get("input_preview", "")
            )
        elif event_type == "tool.result":
            renderer.render_tool_result(
                payload.get("tool_use_id", ""),
                payload.get("is_error", False),
                payload.get("preview", ""),
            )
        elif event_type == "human.response":
            renderer.render_human_response(payload.get("text", ""))
        elif event_type == "session.compact":
            renderer.render_compact(None)
        elif event_type == "session.end":
            renderer.render_session_end(
                payload.get("turns", 0),
                payload.get("cost"),
                payload.get("tokens_in", 0),
                payload.get("tokens_out", 0),
                payload.get("elapsed", 0.0),
            )

    return renderer, term_cb


def main(argv: list[str] | None = None) -> int:
    """Run an autonomous or CI session and return exit code."""
    args = _parse_args(argv)

    # Build driver config
    mode = DriverMode.AUTONOMOUS if args.mode == "autonomous" else DriverMode.CI
    driver_config = SessionDriverConfig(
        mode=mode,
        model=args.model,
        max_turns=args.max_turns,
        permission_mode=args.permission_mode,
        history=args.history,
        human_model=args.human_model,
        human_persona=args.human_persona,
        human_max_responses=args.human_max_responses,
    )

    # Build scenario
    scenario = EvalScenario(
        name="cli-session",
        description="CLI-initiated session",
        prompt=args.prompt,
        configs=[RunConfig(name="session", plugins=[])],
        model=args.model,
        max_turns=args.max_turns,
    )

    # Build input strategy
    human = HumanSimulator(
        persona=args.human_persona,
        model=args.human_model,
        max_responses=args.human_max_responses,
    )
    client = anthropic.Anthropic() if anthropic else None
    input_strategy = SimulatedInput(
        human=human,
        anthropic_client=client,
    )

    # Build display callback
    _display, on_event = _make_display_callback(args.mode)

    # Build plugin dirs
    plugin_dirs = [Path(d) for d in args.plugin_dirs] if args.plugin_dirs else None
    plugins_dir = Path(args.plugins_dir) if args.plugins_dir else None
    all_dirs = plugin_dirs or ([plugins_dir] if plugins_dir else None)

    # Build run config
    config = RunConfig(name="session", plugins=[])

    # Create driver
    driver = SessionDriver(
        scenario=scenario,
        input_strategy=input_strategy,
        plugins_dirs=all_dirs,
        driver_config=driver_config,
        on_event=on_event,
    )

    # Execute
    try:
        result = driver.execute(config)
        if args.mode == "ci":
            # CI mode: output full result as JSON
            print(
                json.dumps(
                    {
                        "config_name": result.config_name,
                        "turns": result.turns,
                        "cost_usd": result.cost_usd,
                        "total_tokens_in": result.total_tokens_in,
                        "total_tokens_out": result.total_tokens_out,
                        "wall_clock_s": result.wall_clock_s,
                        "error": result.error,
                        "tool_use_count": result.tool_use_count,
                        "mcp_call_count": result.mcp_call_count,
                        "compact_count": result.compact_count,
                        "human_response_count": result.human_response_count,
                    },
                    indent=2,
                )
            )
        return 0 if not result.error else 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

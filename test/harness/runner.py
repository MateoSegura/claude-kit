"""Test execution engine — drive conversations via the Anthropic Messages API."""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

import anthropic

from test.harness.metrics import SessionMetrics, load_telemetry_events
from test.harness.scenario import Scenario, Turn


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    type: str
    passed: bool
    reason: str = ""
    expected: str = ""
    actual: str = ""


@dataclass
class ScenarioResult:
    """Complete result from executing a scenario."""

    scenario: Scenario
    metrics: SessionMetrics
    responses: list[str]
    validation_details: list[dict[str, Any]]
    all_passed: bool = True
    error: str | None = None


def _extract_text(message: anthropic.types.Message) -> str:
    """Extract the text content from an Anthropic Message response."""
    parts = []
    for block in message.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts)


def _validate_response_contains(response: str, value: str) -> ValidationResult:
    """Check that a response string contains the expected value (case-insensitive)."""
    found = value.lower() in response.lower()
    return ValidationResult(
        type="response_contains",
        passed=found,
        expected=value,
        actual=response[:200] if not found else "",
        reason="" if found else f"Response does not contain '{value}'",
    )


def _validate_expected_turn(response: str, turn: Turn) -> list[ValidationResult]:
    """Validate the previous response against an 'expected' turn's constraints."""
    results = []
    for substring in turn.contains:
        results.append(_validate_response_contains(response, substring))
    if turn.max_tokens is not None and len(response.split()) > turn.max_tokens:
        results.append(
            ValidationResult(
                type="max_tokens",
                passed=False,
                reason=(
                    f"Response exceeded max_tokens word estimate: "
                    f"{len(response.split())} words > {turn.max_tokens}"
                ),
            )
        )
    return results


def _prepare_library_session(
    scenario: Scenario,
) -> tuple[list[Any], list[dict[str, Any]]]:
    """Prepare a session using the claude_kit library.

    Resolves plugins via PluginResolver, captures telemetry
    in memory, and builds a system prompt from loaded plugins.

    Returns:
        Tuple of (system_prompt_parts, captured_events).
    """
    from pathlib import Path

    from claude_kit import (
        PluginResolver,
        SessionManager,
        TelemetryEmitter,
        build_system_prompt,
    )

    plugins_dir = Path(__file__).resolve().parents[2] / "plugins"
    captured: list[dict[str, Any]] = []

    telemetry = TelemetryEmitter(
        level="debug",
        on_emit=captured.append,
    )

    resolver = PluginResolver(
        plugins_dirs=[plugins_dir],
        telemetry=telemetry,
    )
    session_mgr = SessionManager(resolver, telemetry=telemetry)
    session = session_mgr.prepare(
        kit_names=scenario.plugins,
    )

    prompt = build_system_prompt(session.plugins)
    session_mgr.finalize(session)

    return prompt, captured


def run_scenario(
    scenario: Scenario,
    mode: str | None = None,
) -> ScenarioResult:
    """Execute a scenario against the Anthropic Messages API.

    Walks through each turn in the scenario:
      - 'user' turns are sent to the API as user messages.
      - 'human_sim' turns are injected as user messages without calling the API
        (they appear in the conversation history for the next API call).
      - 'expected' turns validate the most recent assistant response.

    Args:
        scenario: A parsed Scenario object.
        mode: Override scenario.mode ("subprocess" or "library").

    Returns:
        ScenarioResult with metrics, responses, and validation outcomes.
    """
    effective_mode = mode or scenario.mode

    # Library mode: resolve plugins and capture telemetry in-memory
    system_prompt = None
    library_events: list[dict[str, Any]] = []
    if effective_mode == "library" and scenario.plugins:
        system_prompt, library_events = _prepare_library_session(
            scenario,
        )

    client = anthropic.Anthropic()
    session_id = os.environ.get("CLAUDE_KIT_SESSION_ID", str(uuid.uuid4()))

    metrics = SessionMetrics(
        session_id=session_id,
        scenario_name=scenario.name,
        model=scenario.model,
    )

    messages: list[dict[str, str]] = []
    responses: list[str] = []
    validation_details: list[dict[str, Any]] = []
    all_passed = True
    last_response = ""
    has_error = False

    start_time = time.monotonic()

    for turn in scenario.turns:
        if turn.role == "user":
            messages.append({"role": "user", "content": turn.content})

            try:
                turn_start = time.monotonic()
                create_kwargs: dict[str, Any] = {
                    "model": scenario.model,
                    "max_tokens": (turn.max_tokens or scenario.max_tokens),
                    "messages": messages,
                }
                if system_prompt:
                    create_kwargs["system"] = system_prompt
                response = client.messages.create(**create_kwargs)
                _ = time.monotonic() - turn_start  # track per-turn elapsed time

                # Extract usage
                tokens_in = response.usage.input_tokens
                tokens_out = response.usage.output_tokens
                metrics.add_turn_usage(tokens_in, tokens_out)

                # Extract text
                last_response = _extract_text(response)
                responses.append(last_response)

                # Add assistant turn to conversation history
                messages.append({"role": "assistant", "content": last_response})

            except anthropic.APIError as exc:
                has_error = True
                last_response = ""
                responses.append("")
                validation_details.append(
                    {
                        "type": "api_error",
                        "passed": False,
                        "reason": f"API error on user turn: {exc}",
                    }
                )
                all_passed = False
                break

        elif turn.role == "human_sim":
            # Inject a simulated human response as a user message.
            # This does not call the API — it just adds to the message history
            # so the next API call sees it as prior context.
            messages.append({"role": "user", "content": turn.content})
            metrics.human_sim_count += 1

        elif turn.role == "expected":
            # Validate the most recent assistant response
            if not last_response and not has_error:
                validation_details.append(
                    {
                        "type": "expected_no_response",
                        "passed": False,
                        "reason": (
                            "Expected turn has no prior assistant response to validate"
                        ),
                    }
                )
                all_passed = False
                continue

            results = _validate_expected_turn(last_response, turn)
            for vr in results:
                detail = {
                    "type": vr.type,
                    "passed": vr.passed,
                    "reason": vr.reason,
                    "expected": vr.expected,
                }
                if not vr.passed:
                    detail["actual_snippet"] = vr.actual
                    all_passed = False
                validation_details.append(detail)

    # Run post-scenario validations
    for validation in scenario.validations:
        if validation.type == "response_contains":
            vr = _validate_response_contains(last_response, validation.value)
            detail: dict[str, Any] = {
                "type": vr.type,
                "passed": vr.passed,
                "reason": vr.reason,
                "expected": vr.expected,
            }
            if not vr.passed:
                detail["actual_snippet"] = vr.actual
                all_passed = False
            validation_details.append(detail)

        elif validation.type == "no_error":
            passed = not has_error
            validation_details.append(
                {
                    "type": "no_error",
                    "passed": passed,
                    "reason": "" if passed else "An API error occurred during the run",
                }
            )
            if not passed:
                all_passed = False

    # Finalize metrics
    metrics.wall_clock_s = time.monotonic() - start_time
    metrics.compute_cost()

    # Load telemetry: in-memory for library mode, JSONL for subprocess
    if library_events:
        metrics.telemetry_events = library_events
    else:
        kit_session_id = os.environ.get("CLAUDE_KIT_SESSION_ID", "")
        if kit_session_id:
            metrics.telemetry_events = load_telemetry_events(
                kit_session_id,
            )

    return ScenarioResult(
        scenario=scenario,
        metrics=metrics,
        responses=responses,
        validation_details=validation_details,
        all_passed=all_passed,
    )

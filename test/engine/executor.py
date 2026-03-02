"""ConversationExecutor — drives a single benchmark conversation.

Merges the execution logic from harness/runner.py (turn-by-turn API calls)
and benchmark/runner.py (multi-turn with HumanSimulator) into a unified
executor. Single responsibility: drive one conversation, return RunResult.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

try:
    import anthropic
except ModuleNotFoundError:  # CI: anthropic not installed
    anthropic = None  # type: ignore[assignment]

from test.engine.config import EvalScenario, RunConfig, RunResult, Transcript
from test.engine.human import HumanSimulator, NeedsInputResult
from test.engine.session_factory import SessionFactory


class ConversationExecutor:
    """Execute a single benchmark conversation via the Anthropic SDK.

    Handles:
    - System prompt construction from plugins (via SessionFactory)
    - Multi-turn conversation with HumanSimulator for input detection
    - Token tracking and telemetry capture
    - Transcript recording for scoring
    """

    def __init__(
        self,
        scenario: EvalScenario,
        plugins_dirs: list[Path] | None = None,
        human: HumanSimulator | None = None,
    ) -> None:
        self.scenario = scenario
        self._factory = SessionFactory(plugins_dirs=plugins_dirs)
        self.human = human or HumanSimulator()

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a single conversation for the given config.

        Args:
            config: RunConfig specifying plugins and name.

        Returns:
            RunResult with responses, metrics, telemetry, and transcript.
        """
        client = anthropic.Anthropic()
        messages: list[dict[str, str]] = [
            {"role": "user", "content": self.scenario.prompt},
        ]
        transcript: list[Transcript] = [
            Transcript(role="user", content=self.scenario.prompt),
        ]

        # Build system prompt
        create_kwargs: dict[str, Any] = {}
        telemetry_events: list[dict[str, Any]] = []

        if config.system_prompt:
            create_kwargs["system"] = config.system_prompt
            telemetry_events.append({"event_type": "session.start"})
        elif config.plugins:
            system_prompt, captured, _ = self._factory.prepare(
                config.plugins,
            )
            if system_prompt:
                create_kwargs["system"] = system_prompt
                telemetry_events.extend(captured)
                if not any(e.get("event_type") == "session.start" for e in captured):
                    telemetry_events.append({"event_type": "session.start"})

        responses: list[str] = []
        total_in = 0
        total_out = 0
        turns = 0
        start = time.monotonic()

        for _ in range(self.scenario.max_turns):
            try:
                msg = client.messages.create(
                    model=self.scenario.model,
                    max_tokens=self.scenario.max_tokens,
                    messages=messages,
                    **create_kwargs,
                )
            except anthropic.APIError as exc:
                return RunResult(
                    config_name=config.name,
                    responses=responses,
                    turns=turns,
                    total_tokens_in=total_in,
                    total_tokens_out=total_out,
                    wall_clock_s=time.monotonic() - start,
                    telemetry_events=telemetry_events,
                    model=self.scenario.model,
                    transcript=transcript,
                    error=str(exc),
                )

            text = msg.content[0].text
            responses.append(text)
            total_in += msg.usage.input_tokens
            total_out += msg.usage.output_tokens
            turns += 1

            transcript.append(
                Transcript(
                    role="assistant",
                    content=text,
                    tokens_in=msg.usage.input_tokens,
                    tokens_out=msg.usage.output_tokens,
                ),
            )

            # Per-turn telemetry
            telemetry_events.append(
                {
                    "event_type": "turn.completed",
                    "payload": {
                        "turn": turns,
                        "tokens_in": msg.usage.input_tokens,
                        "tokens_out": msg.usage.output_tokens,
                    },
                },
            )

            if turns >= self.scenario.max_turns:
                break

            # Check if Claude needs human input
            check = NeedsInputResult.from_message(text)

            if not check.needs_input:
                break

            # Claude needs input — use the human simulator
            messages.append({"role": "assistant", "content": text})

            human_response = self.human.respond(messages, client)
            if human_response is None:
                messages.append({"role": "user", "content": "Continue."})
                transcript.append(
                    Transcript(role="user", content="Continue."),
                )
            else:
                messages.append({"role": "user", "content": human_response})
                transcript.append(
                    Transcript(role="human_sim", content=human_response),
                )
                telemetry_events.append(
                    {
                        "event_type": "human.responded",
                        "payload": {
                            "turn": turns,
                            "reason": check.reason,
                        },
                    },
                )

        elapsed = time.monotonic() - start

        # Session end telemetry
        telemetry_events.append(
            {
                "event_type": "session.end",
                "payload": {
                    "total_turns": turns,
                    "total_tokens_in": total_in,
                    "total_tokens_out": total_out,
                    "human_responses": self.human.response_count,
                    "wall_clock_s": round(elapsed, 3),
                },
            },
        )

        return RunResult(
            config_name=config.name,
            responses=responses,
            turns=turns,
            total_tokens_in=total_in,
            total_tokens_out=total_out,
            wall_clock_s=elapsed,
            telemetry_events=telemetry_events,
            model=self.scenario.model,
            transcript=transcript,
        )

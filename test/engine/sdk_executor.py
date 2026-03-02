"""SdkExecutor — drives a benchmark conversation via claude-code-sdk.

Uses the Claude Code SDK (claude_code_sdk.query) to run real conversations
through the Claude CLI, capturing cost, usage, and transcript data. This
executor talks to the actual Claude API through the CLI, unlike
ConversationExecutor which uses the anthropic SDK directly.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

try:
    import claude_code_sdk
    from claude_code_sdk import query
    from claude_code_sdk._errors import MessageParseError as _ParseError
    from claude_code_sdk._internal.message_parser import (
        parse_message as _original_parse,
    )
    from claude_code_sdk.types import (
        AssistantMessage,
        ClaudeCodeOptions,
        ResultMessage,
        TextBlock,
    )
except ModuleNotFoundError:  # CI: claude-code-sdk not installed
    claude_code_sdk = None  # type: ignore[assignment]
    query = None  # type: ignore[assignment]
    _ParseError = None  # type: ignore[assignment,misc]
    _original_parse = None  # type: ignore[assignment]
    AssistantMessage = None  # type: ignore[assignment,misc]
    ClaudeCodeOptions = None  # type: ignore[assignment,misc]
    ResultMessage = None  # type: ignore[assignment,misc]
    TextBlock = None  # type: ignore[assignment,misc]

from test.engine.config import EvalScenario, RunConfig, RunResult, Transcript
from test.engine.session_factory import SessionFactory

# Linux MAX_ARG_STRLEN is PAGE_SIZE*32 = 128KB per argument.
# Stay under this to avoid E2BIG when passing --system-prompt.
_MAX_CLI_ARG = 128 * 1024


class _SkipMessage:
    """Sentinel yielded for messages that failed to parse.

    The Claude CLI emits ``rate_limit_event`` messages which the SDK's
    ``parse_message`` does not recognise, raising ``MessageParseError``.
    Because the error occurs inside a ``yield`` expression, Python
    terminates the async generator — killing the stream before the
    ``ResultMessage`` (which follows immediately after) can be received.

    By patching ``parse_message`` to return this sentinel instead of
    raising, the generator stays alive and all downstream messages
    (including ``ResultMessage`` with cost/token data) are delivered.
    """


def _safe_parse_message(data: dict[str, Any]) -> Any:
    """Wrapper around the SDK's parse_message that never raises."""
    try:
        return _original_parse(data)
    except Exception:
        return _SkipMessage()


async def _stream_prompt(text: str):
    """Yield a single user message as an async iterable.

    The SDK's stream-json input mode reads from stdin, bypassing the
    OS per-argument size limit that blocks large --print prompts.
    The message format must match the SDK's expected streaming schema.
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": text},
    }


class SdkExecutor:
    """Execute a benchmark conversation via the Claude Code SDK.

    Uses claude_code_sdk.query() to drive a real conversation through
    the Claude CLI. Captures cost, usage, and transcript from the
    ResultMessage returned by the SDK.
    """

    def __init__(
        self,
        scenario: EvalScenario,
        plugins_dirs: list[Path] | None = None,
    ) -> None:
        self.scenario = scenario
        self._factory = SessionFactory(plugins_dirs=plugins_dirs)

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a single conversation for the given config.

        Args:
            config: RunConfig specifying plugins and name.

        Returns:
            RunResult with responses, metrics, telemetry, and transcript.
        """
        return asyncio.run(self._execute_async(config))

    async def _execute_async(self, config: RunConfig) -> RunResult:
        """Async implementation of execute."""
        # Build system prompt from plugins
        system_prompt: str | None = None
        telemetry_events: list[dict[str, Any]] = []

        if config.system_prompt:
            system_prompt = config.system_prompt
            telemetry_events.append({"event_type": "session.start"})
        elif config.plugins:
            prompt_text, captured, _ = self._factory.prepare(
                config.plugins,
            )
            if prompt_text:
                system_prompt = prompt_text
                telemetry_events.extend(captured)
                if not any(e.get("event_type") == "session.start" for e in captured):
                    telemetry_events.append(
                        {"event_type": "session.start"},
                    )

        # Configure SDK options
        options = ClaudeCodeOptions(
            max_turns=self.scenario.max_turns,
            model=self.scenario.model,
        )

        # Handle system prompt: if it fits in a CLI arg (<128KB),
        # pass via --system-prompt. Otherwise prepend to the user
        # prompt and use streaming input to bypass argv limits.
        effective_prompt: str | None = self.scenario.prompt
        use_streaming = False
        if system_prompt and len(system_prompt) <= _MAX_CLI_ARG:
            options.system_prompt = system_prompt
        elif system_prompt:
            effective_prompt = (
                "<system-context>\n"
                + system_prompt
                + "\n</system-context>\n\n"
                + self.scenario.prompt
            )
            # Total prompt exceeds CLI arg limit — must stream
            if len(effective_prompt) > _MAX_CLI_ARG:
                use_streaming = True

        # Build transcript
        transcript: list[Transcript] = [
            Transcript(role="user", content=self.scenario.prompt),
        ]
        responses: list[str] = []
        result_msg: ResultMessage | None = None

        start = time.monotonic()

        # Unset CLAUDECODE to avoid nested session error
        env_backup = os.environ.pop("CLAUDECODE", None)
        try:
            # Determine prompt arg: use async iterable for large
            # prompts so the SDK sends via stdin (stream-json mode)
            # instead of CLI argv which has a 128KB limit.
            if use_streaming:
                prompt_arg = _stream_prompt(effective_prompt)
            else:
                prompt_arg = effective_prompt

            # Patch parse_message to handle unknown message types
            # (e.g. rate_limit_event) without killing the async
            # generator. This ensures ResultMessage is received.
            with patch(
                "claude_code_sdk._internal.client.parse_message",
                _safe_parse_message,
            ):
                async for message in query(
                    prompt=prompt_arg,
                    options=options,
                ):
                    if isinstance(message, _SkipMessage):
                        continue

                    if isinstance(message, AssistantMessage):
                        text_parts = [
                            block.text
                            for block in message.content
                            if isinstance(block, TextBlock)
                        ]
                        if text_parts:
                            text = "\n".join(text_parts)
                            responses.append(text)
                            transcript.append(
                                Transcript(role="assistant", content=text),
                            )
                    elif isinstance(message, ResultMessage):
                        result_msg = message
        except Exception as exc:
            error_name = type(exc).__name__
            if result_msg is None and not responses:
                elapsed = time.monotonic() - start
                return RunResult(
                    config_name=config.name,
                    responses=responses,
                    turns=0,
                    total_tokens_in=0,
                    total_tokens_out=0,
                    wall_clock_s=elapsed,
                    telemetry_events=telemetry_events,
                    model=self.scenario.model,
                    transcript=transcript,
                    error=f"{error_name}: {exc}",
                )
        finally:
            if env_backup is not None:
                os.environ["CLAUDECODE"] = env_backup

        elapsed = time.monotonic() - start

        # Extract metrics from ResultMessage
        total_in = 0
        total_out = 0
        turns = 0
        cost: float | None = None

        if result_msg is not None:
            turns = result_msg.num_turns
            cost = result_msg.total_cost_usd
            if result_msg.usage:
                total_in = result_msg.usage.get("input_tokens", 0)
                total_out = result_msg.usage.get("output_tokens", 0)
            if result_msg.is_error and result_msg.result:
                telemetry_events.append(
                    {
                        "event_type": "session.error",
                        "payload": {"error": result_msg.result},
                    },
                )
        else:
            turns = len(responses)

        # Session end telemetry
        telemetry_events.append(
            {
                "event_type": "session.end",
                "payload": {
                    "total_turns": turns,
                    "total_tokens_in": total_in,
                    "total_tokens_out": total_out,
                    "wall_clock_s": round(elapsed, 3),
                    "cost_usd": cost,
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
            cost_usd=cost,
        )

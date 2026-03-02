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
        SystemMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
    )

    # ThinkingBlock may not exist in all SDK versions
    try:
        from claude_code_sdk.types import ThinkingBlock
    except ImportError:
        ThinkingBlock = None  # type: ignore[assignment,misc]
except ModuleNotFoundError:  # CI: claude-code-sdk not installed
    claude_code_sdk = None  # type: ignore[assignment]
    query = None  # type: ignore[assignment]
    _ParseError = None  # type: ignore[assignment,misc]
    _original_parse = None  # type: ignore[assignment]
    AssistantMessage = None  # type: ignore[assignment,misc]
    ClaudeCodeOptions = None  # type: ignore[assignment,misc]
    ResultMessage = None  # type: ignore[assignment,misc]
    SystemMessage = None  # type: ignore[assignment,misc]
    TextBlock = None  # type: ignore[assignment,misc]
    ToolResultBlock = None  # type: ignore[assignment,misc]
    ToolUseBlock = None  # type: ignore[assignment,misc]
    ThinkingBlock = None  # type: ignore[assignment,misc]

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

        # Per-message tracking
        turn_number = 0
        tool_counter = 0
        mcp_counter = 0
        compact_counter = 0

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
                        turn_number += 1

                        # Classify content block types
                        content_types: list[str] = []
                        text_parts: list[str] = []
                        turn_tool_calls: list[str] = []
                        turn_mcp_calls: list[str] = []

                        for block in message.content:
                            if isinstance(block, TextBlock):
                                content_types.append("text")
                                text_parts.append(block.text)
                            elif ToolUseBlock is not None and isinstance(
                                block, ToolUseBlock
                            ):
                                content_types.append("tool_use")
                                tool_counter += 1
                                tool_name = block.name
                                is_mcp = tool_name.startswith("mcp__")
                                if is_mcp:
                                    mcp_counter += 1
                                    parts = tool_name.split("__", 2)
                                    server = parts[1] if len(parts) >= 2 else "unknown"
                                    method = parts[2] if len(parts) == 3 else tool_name
                                    turn_mcp_calls.append(tool_name)
                                else:
                                    server = None
                                    method = None
                                turn_tool_calls.append(tool_name)

                                # Emit tool.used event
                                input_preview = (
                                    str(block.input)[:500] if block.input else ""
                                )
                                tool_payload: dict[str, Any] = {
                                    "tool_name": tool_name,
                                    "tool_use_id": block.id,
                                    "input_preview": input_preview,
                                    "is_mcp": is_mcp,
                                }
                                if is_mcp:
                                    tool_payload["mcp_server"] = server
                                    tool_payload["mcp_method"] = method
                                telemetry_events.append(
                                    {
                                        "event_type": "tool.used",
                                        "payload": tool_payload,
                                    },
                                )

                                # Add to transcript
                                transcript.append(
                                    Transcript(
                                        role="tool_use",
                                        content=input_preview,
                                        tool_name=tool_name,
                                        tool_use_id=block.id,
                                    ),
                                )
                            elif ToolResultBlock is not None and isinstance(
                                block, ToolResultBlock
                            ):
                                content_types.append("tool_result")
                                content_preview = (
                                    str(block.content)[:500] if block.content else ""
                                )
                                telemetry_events.append(
                                    {
                                        "event_type": "tool.result",
                                        "payload": {
                                            "tool_use_id": block.tool_use_id,
                                            "is_error": bool(block.is_error),
                                            "content_preview": content_preview,
                                        },
                                    },
                                )
                                transcript.append(
                                    Transcript(
                                        role="tool_result",
                                        content=content_preview,
                                        tool_use_id=block.tool_use_id,
                                        is_error=bool(block.is_error),
                                    ),
                                )
                            elif ThinkingBlock is not None and isinstance(
                                block, ThinkingBlock
                            ):
                                content_types.append("thinking")

                        # Emit message.assistant for text content
                        if text_parts:
                            text = "\n".join(text_parts)
                            responses.append(text)
                            transcript.append(
                                Transcript(
                                    role="assistant",
                                    content=text,
                                    model=getattr(message, "model", None),
                                    content_types=content_types,
                                ),
                            )
                            telemetry_events.append(
                                {
                                    "event_type": "message.assistant",
                                    "payload": {
                                        "model": getattr(message, "model", None),
                                        "text": text[:500],
                                        "content_types": content_types,
                                    },
                                },
                            )

                        # Emit turn.completed
                        telemetry_events.append(
                            {
                                "event_type": "turn.completed",
                                "payload": {
                                    "turn": turn_number,
                                    "model": getattr(message, "model", None),
                                    "content_types": list(dict.fromkeys(content_types)),
                                    "tool_calls": turn_tool_calls,
                                    "mcp_calls": turn_mcp_calls,
                                },
                            },
                        )

                    elif SystemMessage is not None and isinstance(
                        message, SystemMessage
                    ):
                        msg_subtype = getattr(message, "subtype", "") or ""
                        msg_data = getattr(message, "data", None)

                        if "compact" in msg_subtype.lower():
                            compact_counter += 1
                            telemetry_events.append(
                                {
                                    "event_type": "session.compact",
                                    "payload": {
                                        "subtype": msg_subtype,
                                        "data": msg_data,
                                    },
                                },
                            )
                        else:
                            telemetry_events.append(
                                {
                                    "event_type": "message.system",
                                    "payload": {
                                        "subtype": msg_subtype,
                                        "data": msg_data,
                                    },
                                },
                            )

                        transcript.append(
                            Transcript(
                                role="system",
                                content=str(msg_data) if msg_data else "",
                                subtype=msg_subtype,
                            ),
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
        usage_dict: dict[str, Any] = {}
        sdk_session_id: str | None = None
        sdk_duration_ms = 0
        sdk_duration_api_ms = 0

        if result_msg is not None:
            turns = result_msg.num_turns
            cost = result_msg.total_cost_usd
            usage_dict = result_msg.usage or {}
            sdk_session_id = getattr(result_msg, "session_id", None)
            sdk_duration_ms = getattr(result_msg, "duration_ms", 0) or 0
            sdk_duration_api_ms = getattr(result_msg, "duration_api_ms", 0) or 0
            if usage_dict:
                total_in = usage_dict.get("input_tokens", 0)
                total_out = usage_dict.get("output_tokens", 0)
            if result_msg.is_error and result_msg.result:
                telemetry_events.append(
                    {
                        "event_type": "session.error",
                        "payload": {"error": result_msg.result},
                    },
                )

            # Emit session.result with full usage
            telemetry_events.append(
                {
                    "event_type": "session.result",
                    "payload": {
                        "usage": usage_dict,
                        "duration_ms": sdk_duration_ms,
                        "duration_api_ms": sdk_duration_api_ms,
                        "session_id": sdk_session_id,
                        "cost_usd": cost,
                        "num_turns": turns,
                        "is_error": result_msg.is_error,
                        "result": result_msg.result,
                    },
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
                    "tool_use_count": tool_counter,
                    "mcp_call_count": mcp_counter,
                    "compact_count": compact_counter,
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
            usage=usage_dict,
            session_id=sdk_session_id,
            duration_ms=sdk_duration_ms,
            duration_api_ms=sdk_duration_api_ms,
            tool_use_count=tool_counter,
            mcp_call_count=mcp_counter,
            compact_count=compact_counter,
        )

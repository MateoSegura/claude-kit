"""SessionDriver — unified multi-turn session executor via Claude Code SDK.

Drives real Claude Code sessions using ClaudeSDKClient for multi-turn
conversations with programmatic follow-up injection. Absorbs the
message-processing and telemetry logic from SdkExecutor and adds the
multi-turn loop concept from ConversationExecutor.

This is the third executor type ("session") alongside "sdk" (single-turn
real CLI) and "api" (direct Anthropic Messages API).
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

from claude_kit.driver_config import DriverMode, SessionDriverConfig
from claude_kit.input_strategy import InputStrategy

try:
    from claude_code_sdk import ClaudeSDKClient, query
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

    try:
        from claude_code_sdk.types import ThinkingBlock
    except ImportError:
        ThinkingBlock = None  # type: ignore[assignment,misc]
except ModuleNotFoundError:  # CI: claude-code-sdk not installed
    ClaudeSDKClient = None  # type: ignore[assignment,misc]
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
_MAX_CLI_ARG = 128 * 1024


class _SkipMessage:
    """Sentinel for messages that failed to parse.

    The Claude CLI emits ``rate_limit_event`` messages which the SDK's
    ``parse_message`` does not recognise, raising ``MessageParseError``.
    By patching ``parse_message`` to return this sentinel, the async
    generator stays alive and all downstream messages are delivered.
    """


def _safe_parse_message(data: dict[str, Any]) -> Any:
    """Wrapper around the SDK's parse_message that never raises."""
    try:
        return _original_parse(data)
    except Exception:
        return _SkipMessage()


async def _stream_prompt(text: str):
    """Yield a single user message as an async iterable.

    Bypasses OS per-argument size limit for large prompts.
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": text},
    }


class SessionDriver:
    """Multi-turn session executor using ClaudeSDKClient.

    Replaces both SdkExecutor and ConversationExecutor for real Claude
    Code sessions. Uses ClaudeSDKClient.query() for programmatic
    follow-up injection during multi-turn conversations.

    Three input strategies control how follow-ups are provided:
    - TerminalInput: human types via terminal (human mode)
    - SimulatedInput: HumanSimulator + scripted follow-ups (autonomous/benchmark)
    - ScriptedInput: deterministic sequence (testing)
    """

    def __init__(
        self,
        scenario: EvalScenario,
        input_strategy: InputStrategy,
        plugins_dirs: list[Path] | None = None,
        driver_config: SessionDriverConfig | None = None,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.scenario = scenario
        self.input = input_strategy
        self._factory = SessionFactory(plugins_dirs=plugins_dirs)
        self._config = driver_config or SessionDriverConfig()
        self._on_event = on_event or (lambda _t, _p: None)
        self._pre_compact_history: list[dict[str, Any]] = []

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a single conversation for the given config.

        Args:
            config: RunConfig specifying plugins and name.

        Returns:
            RunResult with responses, metrics, telemetry, and transcript.
        """
        return asyncio.run(self._execute_async(config))

    def _build_system_prompt(
        self, config: RunConfig
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Build system prompt from plugins, returning (prompt, events)."""
        telemetry_events: list[dict[str, Any]] = []

        if config.system_prompt:
            telemetry_events.append({"event_type": "session.start"})
            return config.system_prompt, telemetry_events

        if config.plugins:
            prompt_text, captured, _ = self._factory.prepare(config.plugins)
            if prompt_text:
                telemetry_events.extend(captured)
                if not any(e.get("event_type") == "session.start" for e in captured):
                    telemetry_events.append({"event_type": "session.start"})
                return prompt_text, telemetry_events

        telemetry_events.append({"event_type": "session.start"})
        return None, telemetry_events

    def _build_options(self, system_prompt: str | None) -> ClaudeCodeOptions:
        """Build ClaudeCodeOptions from config and system prompt."""
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "max_turns": self._config.max_turns,
            "permission_mode": self._config.permission_mode,
        }

        if system_prompt and len(system_prompt) <= _MAX_CLI_ARG:
            kwargs["system_prompt"] = system_prompt

        if self._config.cwd:
            kwargs["cwd"] = self._config.cwd
        if self._config.resume:
            kwargs["resume"] = self._config.resume
        if self._config.continue_conversation:
            kwargs["continue_conversation"] = self._config.continue_conversation
        if self._config.allowed_tools:
            kwargs["allowed_tools"] = self._config.allowed_tools
        if self._config.disallowed_tools:
            kwargs["disallowed_tools"] = self._config.disallowed_tools
        if self._config.env:
            kwargs["env"] = self._config.env

        return ClaudeCodeOptions(**kwargs)

    def _process_assistant_message(
        self,
        message: Any,
        turn_number: int,
        transcript: list[Transcript],
        responses: list[str],
        telemetry_events: list[dict[str, Any]],
    ) -> tuple[int, int, int, str]:
        """Process an AssistantMessage, extracting telemetry and transcript.

        Returns (tool_count, mcp_count, turn_number, latest_text).
        """
        turn_number += 1
        tool_count = 0
        mcp_count = 0

        content_types: list[str] = []
        text_parts: list[str] = []
        turn_tool_calls: list[str] = []
        turn_mcp_calls: list[str] = []

        for block in message.content:
            if isinstance(block, TextBlock):
                content_types.append("text")
                text_parts.append(block.text)
            elif ToolUseBlock is not None and isinstance(block, ToolUseBlock):
                content_types.append("tool_use")
                tool_count += 1
                tool_name = block.name
                is_mcp = tool_name.startswith("mcp__")
                if is_mcp:
                    mcp_count += 1
                    parts = tool_name.split("__", 2)
                    server = parts[1] if len(parts) >= 2 else "unknown"
                    method = parts[2] if len(parts) == 3 else tool_name
                    turn_mcp_calls.append(tool_name)
                else:
                    server = None
                    method = None
                turn_tool_calls.append(tool_name)

                input_preview = str(block.input)[:500] if block.input else ""
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
                    {"event_type": "tool.used", "payload": tool_payload},
                )
                transcript.append(
                    Transcript(
                        role="tool_use",
                        content=input_preview,
                        tool_name=tool_name,
                        tool_use_id=block.id,
                    ),
                )
                self._on_event(
                    "tool.use",
                    {"name": tool_name, "input_preview": input_preview},
                )
            elif ToolResultBlock is not None and isinstance(block, ToolResultBlock):
                content_types.append("tool_result")
                content_preview = str(block.content)[:500] if block.content else ""
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
                self._on_event(
                    "tool.result",
                    {
                        "tool_use_id": block.tool_use_id,
                        "is_error": bool(block.is_error),
                        "preview": content_preview,
                    },
                )
            elif ThinkingBlock is not None and isinstance(block, ThinkingBlock):
                content_types.append("thinking")

        latest_text = ""
        if text_parts:
            text = "\n".join(text_parts)
            latest_text = text
            responses.append(text)
            transcript.append(
                Transcript(
                    role="assistant",
                    content=text,
                    model=getattr(message, "model", None),
                    content_types=content_types,
                ),
            )
            self._on_event(
                "assistant.text",
                {"text": text, "model": getattr(message, "model", None)},
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

        return tool_count, mcp_count, turn_number, latest_text

    def _process_system_message(
        self,
        message: Any,
        compact_counter: int,
        transcript: list[Transcript],
        telemetry_events: list[dict[str, Any]],
    ) -> int:
        """Process a SystemMessage, returning updated compact_counter."""
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
            self._on_event("session.compact", {"subtype": msg_subtype})
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
        return compact_counter

    def _build_run_result(
        self,
        config: RunConfig,
        responses: list[str],
        transcript: list[Transcript],
        telemetry_events: list[dict[str, Any]],
        result_msg: Any,
        turn_number: int,
        tool_counter: int,
        mcp_counter: int,
        compact_counter: int,
        elapsed: float,
        error: str | None = None,
    ) -> RunResult:
        """Build the final RunResult from collected data."""
        total_in = 0
        total_out = 0
        turns = turn_number
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
                    "human_responses": self.input.response_count,
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
            error=error,
            cost_usd=cost,
            usage=usage_dict,
            session_id=sdk_session_id,
            duration_ms=sdk_duration_ms,
            duration_api_ms=sdk_duration_api_ms,
            tool_use_count=tool_counter,
            mcp_call_count=mcp_counter,
            compact_count=compact_counter,
            human_response_count=self.input.response_count,
            pre_compact_snapshots=list(self._pre_compact_history),
        )

    async def _run_oneshot(
        self,
        config: RunConfig,
        options: ClaudeCodeOptions,
        system_prompt: str | None,
        telemetry_events: list[dict[str, Any]],
    ) -> RunResult:
        """Human mode: single-turn via query(), SDK handles terminal I/O.

        Same flow as SdkExecutor._execute_async — query() keeps stdin
        open for the terminal user.
        """
        self._on_event(
            "session.start",
            {"mode": self._config.mode.value, "model": self._config.model},
        )
        effective_prompt = self.scenario.prompt
        use_streaming = False

        if system_prompt and not getattr(options, "system_prompt", None):
            effective_prompt = (
                "<system-context>\n"
                + system_prompt
                + "\n</system-context>\n\n"
                + self.scenario.prompt
            )
            if len(effective_prompt) > _MAX_CLI_ARG:
                use_streaming = True

        transcript: list[Transcript] = [
            Transcript(role="user", content=self.scenario.prompt),
        ]
        responses: list[str] = []
        result_msg = None
        turn_number = 0
        tool_counter = 0
        mcp_counter = 0
        compact_counter = 0
        start = time.monotonic()

        try:
            prompt_arg = (
                _stream_prompt(effective_prompt) if use_streaming else effective_prompt
            )

            with patch(
                "claude_code_sdk._internal.client.parse_message",
                _safe_parse_message,
            ):
                async for message in query(prompt=prompt_arg, options=options):
                    if isinstance(message, _SkipMessage):
                        continue

                    if isinstance(message, AssistantMessage):
                        tc, mc, turn_number, _ = self._process_assistant_message(
                            message,
                            turn_number,
                            transcript,
                            responses,
                            telemetry_events,
                        )
                        tool_counter += tc
                        mcp_counter += mc

                    elif SystemMessage is not None and isinstance(
                        message, SystemMessage
                    ):
                        compact_counter = self._process_system_message(
                            message,
                            compact_counter,
                            transcript,
                            telemetry_events,
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

        elapsed = time.monotonic() - start

        # session.end display event for oneshot mode
        oneshot_total_in = 0
        oneshot_total_out = 0
        oneshot_cost: float | None = None
        if result_msg is not None:
            oneshot_usage = result_msg.usage or {}
            oneshot_total_in = oneshot_usage.get("input_tokens", 0)
            oneshot_total_out = oneshot_usage.get("output_tokens", 0)
            oneshot_cost = result_msg.total_cost_usd
        self._on_event(
            "session.end",
            {
                "turns": turn_number,
                "cost": oneshot_cost,
                "tokens_in": oneshot_total_in,
                "tokens_out": oneshot_total_out,
                "elapsed": elapsed,
            },
        )

        return self._build_run_result(
            config=config,
            responses=responses,
            transcript=transcript,
            telemetry_events=telemetry_events,
            result_msg=result_msg,
            turn_number=turn_number,
            tool_counter=tool_counter,
            mcp_counter=mcp_counter,
            compact_counter=compact_counter,
            elapsed=elapsed,
        )

    async def _execute_async(self, config: RunConfig) -> RunResult:
        """Async implementation — multi-turn via ClaudeSDKClient."""
        system_prompt, telemetry_events = self._build_system_prompt(config)
        options = self._build_options(system_prompt)
        self._on_event(
            "session.start",
            {"mode": self._config.mode.value, "model": self._config.model},
        )

        transcript: list[Transcript] = [
            Transcript(role="user", content=self.scenario.prompt),
        ]
        responses: list[str] = []
        result_msg = None
        turn_number = 0
        tool_counter = 0
        mcp_counter = 0
        compact_counter = 0
        start = time.monotonic()

        env_backup = os.environ.pop("CLAUDECODE", None)
        try:
            if self._config.mode == DriverMode.HUMAN:
                return await self._run_oneshot(
                    config, options, system_prompt, telemetry_events
                )

            # Non-human modes: ClaudeSDKClient for multi-turn
            # Determine initial prompt handling
            effective_prompt = self.scenario.prompt
            if system_prompt and not getattr(options, "system_prompt", None):
                effective_prompt = (
                    "<system-context>\n"
                    + system_prompt
                    + "\n</system-context>\n\n"
                    + self.scenario.prompt
                )

            client = ClaudeSDKClient(options)
            conversation_history: list[dict[str, str]] = [
                {"role": "user", "content": self.scenario.prompt},
            ]

            with patch(
                "claude_code_sdk._internal.client.parse_message",
                _safe_parse_message,
            ):
                async with client:
                    await client.query(effective_prompt)

                    for _turn_idx in range(self._config.max_turns):
                        latest_text = ""

                        async for message in client.receive_response():
                            if isinstance(message, _SkipMessage):
                                continue

                            if isinstance(message, AssistantMessage):
                                tc, mc, turn_number, lt = (
                                    self._process_assistant_message(
                                        message,
                                        turn_number,
                                        transcript,
                                        responses,
                                        telemetry_events,
                                    )
                                )
                                tool_counter += tc
                                mcp_counter += mc
                                if lt:
                                    latest_text = lt

                            elif SystemMessage is not None and isinstance(
                                message, SystemMessage
                            ):
                                compact_counter = self._process_system_message(
                                    message,
                                    compact_counter,
                                    transcript,
                                    telemetry_events,
                                )

                                # History preservation: capture pre-compact
                                if (
                                    self._config.history
                                    and "compact"
                                    in (getattr(message, "subtype", "") or "").lower()
                                ):
                                    self._pre_compact_history.append(
                                        {
                                            "compact_number": compact_counter,
                                            "timestamp": time.time(),
                                            "conversation_history": list(
                                                conversation_history
                                            ),
                                        },
                                    )

                            elif isinstance(message, ResultMessage):
                                result_msg = message
                                break

                        # Check if conversation should continue
                        if result_msg and result_msg.is_error:
                            break
                        if not latest_text:
                            break
                        if not self.input.needs_input(latest_text):
                            break

                        # Get follow-up from InputStrategy
                        conversation_history.append(
                            {"role": "assistant", "content": latest_text},
                        )
                        follow_up = self.input.get_response(
                            conversation_history,
                        )
                        if follow_up is None:
                            break

                        # Record follow-up
                        conversation_history.append(
                            {"role": "user", "content": follow_up},
                        )
                        transcript.append(
                            Transcript(role="human_sim", content=follow_up),
                        )
                        telemetry_events.append(
                            {
                                "event_type": "human.responded",
                                "payload": {
                                    "turn": turn_number,
                                    "response_count": (self.input.response_count),
                                    "response_preview": follow_up[:200],
                                },
                            },
                        )
                        self._on_event(
                            "human.response",
                            {
                                "text": follow_up,
                                "count": self.input.response_count,
                            },
                        )

                        # Inject follow-up via ClaudeSDKClient.query()
                        result_msg = None
                        await client.query(follow_up)

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

        # Compute totals for the session.end display event
        total_in = 0
        total_out = 0
        cost: float | None = None
        if result_msg is not None:
            usage_dict = result_msg.usage or {}
            total_in = usage_dict.get("input_tokens", 0)
            total_out = usage_dict.get("output_tokens", 0)
            cost = result_msg.total_cost_usd
        self._on_event(
            "session.end",
            {
                "turns": turn_number,
                "cost": cost,
                "tokens_in": total_in,
                "tokens_out": total_out,
                "elapsed": elapsed,
            },
        )

        return self._build_run_result(
            config=config,
            responses=responses,
            transcript=transcript,
            telemetry_events=telemetry_events,
            result_msg=result_msg,
            turn_number=turn_number,
            tool_counter=tool_counter,
            mcp_counter=mcp_counter,
            compact_counter=compact_counter,
            elapsed=elapsed,
        )

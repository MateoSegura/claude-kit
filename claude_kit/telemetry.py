"""Structured telemetry emitter with configurable sinks.

Events follow the claude-kit telemetry schema (v1). The emitter routes
events to zero or more sinks based on its configured level:

- off:   no output
- debug: on_emit callback only (for CLI stderr formatting)
- local: on_emit callback + JSONL file
- full:  on_emit callback + JSONL file + in-memory buffer for API upload
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_VERSION = 1
_DEFAULT_TELEMETRY_DIR = Path.home() / ".claude-kit" / "telemetry"


class TelemetryEmitter:
    """Emit structured telemetry events to JSONL files and/or an API.

    Args:
        level: Telemetry level — "off", "debug", "local", or "full".
            Invalid values are treated as "off".
        telemetry_dir: Directory for JSONL output files. Defaults to
            ``~/.claude-kit/telemetry/``. Only used when level is
            "local" or "full".
        on_emit: Optional callback invoked with the raw event dict on
            every emit. Used by the CLI to format stderr output.
    """

    def __init__(
        self,
        level: str = "off",
        telemetry_dir: Path | None = None,
        on_emit: Callable[[dict], None] | None = None,
    ) -> None:
        self.level = level if level in ("debug", "local", "full") else "off"
        self.session_id = str(uuid.uuid4())
        self._start_time = time.monotonic()
        self._on_emit = on_emit
        self._jsonl_path: Path | None = None
        self._jsonl_file = None
        self._buffer: list[dict] = []

        # Session-level counters for session.end summary
        self._plugins_loaded: list[str] = []
        self._skills: dict[str, int] = {}
        self._hooks: dict[str, int] = {}
        self._autorouter_matches = 0
        self._autorouter_misses = 0
        self._tool_uses: dict[str, int] = {}
        self._mcp_calls: dict[str, int] = {}
        self._compact_count = 0
        self._total_tokens_in = 0
        self._total_tokens_out = 0
        self._cost_usd: float | None = None
        self._model: str | None = None

        if self.level in ("local", "full"):
            tel_dir = telemetry_dir or _DEFAULT_TELEMETRY_DIR
            tel_dir.mkdir(parents=True, exist_ok=True)
            self._jsonl_path = tel_dir / f"{self.session_id}.jsonl"

    @property
    def active(self) -> bool:
        """Whether telemetry is enabled (any level other than off)."""
        return self.level != "off"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_event(self, event_type: str, payload: dict) -> dict:
        return {
            "schema_version": _SCHEMA_VERSION,
            "event_type": event_type,
            "timestamp": self._now(),
            "session_id": self.session_id,
            "payload": payload,
        }

    def _write_jsonl(self, event: dict) -> None:
        if self._jsonl_path is None:
            return
        try:
            if self._jsonl_file is None:
                self._jsonl_file = open(self._jsonl_path, "a")  # noqa: SIM115
            self._jsonl_file.write(json.dumps(event, sort_keys=True) + "\n")
            self._jsonl_file.flush()
        except OSError:
            pass  # non-fatal — telemetry must never crash the caller

    def emit(self, event_type: str, payload: dict | None = None) -> None:
        """Emit a telemetry event to all active sinks.

        Args:
            event_type: Event type string (e.g. "plugin.loaded").
            payload: Type-specific event data. Defaults to empty dict.
        """
        if self.level == "off":
            return
        event = self._build_event(event_type, payload or {})

        # Update counters for session summary
        if event_type == "plugin.loaded":
            self._plugins_loaded.append((payload or {}).get("plugin", "?"))
        elif event_type == "skill.invoked":
            skill = (payload or {}).get("skill", "?")
            self._skills[skill] = self._skills.get(skill, 0) + 1
        elif event_type == "hook.fired":
            hook_event = (payload or {}).get("hook_event", "?")
            self._hooks[hook_event] = self._hooks.get(hook_event, 0) + 1
        elif event_type == "autorouter.match":
            self._autorouter_matches += 1
        elif event_type == "autorouter.miss":
            self._autorouter_misses += 1
        elif event_type == "tool.used":
            tool = (payload or {}).get("tool_name", "?")
            self._tool_uses[tool] = self._tool_uses.get(tool, 0) + 1
            if (payload or {}).get("is_mcp"):
                server = (payload or {}).get("mcp_server", "?")
                self._mcp_calls[server] = self._mcp_calls.get(server, 0) + 1
        elif event_type == "session.compact":
            self._compact_count += 1
        elif event_type == "session.result":
            p = payload or {}
            usage = p.get("usage", {})
            self._total_tokens_in = usage.get("input_tokens", 0)
            self._total_tokens_out = usage.get("output_tokens", 0)
            self._cost_usd = p.get("cost_usd")
            self._model = p.get("model")

        # Route to sinks
        if self._on_emit is not None:
            self._on_emit(event)
        if self.level in ("local", "full"):
            self._write_jsonl(event)
        if self.level == "full":
            self._buffer.append(event)

    def emit_session_start(
        self,
        plugins: list[str],
        cli_version: str = "?",
        mode: str = "dev",
    ) -> None:
        """Emit a session.start event.

        Args:
            plugins: List of loaded plugin names.
            cli_version: CLI version string.
            mode: Execution mode ("dev" or "user").
        """
        self.emit(
            "session.start",
            {
                "plugins": plugins,
                "mode": mode,
                "telemetry_level": self.level,
                "cli_version": cli_version,
            },
        )

    def emit_session_end(self) -> None:
        """Emit a session.end event with aggregated counters."""
        duration = time.monotonic() - self._start_time
        self.emit(
            "session.end",
            {
                "duration_s": round(duration, 2),
                "plugins_loaded": len(self._plugins_loaded),
                "skills_invoked": dict(self._skills),
                "hooks_fired": dict(self._hooks),
                "autorouter_matches": self._autorouter_matches,
                "autorouter_misses": self._autorouter_misses,
                "tool_uses": dict(self._tool_uses),
                "mcp_calls": dict(self._mcp_calls),
                "compact_count": self._compact_count,
                "total_tokens_in": self._total_tokens_in,
                "total_tokens_out": self._total_tokens_out,
                "cost_usd": self._cost_usd,
                "model": self._model,
            },
        )

    def flush_buffer(self) -> list[dict]:
        """Return buffered events and clear the internal buffer.

        Returns:
            List of raw event dicts ready for API upload.
        """
        events = list(self._buffer)
        self._buffer.clear()
        return events

    def close(self) -> None:
        """Close file handles and release resources."""
        if self._jsonl_file is not None:
            try:
                self._jsonl_file.close()
            except OSError:
                pass
            self._jsonl_file = None

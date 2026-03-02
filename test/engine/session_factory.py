"""SessionFactory — wraps the claude_kit library for benchmark sessions.

Eliminates the duplication between harness/runner.py's _prepare_library_session()
and benchmark/runner.py's _build_system_prompt(). Both are replaced by this
single factory that uses PluginResolver, SessionManager, TelemetryEmitter,
and build_system_prompt from the claude_kit library.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_kit import (
    PluginResolver,
    SessionManager,
    TelemetryEmitter,
    build_system_prompt,
)


class SessionFactory:
    """Prepare benchmark sessions using the claude_kit library.

    Wraps PluginResolver + SessionManager + TelemetryEmitter into a
    single call that returns a system prompt and captured telemetry.
    """

    def __init__(
        self,
        plugins_dirs: list[Path] | None = None,
        telemetry_level: str = "debug",
    ) -> None:
        self._plugins_dirs = plugins_dirs or [
            Path(__file__).resolve().parents[2] / "plugins",
        ]
        self._telemetry_level = telemetry_level

    def prepare(
        self,
        plugin_names: list[str],
        cli_version: str = "0.0.0-bench",
    ) -> tuple[str, list[dict[str, Any]], TelemetryEmitter]:
        """Resolve plugins and build a system prompt.

        Args:
            plugin_names: Plugin directory names to load.
            cli_version: Version string for telemetry events.

        Returns:
            Tuple of (system_prompt, captured_events, telemetry_emitter).
            The emitter is returned so callers can emit additional events
            and finalize the session when done.
        """
        captured: list[dict[str, Any]] = []

        telemetry = TelemetryEmitter(
            level=self._telemetry_level,
            on_emit=captured.append,
        )

        resolver = PluginResolver(
            plugins_dirs=self._plugins_dirs,
            telemetry=telemetry,
        )
        session_mgr = SessionManager(resolver, telemetry=telemetry)
        session = session_mgr.prepare(
            kit_names=plugin_names,
            cli_version=cli_version,
        )

        prompt = build_system_prompt(session.plugins)
        session_mgr.finalize(session)

        return prompt, captured, telemetry

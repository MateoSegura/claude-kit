"""Session management — prepare, run, and finalize claude-kit sessions.

Uses only stdlib (uuid, shutil, datetime) — no third-party deps.
"""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone

from claude_kit.models import Session
from claude_kit.resolver import PluginResolver
from claude_kit.telemetry import TelemetryEmitter


class SessionManager:
    """Prepare and manage claude-kit sessions.

    Args:
        resolver: PluginResolver for expanding kit names into plugins.
        telemetry: Optional TelemetryEmitter for session lifecycle events.
    """

    def __init__(
        self,
        resolver: PluginResolver,
        telemetry: TelemetryEmitter | None = None,
    ) -> None:
        self.resolver = resolver
        self.telemetry = telemetry

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def prepare(
        self,
        kit_names: list[str],
        cli_version: str = "",
    ) -> Session:
        """Prepare a session from kit names.

        1. Expand each kit name via the resolver
        2. Build CK_* environment variables
        3. Emit session.start telemetry event
        4. Return a Session object ready for execution

        Args:
            kit_names: One or more plugin names or prefixes to load.
            cli_version: Version string for telemetry.

        Returns:
            Session with plugins, env_vars, and started_at populated.
        """
        session_id = str(uuid.uuid4())
        seen: set[str] = set()
        all_plugins = []

        for kit_name in kit_names:
            expanded = self.resolver.expand_kit(kit_name)
            for plugin in expanded:
                if plugin.name not in seen:
                    seen.add(plugin.name)
                    all_plugins.append(plugin)

        env_vars = self._build_env(session_id, all_plugins)

        session = Session(
            session_id=session_id,
            plugins=all_plugins,
            env_vars=env_vars,
            started_at=self._now(),
        )

        if self.telemetry:
            self.telemetry.emit_session_start(
                plugins=[p.name for p in all_plugins],
                cli_version=cli_version,
            )

        return session

    def finalize(self, session: Session) -> None:
        """Finalize a completed session.

        1. Emit session.end telemetry event
        2. Cleanup decrypted temp directories
        3. Set ended_at timestamp
        """
        if self.telemetry:
            self.telemetry.emit_session_end()

        for d in session.decrypted_dirs:
            try:
                shutil.rmtree(d)
            except OSError:
                pass

        session.ended_at = self._now()

    def build_env_vars(self, session: Session) -> dict[str, str]:
        """Build the CK_* environment variables for a session.

        Returns a dict suitable for os.environ.update() or subprocess.run(env=).
        """
        return self._build_env(session.session_id, session.plugins)

    @staticmethod
    def _build_env(session_id: str, plugins: list) -> dict[str, str]:
        """Build environment variable dict from session state."""
        plugin_names = ",".join(p.name for p in plugins)
        return {
            "CK_PLUGINS": plugin_names,
            "CLAUDE_KIT_SESSION_ID": session_id,
        }

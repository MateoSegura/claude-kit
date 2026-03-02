"""HooksGenerator — generate hooks.json for human mode history preservation.

Stdlib-only. Produces a temporary hooks.json file with a PreCompact
shell hook that captures the conversation state before each compaction
event. Used when running in human mode where SDK hooks are not available
(the native terminal UI requires launching `claude` CLI directly).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

_HISTORY_BASE = Path.home() / ".claude-kit" / "history"


class HooksGenerator:
    """Generate temporary hooks.json files for session history capture."""

    def generate_history_hooks(self, session_id: str) -> Path:
        """Generate a hooks.json with a PreCompact shell hook.

        Creates a temporary hooks.json file that writes pre-compact
        conversation data to the session's history directory.

        Args:
            session_id: Unique session identifier for file naming.

        Returns:
            Path to the generated temporary hooks.json file.
        """
        history_dir = _HISTORY_BASE / session_id / "compact-snapshots"
        history_dir.mkdir(parents=True, exist_ok=True)

        hooks = {
            "hooks": [
                {
                    "type": "PreCompact",
                    "command": (f"cat > {history_dir}/compact-$(date +%s).json"),
                },
            ],
        }

        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="ck-hooks-",
            delete=False,
        )
        json.dump(hooks, tmp, indent=2)
        tmp.write("\n")
        tmp.close()

        return Path(tmp.name)

    @staticmethod
    def history_dir(session_id: str) -> Path:
        """Return the history directory for a given session.

        Args:
            session_id: Session identifier.

        Returns:
            Path to ~/.claude-kit/history/<session_id>/
        """
        return _HISTORY_BASE / session_id

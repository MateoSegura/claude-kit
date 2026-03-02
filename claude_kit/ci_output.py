"""JsonlWriter — structured JSONL output for CI mode sessions.

Stdlib-only. Writes one JSON line per event to a stream (stdout or file).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, TextIO


class JsonlWriter:
    """Write structured JSONL events for CI pipelines.

    Each line is a self-contained JSON object with a timestamp, event
    type, and payload. Designed for machine consumption — no color, no
    formatting, one event per line.
    """

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        self._stream = stream

    def write_event(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Write one JSONL line.

        Args:
            event_type: Event type string (e.g. "session.start").
            payload: Optional event payload dict.
        """
        record: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
        }
        if payload:
            record.update(payload)
        self._stream.write(json.dumps(record, default=str) + "\n")
        self._stream.flush()

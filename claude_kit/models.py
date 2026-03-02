"""Data models for claude-kit plugins, sessions, and telemetry events."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Plugin:
    """A loaded claude-kit plugin."""

    name: str
    path: Path
    version: str
    role: str  # engineer | grader | tester | debugger | knowledge | system
    domain: str  # universal | embedded | backend | frontend | ...
    companions: list[str] = field(default_factory=list)


@dataclass
class Session:
    """A prepared claude-kit session ready for execution."""

    session_id: str
    plugins: list[Plugin] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    decrypted_dirs: list[Path] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""


@dataclass
class TelemetryEvent:
    """A single telemetry event emitted during a session."""

    event_type: str
    timestamp: str
    session_id: str
    payload: dict = field(default_factory=dict)
    schema_version: int = 1

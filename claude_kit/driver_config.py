"""Session driver configuration — mode enum and driver settings.

Stdlib-only. Defines DriverMode (human, autonomous, benchmark, CI) and
SessionDriverConfig (all knobs for driving a Claude Code session).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DriverMode(Enum):
    """Operating mode for the session driver."""

    HUMAN = "human"
    AUTONOMOUS = "autonomous"
    BENCHMARK = "benchmark"
    CI = "ci"


@dataclass
class SessionDriverConfig:
    """Configuration for a SessionDriver instance.

    Attributes:
        mode: Operating mode (human, autonomous, benchmark, ci).
        model: Model ID for the main conversation.
        max_turns: Maximum conversation turns before stopping.
        permission_mode: Claude Code permission mode string.
        cwd: Working directory for the Claude session.
        resume: Session ID to resume.
        continue_conversation: Whether to continue an existing session.
        history: Preserve pre-compact transcript snapshots.
        human_model: Model ID for the HumanSimulator.
        human_persona: Persona description for the HumanSimulator.
        human_max_responses: Max responses the HumanSimulator will give.
        env: Additional environment variables for the session.
        allowed_tools: Tools to allow in the session.
        disallowed_tools: Tools to disallow in the session.
    """

    mode: DriverMode = DriverMode.BENCHMARK
    model: str = "claude-sonnet-4-20250514"
    max_turns: int = 20
    permission_mode: str = "bypassPermissions"
    cwd: str | None = None
    resume: str | None = None
    continue_conversation: bool = False
    history: bool = False
    human_model: str = "claude-haiku-4-5-20251001"
    human_persona: str | None = None
    human_max_responses: int = 10
    env: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)

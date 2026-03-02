"""InputStrategy protocol — abstraction for conversation input sources.

Stdlib-only. Defines the protocol that all input strategies must implement.
Concrete implementations live in test/engine/input_strategies.py (SDK-dependent).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class InputStrategy(Protocol):
    """Protocol for providing follow-up input during multi-turn sessions.

    Implementations decide whether an assistant message requires a
    follow-up and what that follow-up should be. Three concrete
    implementations exist:

    - TerminalInput: no-op (human types directly via SDK terminal)
    - SimulatedInput: HumanSimulator + optional scripted follow-ups
    - ScriptedInput: deterministic response sequence for testing
    """

    @property
    def response_count(self) -> int:
        """Number of responses provided so far."""
        ...

    def needs_input(self, assistant_text: str) -> bool:
        """Determine whether the assistant's message requires follow-up.

        Args:
            assistant_text: The latest assistant response text.

        Returns:
            True if a follow-up response should be injected.
        """
        ...

    def get_response(self, messages: list[dict[str, str]]) -> str | None:
        """Generate a follow-up response for the conversation.

        Args:
            messages: Conversation history as role/content dicts.

        Returns:
            Response text, or None if no more responses available.
        """
        ...

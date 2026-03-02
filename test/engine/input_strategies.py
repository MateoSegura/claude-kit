"""InputStrategy implementations for multi-turn session driving.

Three concrete strategies:
- SimulatedInput: HumanSimulator + optional scripted follow-ups
- TerminalInput: No-op for human mode (SDK handles terminal I/O)
- ScriptedInput: Deterministic response sequence for testing
"""

from __future__ import annotations

from test.engine.human import HumanSimulator, NeedsInputResult


class SimulatedInput:
    """Input strategy wrapping HumanSimulator with optional scripted follow-ups.

    Scripted follow-ups are consumed first (deterministic), then falls
    back to HumanSimulator (stochastic) when auto_respond is enabled.
    """

    def __init__(
        self,
        human: HumanSimulator,
        anthropic_client: object,
        follow_ups: list[str] | None = None,
        auto_respond: bool = True,
    ) -> None:
        self._human = human
        self._client = anthropic_client
        self._follow_ups = list(follow_ups or [])
        self._follow_up_index = 0
        self._auto_respond = auto_respond

    @property
    def response_count(self) -> int:
        """Total responses: scripted follow-ups consumed + human responses."""
        return self._follow_up_index + self._human.response_count

    def needs_input(self, assistant_text: str) -> bool:
        """Check if the assistant message warrants a follow-up.

        Scripted follow-ups always proceed regardless of message content.
        After scripts are exhausted, defers to NeedsInputResult heuristic
        (only if auto_respond is True).
        """
        if self._follow_up_index < len(self._follow_ups):
            return True
        if not self._auto_respond:
            return False
        return NeedsInputResult.from_message(assistant_text).needs_input

    def get_response(self, messages: list[dict[str, str]]) -> str | None:
        """Return the next response: scripted first, then HumanSimulator.

        Returns None when all scripted follow-ups are consumed and
        HumanSimulator has reached its max_responses limit.
        """
        if self._follow_up_index < len(self._follow_ups):
            resp = self._follow_ups[self._follow_up_index]
            self._follow_up_index += 1
            return resp
        if not self._auto_respond:
            return None
        return self._human.respond(messages, self._client)


class TerminalInput:
    """No-op input strategy for human mode.

    In human mode, the SDK handles terminal I/O directly — no
    programmatic input injection is needed.
    """

    def __init__(self) -> None:
        self._count = 0

    @property
    def response_count(self) -> int:
        """Always zero — human input is handled by the SDK."""
        return self._count

    def needs_input(self, assistant_text: str) -> bool:
        """Always False — SDK handles human input natively."""
        return False

    def get_response(self, messages: list[dict[str, str]]) -> str | None:
        """Never called in human mode."""
        return None


class ScriptedInput:
    """Deterministic input strategy for testing.

    Provides a fixed sequence of responses, then stops. Does not use
    HumanSimulator or any LLM call.
    """

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0

    @property
    def response_count(self) -> int:
        """Number of scripted responses consumed so far."""
        return self._index

    def needs_input(self, assistant_text: str) -> bool:
        """True if scripted responses remain and message warrants input."""
        if self._index >= len(self._responses):
            return False
        return NeedsInputResult.from_message(assistant_text).needs_input

    def get_response(self, messages: list[dict[str, str]]) -> str | None:
        """Return the next scripted response, or None when exhausted."""
        if self._index >= len(self._responses):
            return None
        resp = self._responses[self._index]
        self._index += 1
        return resp

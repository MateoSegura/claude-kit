"""HumanSimulator — Claude-backed human stand-in for benchmarks."""

from __future__ import annotations

import re
from dataclasses import dataclass

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_RESPONSES = 10

_SYSTEM_PROMPT_TEMPLATE = """\
You are a human developer participating in a benchmark evaluation.
Your role is to act as a realistic human user interacting with an
AI coding assistant.

Guidelines:
- Respond concisely and briefly, like a busy developer would
- Exercise judgment — approve reasonable suggestions, push back
  on questionable ones
- When asked a question, give a direct answer
- When given choices, pick the most pragmatic option
- Do not over-explain or write long responses
{persona_section}"""


@dataclass
class NeedsInputResult:
    """Whether a message from Claude needs human input."""

    needs_input: bool
    reason: str

    @staticmethod
    def from_message(text: str) -> NeedsInputResult:
        """Heuristic detection of whether a message needs input."""
        stripped = text.strip()

        # Check for rhetorical patterns first
        if _is_rhetorical(stripped):
            return NeedsInputResult(
                needs_input=False,
                reason="rhetorical",
            )

        # Direct question ending with ?
        if _has_direct_question(stripped):
            return NeedsInputResult(
                needs_input=True,
                reason="direct question detected",
            )

        # Permission / confirmation patterns
        if _has_permission_request(stripped):
            return NeedsInputResult(
                needs_input=True,
                reason="permission request detected",
            )

        # Multiple choice patterns
        if _has_choice(stripped):
            return NeedsInputResult(
                needs_input=True,
                reason="choice presented",
            )

        return NeedsInputResult(needs_input=False, reason="")


def _is_rhetorical(text: str) -> bool:
    """Detect rhetorical questions followed by explanations."""
    pattern = (
        r"(?:how|what|why|where|when)\s+.*\?.*"
        r"(?:let me|I\'ll|here\'s|the \w+ (?:takes|returns|is))"
    )
    return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))


def _has_direct_question(text: str) -> bool:
    """Detect direct questions at the end of the message."""
    lines = text.strip().split("\n")
    last_line = lines[-1].strip()
    return last_line.endswith("?")


def _has_permission_request(text: str) -> bool:
    """Detect permission or confirmation requests."""
    patterns = [
        r"\bshall I\b",
        r"\bshould I\b",
        r"\bwould you like\b",
        r"\bdo you want\b",
        r"\bis that okay\b",
        r"\bcan I\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _has_choice(text: str) -> bool:
    """Detect multiple-choice style messages."""
    numbered = re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE)
    has_which = bool(re.search(r"\bwhich\b.*\bprefer\b", text, re.IGNORECASE))
    return len(numbered) >= 2 and has_which


class HumanSimulator:
    """Claude-backed human stand-in for benchmark conversations."""

    def __init__(
        self,
        *,
        persona: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_responses: int = _DEFAULT_MAX_RESPONSES,
    ) -> None:
        self.model = model
        self.max_responses = max_responses
        self.response_count = 0

        persona_section = ""
        if persona:
            persona_section = f"\nPersona: {persona}\n"

        self._system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            persona_section=persona_section,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for the human simulator."""
        return self._system_prompt

    def respond(
        self,
        messages: list[dict],
        client: object,
    ) -> str | None:
        """Generate a human response using the configured Claude model.

        Returns None if max_responses has been reached.
        """
        if self.response_count >= self.max_responses:
            return None

        msg = client.messages.create(
            model=self.model,
            system=self._system_prompt,
            max_tokens=500,
            messages=messages,
        )
        self.response_count += 1
        return msg.content[0].text

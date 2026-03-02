"""Tests for the HumanSimulator — Claude-backed human stand-in.

TDD: Ports the benchmark human tests to the engine layer.
The HumanSimulator uses a cheap Claude model (Haiku) to act
as a human developer during benchmark conversations. It decides
when Claude is asking a question vs making a statement, and
responds with judgment like a real human would.
"""

from __future__ import annotations

from test.engine.human import (
    HumanSimulator,
    NeedsInputResult,
)

# ── Construction ─────────────────────────────────────────


def test_human_simulator_importable():
    """HumanSimulator is importable."""
    assert callable(HumanSimulator)


def test_human_simulator_has_system_prompt():
    """Simulator has a system prompt explaining its role."""
    sim = HumanSimulator()
    assert sim.system_prompt
    assert "benchmark" in sim.system_prompt.lower()


def test_human_simulator_custom_persona():
    """Simulator accepts a custom persona description."""
    sim = HumanSimulator(
        persona="A senior backend engineer who prefers PostgreSQL",
    )
    assert "PostgreSQL" in sim.system_prompt


def test_human_simulator_default_model():
    """Simulator defaults to Haiku for cheapness."""
    sim = HumanSimulator()
    assert "haiku" in sim.model


def test_human_simulator_custom_model():
    """Simulator accepts a custom model."""
    sim = HumanSimulator(model="claude-sonnet-4-20250514")
    assert sim.model == "claude-sonnet-4-20250514"


# ── needs_input detection ────────────────────────────────


def test_needs_input_detects_question():
    """Direct questions should be detected as needing input."""
    result = NeedsInputResult.from_message(
        "Should I use PostgreSQL or SQLite for the database?"
    )
    assert result.needs_input is True
    assert result.reason != ""


def test_needs_input_ignores_statements():
    """Declarative statements should not need input."""
    result = NeedsInputResult.from_message(
        "I'll create the endpoint in app/routes/health.py."
    )
    assert result.needs_input is False


def test_needs_input_detects_permission_request():
    """Requests for permission should need input."""
    result = NeedsInputResult.from_message(
        "I'd like to install the requests library. Shall I add it to requirements.txt?"
    )
    assert result.needs_input is True


def test_needs_input_ignores_rhetorical():
    """Rhetorical questions should not need input."""
    result = NeedsInputResult.from_message(
        "Now, how does this work? Let me explain. "
        "The function takes a path and returns a dict."
    )
    assert result.needs_input is False


def test_needs_input_detects_choice():
    """Multiple-choice questions should need input."""
    result = NeedsInputResult.from_message(
        "I can approach this two ways:\n"
        "1. Add a new router module\n"
        "2. Extend the existing main.py\n"
        "Which approach do you prefer?"
    )
    assert result.needs_input is True


def test_needs_input_returns_dataclass():
    """Result is a proper dataclass with fields."""
    result = NeedsInputResult.from_message("Hello")
    assert hasattr(result, "needs_input")
    assert hasattr(result, "reason")
    assert isinstance(result.needs_input, bool)


# ── Conversation tracking ────────────────────────────────


def test_simulator_tracks_response_count():
    """Simulator tracks how many responses it has given."""
    sim = HumanSimulator()
    assert sim.response_count == 0


def test_simulator_max_responses():
    """Simulator has a configurable max response limit."""
    sim = HumanSimulator(max_responses=3)
    assert sim.max_responses == 3


def test_simulator_default_max_responses():
    """Default max responses is reasonable."""
    sim = HumanSimulator()
    assert sim.max_responses > 0
    assert sim.max_responses <= 20


# ── System prompt content ────────────────────────────────


def test_system_prompt_explains_role():
    """System prompt tells the LLM it's a human in a benchmark."""
    sim = HumanSimulator()
    prompt = sim.system_prompt
    assert "developer" in prompt.lower() or "human" in prompt.lower()


def test_system_prompt_includes_guidelines():
    """System prompt includes response guidelines."""
    sim = HumanSimulator()
    prompt = sim.system_prompt
    # Should mention being concise / brief
    assert "concise" in prompt.lower() or "brief" in prompt.lower()


def test_system_prompt_includes_persona():
    """Custom persona is embedded in the system prompt."""
    sim = HumanSimulator(persona="A junior dev learning Python for the first time")
    prompt = sim.system_prompt
    assert "junior" in prompt.lower()

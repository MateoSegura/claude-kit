"""Tests for InputStrategy implementations."""

from __future__ import annotations

from unittest.mock import MagicMock

from claude_kit.input_strategy import InputStrategy
from test.engine.input_strategies import ScriptedInput, SimulatedInput, TerminalInput


class TestTerminalInput:
    """TerminalInput is a no-op — SDK handles human I/O."""

    def test_implements_protocol(self) -> None:
        assert isinstance(TerminalInput(), InputStrategy)

    def test_response_count_always_zero(self) -> None:
        t = TerminalInput()
        assert t.response_count == 0

    def test_needs_input_always_false(self) -> None:
        t = TerminalInput()
        assert t.needs_input("What do you think?") is False
        assert t.needs_input("Done.") is False

    def test_get_response_always_none(self) -> None:
        t = TerminalInput()
        assert t.get_response([]) is None


class TestScriptedInput:
    """ScriptedInput provides deterministic responses in order."""

    def test_implements_protocol(self) -> None:
        assert isinstance(ScriptedInput([]), InputStrategy)

    def test_empty_responses(self) -> None:
        s = ScriptedInput([])
        assert s.response_count == 0
        assert s.needs_input("What do you prefer?") is False
        assert s.get_response([]) is None

    def test_consumes_responses_in_order(self) -> None:
        s = ScriptedInput(["first", "second", "third"])
        # needs_input only True if heuristic detects a question
        assert s.needs_input("Which one do you prefer?") is True
        assert s.get_response([]) == "first"
        assert s.response_count == 1

        assert s.needs_input("Should I proceed?") is True
        assert s.get_response([]) == "second"
        assert s.response_count == 2

        assert s.get_response([]) == "third"
        assert s.response_count == 3

    def test_exhausted_returns_none(self) -> None:
        s = ScriptedInput(["only one"])
        assert s.get_response([]) == "only one"
        assert s.get_response([]) is None
        assert s.needs_input("Another question?") is False

    def test_needs_input_checks_heuristic(self) -> None:
        s = ScriptedInput(["yes"])
        # Statement without question — heuristic says no
        assert s.needs_input("I've completed the task.") is False


class TestSimulatedInput:
    """SimulatedInput combines scripted follow-ups with HumanSimulator."""

    def _make_human(self, max_responses: int = 5) -> MagicMock:
        human = MagicMock()
        human.response_count = 0
        human.max_responses = max_responses

        def _respond(messages, client):
            if human.response_count >= human.max_responses:
                return None
            human.response_count += 1
            return f"human response {human.response_count}"

        human.respond = MagicMock(side_effect=_respond)
        return human

    def test_implements_protocol(self) -> None:
        human = self._make_human()
        s = SimulatedInput(human=human, anthropic_client=MagicMock())
        assert isinstance(s, InputStrategy)

    def test_scripted_follow_ups_first(self) -> None:
        human = self._make_human()
        s = SimulatedInput(
            human=human,
            anthropic_client=MagicMock(),
            follow_ups=["scripted 1", "scripted 2"],
        )

        # Scripted always say needs_input=True
        assert s.needs_input("anything") is True
        assert s.get_response([]) == "scripted 1"
        assert s.response_count == 1

        assert s.needs_input("anything") is True
        assert s.get_response([]) == "scripted 2"
        assert s.response_count == 2

    def test_falls_back_to_human_after_scripts(self) -> None:
        human = self._make_human()
        client = MagicMock()
        s = SimulatedInput(
            human=human,
            anthropic_client=client,
            follow_ups=["scripted"],
        )

        # Consume scripted
        assert s.get_response([]) == "scripted"

        # Now falls back to human (if heuristic triggers)
        assert s.needs_input("Should I continue?") is True
        resp = s.get_response([{"role": "assistant", "content": "Should I?"}])
        assert resp == "human response 1"

    def test_auto_respond_false_stops_after_scripts(self) -> None:
        human = self._make_human()
        s = SimulatedInput(
            human=human,
            anthropic_client=MagicMock(),
            follow_ups=["scripted"],
            auto_respond=False,
        )

        assert s.get_response([]) == "scripted"
        # After scripts exhausted and auto_respond=False, no more input
        assert s.needs_input("Should I continue?") is False
        assert s.get_response([]) is None

    def test_response_count_combines_scripted_and_human(self) -> None:
        human = self._make_human()
        s = SimulatedInput(
            human=human,
            anthropic_client=MagicMock(),
            follow_ups=["s1"],
        )

        s.get_response([])  # scripted
        assert s.response_count == 1

        # Trigger human response
        s.get_response([{"role": "assistant", "content": "Question?"}])
        # 1 scripted + 1 human
        assert s.response_count == 2

    def test_no_follow_ups_uses_human_directly(self) -> None:
        human = self._make_human()
        s = SimulatedInput(
            human=human,
            anthropic_client=MagicMock(),
        )

        assert s.needs_input("Would you like me to proceed?") is True
        resp = s.get_response([{"role": "assistant", "content": "Question?"}])
        assert resp == "human response 1"

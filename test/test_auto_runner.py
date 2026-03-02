"""Tests for auto_runner — the subprocess entry point for autonomous/CI modes.

Tests argument parsing, display callback creation, and the main() function
with mocked SessionDriver (no real API calls).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

from claude_kit.driver_config import DriverMode

# --- Mock SDK types (same pattern as test_session_driver.py) ---


@dataclass
class MockTextBlock:
    text: str
    type: str = "text"


@dataclass
class MockToolUseBlock:
    name: str
    id: str
    input: dict[str, Any] = field(default_factory=dict)
    type: str = "tool_use"


@dataclass
class MockToolResultBlock:
    tool_use_id: str
    content: str = ""
    is_error: bool = False
    type: str = "tool_result"


@dataclass
class MockAssistantMessage:
    content: list[Any] = field(default_factory=list)
    model: str = "claude-sonnet-4-20250514"


@dataclass
class MockSystemMessage:
    subtype: str = ""
    data: Any = None


@dataclass
class MockResultMessage:
    num_turns: int = 1
    total_cost_usd: float = 0.01
    usage: dict[str, int] | None = None
    session_id: str = "test-session"
    duration_ms: int = 1000
    duration_api_ms: int = 800
    is_error: bool = False
    result: str = ""


def _make_patched_modules():
    """Create a dict of patches for SDK modules used by driver.py."""
    return {
        "ClaudeSDKClient": MagicMock,
        "query": MagicMock,
        "_original_parse": MagicMock(),
        "AssistantMessage": MockAssistantMessage,
        "SystemMessage": MockSystemMessage,
        "ResultMessage": MockResultMessage,
        "TextBlock": MockTextBlock,
        "ToolUseBlock": MockToolUseBlock,
        "ToolResultBlock": MockToolResultBlock,
        "ThinkingBlock": None,
        "ClaudeCodeOptions": MagicMock,
    }


class TestParseArgs:
    """Test argument parsing for auto_runner."""

    def test_required_prompt(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "hello world"])
            assert args.prompt == "hello world"

    def test_mode_defaults_autonomous(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "test"])
            assert args.mode == "autonomous"

    def test_ci_mode(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "test", "--mode", "ci"])
            assert args.mode == "ci"

    def test_model_override(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(
                ["--prompt", "test", "--model", "claude-haiku-4-5-20251001"]
            )
            assert args.model == "claude-haiku-4-5-20251001"

    def test_plugin_dirs(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(
                [
                    "--prompt",
                    "test",
                    "--plugin-dir",
                    "/a",
                    "--plugin-dir",
                    "/b",
                ]
            )
            assert args.plugin_dirs == ["/a", "/b"]

    def test_max_turns(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "test", "--max-turns", "30"])
            assert args.max_turns == 30

    def test_history_flag(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "test", "--history"])
            assert args.history is True

    def test_human_persona(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _parse_args

            args = _parse_args(["--prompt", "test", "--human-persona", "Senior dev"])
            assert args.human_persona == "Senior dev"


class TestDisplayCallback:
    """Test display callback creation for autonomous and CI modes."""

    def test_autonomous_returns_renderer(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _make_display_callback

            display, cb = _make_display_callback("autonomous")
            assert display is not None
            assert callable(cb)

    def test_ci_returns_writer(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _make_display_callback

            display, cb = _make_display_callback("ci")
            assert display is not None
            assert callable(cb)

    def test_ci_callback_writes_jsonl(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from io import StringIO

            from claude_kit.ci_output import JsonlWriter
            from test.engine.auto_runner import _make_display_callback

            stream = StringIO()
            orig_init = JsonlWriter.__init__

            def patched_init(self_inner, s=stream):
                orig_init(self_inner, stream=s)

            with patch.object(JsonlWriter, "__init__", patched_init):
                display, cb = _make_display_callback("ci")
            cb("assistant.text", {"text": "hello"})

            output = stream.getvalue()
            assert output, "expected JSONL output"
            assert '"type": "assistant.text"' in output

    def test_autonomous_callback_handles_events(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import _make_display_callback

            _display, cb = _make_display_callback("autonomous")
            # Should not raise for any event type
            cb("assistant.text", {"text": "hello", "model": "test"})
            cb("tool.use", {"name": "Bash", "input_preview": "ls"})
            cb("tool.result", {"tool_use_id": "t1", "is_error": False, "preview": "ok"})
            cb("human.response", {"text": "yes", "count": 1})
            cb("session.compact", {"subtype": "auto_compact"})
            cb(
                "session.end",
                {
                    "turns": 3,
                    "cost": 0.05,
                    "tokens_in": 1000,
                    "tokens_out": 500,
                    "elapsed": 5.0,
                },
            )


class TestMainFunction:
    """Test the main() function with mocked SessionDriver."""

    def test_main_autonomous_mode(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import main
            from test.engine.config import RunResult

            mock_result = RunResult(
                config_name="session",
                responses=["hello"],
                turns=1,
                total_tokens_in=100,
                total_tokens_out=50,
                wall_clock_s=1.0,
            )

            with patch("test.engine.auto_runner.SessionDriver") as mock_driver_cls:
                mock_driver = MagicMock()
                mock_driver.execute.return_value = mock_result
                mock_driver_cls.return_value = mock_driver

                exit_code = main(["--prompt", "Hello world"])
                assert exit_code == 0
                mock_driver.execute.assert_called_once()

    def test_main_ci_mode_outputs_json(self, capsys) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            import json

            from test.engine.auto_runner import main
            from test.engine.config import RunResult

            mock_result = RunResult(
                config_name="session",
                responses=["hello"],
                turns=2,
                total_tokens_in=200,
                total_tokens_out=100,
                wall_clock_s=2.5,
                cost_usd=0.05,
                tool_use_count=3,
                mcp_call_count=1,
                compact_count=0,
                human_response_count=1,
            )

            with patch("test.engine.auto_runner.SessionDriver") as mock_driver_cls:
                mock_driver = MagicMock()
                mock_driver.execute.return_value = mock_result
                mock_driver_cls.return_value = mock_driver

                exit_code = main(["--prompt", "Test prompt", "--mode", "ci"])
                assert exit_code == 0

                captured = capsys.readouterr()
                data = json.loads(captured.out)
                assert data["turns"] == 2
                assert data["cost_usd"] == 0.05
                assert data["human_response_count"] == 1

    def test_main_returns_1_on_error(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import main
            from test.engine.config import RunResult

            mock_result = RunResult(
                config_name="session",
                responses=[],
                turns=0,
                total_tokens_in=0,
                total_tokens_out=0,
                wall_clock_s=0.1,
                error="SDK error: connection failed",
            )

            with patch("test.engine.auto_runner.SessionDriver") as mock_driver_cls:
                mock_driver = MagicMock()
                mock_driver.execute.return_value = mock_result
                mock_driver_cls.return_value = mock_driver

                exit_code = main(["--prompt", "Fail test"])
                assert exit_code == 1

    def test_main_handles_exception(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import main

            with patch("test.engine.auto_runner.SessionDriver") as mock_driver_cls:
                mock_driver = MagicMock()
                mock_driver.execute.side_effect = RuntimeError("boom")
                mock_driver_cls.return_value = mock_driver

                exit_code = main(["--prompt", "Crash test"])
                assert exit_code == 1

    def test_main_builds_correct_driver_config(self) -> None:
        with patch.multiple("test.engine.driver", **_make_patched_modules()):
            from test.engine.auto_runner import main
            from test.engine.config import RunResult

            mock_result = RunResult(
                config_name="session",
                responses=["ok"],
                turns=1,
                total_tokens_in=50,
                total_tokens_out=25,
                wall_clock_s=0.5,
            )

            with patch("test.engine.auto_runner.SessionDriver") as mock_driver_cls:
                mock_driver = MagicMock()
                mock_driver.execute.return_value = mock_result
                mock_driver_cls.return_value = mock_driver

                main(
                    [
                        "--prompt",
                        "Test",
                        "--mode",
                        "ci",
                        "--model",
                        "claude-haiku-4-5-20251001",
                        "--max-turns",
                        "5",
                        "--history",
                        "--human-persona",
                        "QA engineer",
                    ]
                )

                # Verify the driver was created with correct config
                call_kwargs = mock_driver_cls.call_args
                config = call_kwargs.kwargs.get("driver_config") or call_kwargs[1].get(
                    "driver_config"
                )
                assert config.mode == DriverMode.CI
                assert config.model == "claude-haiku-4-5-20251001"
                assert config.max_turns == 5
                assert config.history is True
                assert config.human_persona == "QA engineer"

"""TerminalRenderer — ANSI-based display for autonomous mode sessions.

Stdlib-only. Uses ANSI escape codes directly for colored output.
Does NOT replicate the Claude Code ink/React TUI — this is a simpler
streaming text renderer for autonomous and benchmark modes.
"""

from __future__ import annotations

import sys
from typing import TextIO

# ANSI escape sequences
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"


class TerminalRenderer:
    """Streaming text renderer for autonomous Claude Code sessions.

    Renders assistant text, tool use/results, human simulator responses,
    compaction events, and session summaries to a terminal stream using
    ANSI colors.

    Attributes:
        stream: Output stream (defaults to stdout).
        color: Whether to use ANSI color codes.
        show_tools: Whether to display tool use/result lines.
        show_thinking: Whether to display thinking blocks.
    """

    def __init__(
        self,
        stream: TextIO = sys.stdout,
        color: bool = True,
        show_tools: bool = False,
        show_thinking: bool = False,
    ) -> None:
        self._stream = stream
        self._color = color
        self.show_tools = show_tools
        self.show_thinking = show_thinking

    def _c(self, code: str, text: str) -> str:
        """Wrap text in ANSI code if color is enabled."""
        if not self._color:
            return text
        return f"{code}{text}{_RESET}"

    def _write(self, text: str) -> None:
        """Write text to the stream and flush."""
        self._stream.write(text)
        self._stream.flush()

    def render_header(
        self,
        mode: str,
        plugins: list[str] | None = None,
    ) -> None:
        """Render session header with mode and plugin info."""
        parts = [self._c(_BOLD, "claude-kit")]
        parts.append(self._c(_DIM, mode))
        if plugins:
            parts.append(self._c(_CYAN, ", ".join(plugins)))
        self._write("  ".join(parts) + "\n")
        self._write(
            self._c(_DIM, "\u2500" * 50) + "\n\n",
        )

    def render_assistant_text(
        self,
        text: str,
        model: str | None = None,
    ) -> None:
        """Render assistant text with 'Claude' prefix."""
        prefix = self._c(f"{_BOLD}{_CYAN}", " Claude")
        self._write(f"\n{prefix}  {text}\n")

    def render_tool_use(
        self,
        name: str,
        input_preview: str,
    ) -> None:
        """Render a tool use line."""
        if not self.show_tools:
            return
        label = self._c(_MAGENTA, f" [tool] {name}:")
        preview = input_preview[:80] if input_preview else ""
        self._write(f"{label} {preview}\n")

    def render_tool_result(
        self,
        tool_use_id: str,
        is_error: bool,
        preview: str,
    ) -> None:
        """Render a tool result line."""
        if not self.show_tools:
            return
        if is_error:
            label = self._c(_RED, " [error]")
        else:
            label = self._c(_DIM, " [result]")
        text = preview[:120] if preview else ""
        self._write(f"{label} {text}\n")

    def render_human_response(self, text: str) -> None:
        """Render a human simulator auto-reply."""
        label = self._c(f"{_DIM}{_YELLOW}", " [auto-reply]")
        self._write(f"\n{label} {text}\n")

    def render_compact(
        self,
        tokens_before: int | None = None,
    ) -> None:
        """Render a compaction separator line."""
        line = self._c(_DIM, "\u2500\u2500")
        info = " compact "
        if tokens_before is not None:
            k = tokens_before // 1000
            info = f" compact ({k}K tokens) "
        self._write(
            f"\n {line}{self._c(_DIM, info)}{line}\n\n",
        )

    def render_session_end(
        self,
        turns: int,
        cost: float | None,
        tokens_in: int,
        tokens_out: int,
        elapsed: float,
    ) -> None:
        """Render session summary line."""
        self._write(
            "\n" + self._c(_DIM, " \u2500\u2500 session complete \u2500\u2500") + "\n",
        )

        parts = [f"Turns: {turns}"]
        if cost is not None:
            parts.append(f"Cost: ${cost:.2f}")

        in_k = tokens_in // 1000
        out_k = tokens_out // 1000
        parts.append(f"Tokens: {in_k}K in / {out_k}K out")

        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        if minutes > 0:
            parts.append(f"Time: {minutes}m {seconds}s")
        else:
            parts.append(f"Time: {seconds}s")

        summary = self._c(
            _DIM,
            " " + "  \u00b7  ".join(parts),
        )
        self._write(summary + "\n")

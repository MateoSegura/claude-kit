"""TmuxBenchmarkOrchestrator — side-by-side benchmark visualization.

Stdlib-only (shells out to tmux binary). Launches two panes running
kit vs raw configs simultaneously with TerminalRenderer streaming.
Falls back to sequential execution if tmux is not available.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

_POLL_INTERVAL = 2.0  # seconds between result file checks
_POLL_TIMEOUT = 600.0  # 10 minute max wait


class TmuxBenchmarkOrchestrator:
    """Orchestrate side-by-side benchmark comparison in tmux panes.

    Layout:
    +----------------------------------+----------------------------------+
    |          RAW (no plugins)        |       KIT (with plugins)         |
    +----------------------------------+----------------------------------+

    Each pane runs a driver script that writes RunResult JSON to a temp
    file. The orchestrator monitors both files and collects results.

    Falls back to sequential execution if tmux is not available.

    Attributes:
        scenario_path: Path to the YAML scenario file.
        plugins_dir: Directory containing plugins.
    """

    def __init__(
        self,
        scenario_path: Path,
        plugins_dir: Path,
        model: str | None = None,
    ) -> None:
        self.scenario_path = scenario_path
        self.plugins_dir = plugins_dir
        self._model = model
        self._session_name = f"ck-bench-{int(time.time())}"
        self._tmux_available = shutil.which("tmux") is not None

    def run(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Run the benchmark comparison.

        Returns:
            Tuple of (raw_result_dict, kit_result_dict) loaded from
            the JSON files written by each pane's driver process.
        """
        if not self._tmux_available:
            return self._run_sequential()
        return self._run_tmux()

    def _run_tmux(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Launch both configs in tmux panes."""
        raw_file = Path(
            tempfile.mktemp(
                suffix=".json",
                prefix=f"{self._session_name}-raw-",
            ),
        )
        kit_file = Path(
            tempfile.mktemp(
                suffix=".json",
                prefix=f"{self._session_name}-kit-",
            ),
        )

        try:
            self._create_session(raw_file, kit_file)
            return self._collect_results(raw_file, kit_file)
        finally:
            self._cleanup_session()
            raw_file.unlink(missing_ok=True)
            kit_file.unlink(missing_ok=True)

    def _create_session(
        self,
        raw_file: Path,
        kit_file: Path,
    ) -> None:
        """Create tmux session with two horizontal panes."""
        model_arg = f" --model {self._model}" if self._model else ""

        raw_cmd = (
            f"python -m test.benchmark {self.scenario_path}"
            f" --executor session --plugins-dir {self.plugins_dir}"
            f"{model_arg}"
            f" --output {raw_file.parent}"
            f"; echo '{{\"done\": true}}' > {raw_file}"
        )
        kit_cmd = (
            f"python -m test.benchmark {self.scenario_path}"
            f" --executor session --plugins-dir {self.plugins_dir}"
            f"{model_arg}"
            f" --output {kit_file.parent}"
            f"; echo '{{\"done\": true}}' > {kit_file}"
        )

        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                self._session_name,
                "-x",
                "200",
                "-y",
                "50",
                raw_cmd,
            ],
            check=True,
        )

        subprocess.run(
            [
                "tmux",
                "split-window",
                "-h",
                "-t",
                self._session_name,
                kit_cmd,
            ],
            check=True,
        )

        # Attach for visual display
        subprocess.run(
            ["tmux", "attach-session", "-t", self._session_name],
            check=False,
        )

    def _collect_results(
        self,
        raw_file: Path,
        kit_file: Path,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Poll temp files until both results are available."""
        start = time.monotonic()

        while time.monotonic() - start < _POLL_TIMEOUT:
            raw_done = raw_file.exists()
            kit_done = kit_file.exists()

            if raw_done and kit_done:
                raw_data = json.loads(raw_file.read_text())
                kit_data = json.loads(kit_file.read_text())
                return raw_data, kit_data

            time.sleep(_POLL_INTERVAL)

        return {"error": "timeout"}, {"error": "timeout"}

    def _cleanup_session(self) -> None:
        """Kill the tmux session if it exists."""
        subprocess.run(
            [
                "tmux",
                "kill-session",
                "-t",
                self._session_name,
            ],
            check=False,
            capture_output=True,
        )

    def _run_sequential(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Fallback: run configs sequentially without tmux."""
        model_arg = []
        if self._model:
            model_arg = ["--model", self._model]

        results: list[dict[str, Any]] = []
        for _label in ["raw", "kit"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    "python",
                    "-m",
                    "test.benchmark",
                    str(self.scenario_path),
                    "--executor",
                    "session",
                    "--plugins-dir",
                    str(self.plugins_dir),
                    "--output",
                    tmpdir,
                    *model_arg,
                ]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                )
                if proc.returncode != 0:
                    results.append(
                        {
                            "error": proc.stderr[:500],
                        },
                    )
                else:
                    # Find JSON output in tmpdir
                    json_files = list(Path(tmpdir).glob("*.json"))
                    if json_files:
                        data = json.loads(
                            json_files[0].read_text(),
                        )
                        results.append(data)
                    else:
                        results.append({"stdout": proc.stdout[:500]})

        raw = results[0] if results else {"error": "no results"}
        kit = results[1] if len(results) > 1 else {"error": "no results"}
        return raw, kit

"""Version detection for claude-kit installations.

Uses only stdlib (pathlib, subprocess) — no third-party deps.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class VersionManager:
    """Determine current and remote versions of claude-kit.

    Args:
        install_dir: Root directory of the claude-kit installation.
    """

    def __init__(self, install_dir: Path) -> None:
        self.install_dir = install_dir

    def _git(self, args: list[str]) -> str:
        """Run a git command in install_dir, return stripped stdout or empty string."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.install_dir)] + args,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        return ""

    def current_version(self) -> str:
        """Return the version of the local claude-kit installation.

        Resolution order:
        1. .version file (user installs without .git)
        2. Exact tag at HEAD (dev mode)
        3. Latest versioned entry in CHANGELOG.md
        4. Nearest ancestor tag via git describe (dev fallback)
        5. "unknown"
        """
        ver_file = self.install_dir / ".version"
        if ver_file.exists():
            ver = ver_file.read_text().strip()
            if ver:
                return ver

        tag = self._git(["tag", "--points-at", "HEAD", "--sort=-version:refname"])
        if tag:
            return tag.splitlines()[0]

        cl_version = self.changelog_version()
        if cl_version:
            return "v" + cl_version

        desc = self._git(["describe", "--tags", "--abbrev=0"])
        if desc:
            return desc

        short = self._git(["rev-parse", "--short", "HEAD"])
        if short:
            return short

        return "unknown"

    def remote_version(self) -> str | None:
        """Fetch the latest version from origin/main.

        Returns None if git is not available or fetch fails.
        """
        tag = self._git(
            ["tag", "--points-at", "origin/main", "--sort=-version:refname"]
        )
        if tag:
            return tag.splitlines()[0]
        tag = self._git(["tag", "--sort=-version:refname", "--list", "v*"])
        if tag:
            return tag.splitlines()[0]
        short = self._git(["rev-parse", "--short", "origin/main"])
        return short or None

    def changelog_version(self, path: Path | None = None) -> str | None:
        """Parse CHANGELOG.md for the most recent versioned entry.

        Args:
            path: Path to CHANGELOG.md. Defaults to install_dir/CHANGELOG.md.

        Returns:
            Version string (without 'v' prefix) or None if no entries found.
        """
        cl = path or (self.install_dir / "CHANGELOG.md")
        if not cl.exists():
            return None
        try:
            for line in cl.read_text().splitlines():
                if line.startswith("## [") and "Unreleased" not in line:
                    return line.split("]")[0].replace("## [", "").strip()
        except OSError:
            pass
        return None

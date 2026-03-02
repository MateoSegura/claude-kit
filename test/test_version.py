"""Tests for claude_kit.version — VersionManager contracts.

TDD: These tests define the expected behavior of the VersionManager
before implementation. Uses tmp_path fixtures.
"""

from __future__ import annotations

from pathlib import Path

# ── Import & Construction ────────────────────────────────────────────────


def test_version_manager_importable():
    from claude_kit.version import VersionManager  # noqa: F401


def test_version_manager_exported_from_package():
    from claude_kit import VersionManager  # noqa: F401


def test_version_manager_stores_install_dir(tmp_path: Path):
    from claude_kit.version import VersionManager

    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.install_dir == tmp_path


# ── current_version() ────────────────────────────────────────────────────


def test_current_version_from_version_file(tmp_path: Path):
    from claude_kit.version import VersionManager

    (tmp_path / ".version").write_text("0.12.0\n")
    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.current_version() == "0.12.0"


def test_current_version_strips_whitespace(tmp_path: Path):
    from claude_kit.version import VersionManager

    (tmp_path / ".version").write_text("  v0.13.0  \n")
    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.current_version() == "v0.13.0"


def test_current_version_empty_file_falls_through(tmp_path: Path):
    from claude_kit.version import VersionManager

    (tmp_path / ".version").write_text("\n")
    mgr = VersionManager(install_dir=tmp_path)
    # With no .version content and no git, should return "unknown"
    assert mgr.current_version() == "unknown"


def test_current_version_no_version_file(tmp_path: Path):
    from claude_kit.version import VersionManager

    mgr = VersionManager(install_dir=tmp_path)
    # No .version file and no git — returns "unknown"
    assert mgr.current_version() == "unknown"


# ── changelog_version() ──────────────────────────────────────────────────


def test_changelog_version_parses_entry(tmp_path: Path):
    from claude_kit.version import VersionManager

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        "## [0.14.0] - 2026-03-01\n\n"
        "- Added telemetry\n\n"
        "## [0.13.0] - 2026-02-15\n\n"
        "- Previous release\n"
    )
    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.changelog_version(changelog) == "0.14.0"


def test_changelog_version_skips_unreleased(tmp_path: Path):
    from claude_kit.version import VersionManager

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [Unreleased]\n\n## [0.12.0] - 2026-02-01\n")
    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.changelog_version(changelog) == "0.12.0"


def test_changelog_version_none_when_no_entries(tmp_path: Path):
    from claude_kit.version import VersionManager

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [Unreleased]\n\nNothing yet.\n")
    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.changelog_version(changelog) is None


def test_changelog_version_none_when_missing(tmp_path: Path):
    from claude_kit.version import VersionManager

    mgr = VersionManager(install_dir=tmp_path)
    assert mgr.changelog_version(tmp_path / "nonexistent.md") is None


def test_changelog_version_default_path(tmp_path: Path):
    from claude_kit.version import VersionManager

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [0.10.0] - 2026-01-01\n")
    mgr = VersionManager(install_dir=tmp_path)
    # When no path is passed, should look in install_dir
    assert mgr.changelog_version() == "0.10.0"

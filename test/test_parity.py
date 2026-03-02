"""Parity enforcement — verify CLI does not reimplement library logic.

TDD: These tests define the boundary contract between the claude-kit CLI
and the claude_kit library. They fail if the CLI reimplements classes or
functions that should be imported from the library.

Phase 1 starts with basic checks (importability, no runtime deps).
Later phases will expand LIBRARY_CLASSES and EXTRACTED_FUNCTIONS as
more code is moved from CLI to library.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

# Classes that MUST live in the library, not the CLI.
# Updated as each phase extracts more logic.
LIBRARY_CLASSES: set[str] = {
    # Phase 2 will add: "TelemetryEmitter", "APIClient"
    # Phase 3 will add: "PluginResolver"
    # Phase 4 will add: "SessionManager"
    # Phase 5 will add: "PluginDecryptor", "TempDirManager", "VersionManager"
}

# Functions that MUST live in the library, not the CLI.
EXTRACTED_FUNCTIONS: set[str] = {
    # Phase 3 will add: "find_plugin_dir", "expand_kit", etc.
    # Phase 5 will add: "_is_encrypted", "_decrypt_plugin", etc.
}

CLI_PATH = Path(__file__).parent.parent / "claude-kit"


def test_library_is_importable():
    """The claude_kit package must be importable with core exports."""
    claude_kit = importlib.import_module("claude_kit")
    assert hasattr(claude_kit, "__version__")
    assert hasattr(claude_kit, "Plugin")
    assert hasattr(claude_kit, "Session")
    assert hasattr(claude_kit, "TelemetryEvent")


def test_library_version_is_string():
    from claude_kit import __version__

    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) == 3, f"Version should be semver: {__version__}"


def test_library_has_no_runtime_deps():
    """The root pyproject.toml must declare zero runtime dependencies."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found at repo root"
    content = pyproject.read_text()

    in_deps = False
    dep_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "dependencies = []":
            return  # Perfect — empty deps
        if stripped.startswith("dependencies = ["):
            in_deps = True
            if stripped.endswith("[]"):
                return
            continue
        if in_deps:
            if stripped == "]":
                break
            dep_lines.append(stripped)

    assert not dep_lines, (
        f"pyproject.toml has runtime dependencies — "
        f"claude_kit must be stdlib-only: {dep_lines}"
    )


def test_cli_does_not_duplicate_library_classes():
    """CLI must not define classes that belong in the library."""
    if not LIBRARY_CLASSES:
        return  # No classes to check yet (Phase 1)

    tree = ast.parse(CLI_PATH.read_text())
    cli_classes = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    duplicates = LIBRARY_CLASSES & cli_classes
    assert not duplicates, (
        f"CLI defines classes that should be imported from claude_kit: {duplicates}"
    )


def test_cli_does_not_duplicate_extracted_functions():
    """CLI must not define functions that were extracted to the library."""
    if not EXTRACTED_FUNCTIONS:
        return  # No functions to check yet (Phase 1)

    tree = ast.parse(CLI_PATH.read_text())
    cli_functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    duplicates = EXTRACTED_FUNCTIONS & cli_functions
    assert not duplicates, (
        f"CLI contains functions that should be in claude_kit: {duplicates}"
    )


def test_exceptions_importable():
    """Exception classes must be importable from claude_kit.exceptions."""
    from claude_kit.exceptions import (  # noqa: F401
        APIUploadError,
        ClaudeKitError,
        DecryptionError,
        PluginNotFoundError,
    )

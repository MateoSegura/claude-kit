"""Tests for claude_kit.exceptions — exception hierarchy contracts.

TDD: These tests define the expected exception classes and their
inheritance relationships before implementation.
"""

from __future__ import annotations


def test_base_exception_exists():
    from claude_kit.exceptions import ClaudeKitError

    assert issubclass(ClaudeKitError, Exception)


def test_plugin_not_found_error():
    from claude_kit.exceptions import ClaudeKitError, PluginNotFoundError

    assert issubclass(PluginNotFoundError, ClaudeKitError)
    err = PluginNotFoundError("no-such-plugin")
    assert "no-such-plugin" in str(err)


def test_decryption_error():
    from claude_kit.exceptions import ClaudeKitError, DecryptionError

    assert issubclass(DecryptionError, ClaudeKitError)
    err = DecryptionError("bad key")
    assert "bad key" in str(err)


def test_api_upload_error():
    from claude_kit.exceptions import APIUploadError, ClaudeKitError

    assert issubclass(APIUploadError, ClaudeKitError)
    err = APIUploadError("timeout")
    assert "timeout" in str(err)


def test_exceptions_are_catchable_as_base():
    """All claude-kit exceptions should be catchable via ClaudeKitError."""
    from claude_kit.exceptions import (
        APIUploadError,
        ClaudeKitError,
        DecryptionError,
        PluginNotFoundError,
    )

    for exc_class in (PluginNotFoundError, DecryptionError, APIUploadError):
        try:
            raise exc_class("test")
        except ClaudeKitError:
            pass  # Expected — all are subtypes of ClaudeKitError

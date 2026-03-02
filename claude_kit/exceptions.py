"""Exception hierarchy for the claude-kit library."""

from __future__ import annotations


class ClaudeKitError(Exception):
    """Base exception for claude-kit library."""


class PluginNotFoundError(ClaudeKitError):
    """Raised when a requested plugin cannot be found."""


class DecryptionError(ClaudeKitError):
    """Raised when plugin decryption fails."""


class APIUploadError(ClaudeKitError):
    """Raised when telemetry upload to the API fails."""

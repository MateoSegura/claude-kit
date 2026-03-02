"""claude-kit: Plugin management and telemetry library for Claude Code."""

from __future__ import annotations

from claude_kit.api_client import APIClient
from claude_kit.encryption import PluginDecryptor, TempDirManager
from claude_kit.models import Plugin, Session, TelemetryEvent
from claude_kit.resolver import PluginResolver
from claude_kit.session import SessionManager
from claude_kit.telemetry import TelemetryEmitter
from claude_kit.version import VersionManager

__version__ = "0.14.0"
__all__ = [
    "APIClient",
    "Plugin",
    "PluginDecryptor",
    "PluginResolver",
    "Session",
    "SessionManager",
    "TelemetryEmitter",
    "TelemetryEvent",
    "TempDirManager",
    "VersionManager",
]

"""claude-kit: Plugin management and telemetry library for Claude Code."""

from __future__ import annotations

from claude_kit.api_client import APIClient
from claude_kit.benchmark_tmux import TmuxBenchmarkOrchestrator
from claude_kit.ci_output import JsonlWriter
from claude_kit.driver_config import DriverMode, SessionDriverConfig
from claude_kit.encryption import PluginDecryptor, TempDirManager
from claude_kit.hooks_generator import HooksGenerator
from claude_kit.input_strategy import InputStrategy
from claude_kit.models import Plugin, Session, TelemetryEvent
from claude_kit.prompt import build_system_prompt
from claude_kit.renderer import TerminalRenderer
from claude_kit.resolver import PluginResolver
from claude_kit.session import SessionManager
from claude_kit.telemetry import TelemetryEmitter
from claude_kit.version import VersionManager

__version__ = "0.14.0"
__all__ = [
    "APIClient",
    "DriverMode",
    "HooksGenerator",
    "InputStrategy",
    "JsonlWriter",
    "Plugin",
    "PluginDecryptor",
    "PluginResolver",
    "Session",
    "SessionDriverConfig",
    "SessionManager",
    "TelemetryEmitter",
    "TelemetryEvent",
    "TempDirManager",
    "TerminalRenderer",
    "TmuxBenchmarkOrchestrator",
    "VersionManager",
    "build_system_prompt",
]

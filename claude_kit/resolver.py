"""Plugin resolution — find, expand, and deduplicate plugin trees.

Uses only stdlib (json, pathlib) — no third-party deps.
"""

from __future__ import annotations

import json
from pathlib import Path

from claude_kit.exceptions import PluginNotFoundError
from claude_kit.models import Plugin
from claude_kit.telemetry import TelemetryEmitter


class PluginResolver:
    """Resolve claude-kit plugin names to loaded Plugin objects.

    Args:
        plugins_dirs: Ordered list of directories to search for plugins.
            First match wins. Typically [PLUGINS_DIR, LOCAL_DIR].
        telemetry: Optional emitter — emits plugin.loaded events during
            expand_kit().
    """

    def __init__(
        self,
        plugins_dirs: list[Path],
        telemetry: TelemetryEmitter | None = None,
    ) -> None:
        self.plugins_dirs = plugins_dirs
        self.telemetry = telemetry

    @staticmethod
    def _read_plugin_json(plugin_dir: Path) -> dict:
        """Read plugin.json from a plugin directory."""
        pjson = plugin_dir / ".claude-plugin" / "plugin.json"
        if not pjson.exists():
            return {}
        try:
            return json.loads(pjson.read_text())
        except Exception:
            return {}

    @staticmethod
    def _read_ctl(plugin_dir: Path) -> dict:
        """Read ctl.json from a plugin directory."""
        ctl = plugin_dir / ".claude-plugin" / "ctl.json"
        if not ctl.exists():
            return {}
        try:
            return json.loads(ctl.read_text())
        except Exception:
            return {}

    def _build_plugin(self, name: str, plugin_dir: Path) -> Plugin:
        """Build a Plugin dataclass from a plugin directory."""
        pjson = self._read_plugin_json(plugin_dir)
        ctl = self._read_ctl(plugin_dir)
        return Plugin(
            name=pjson.get("name", name),
            path=plugin_dir,
            version=pjson.get("version", "?"),
            role=ctl.get("role", ""),
            domain=ctl.get("domain", ""),
            companions=ctl.get("companions", []),
        )

    def find(self, name: str) -> Plugin:
        """Find a plugin by exact name. Raises PluginNotFoundError."""
        for base in self.plugins_dirs:
            d = base / name
            if d.is_dir():
                return self._build_plugin(name, d)
        raise PluginNotFoundError(f"Plugin '{name}' not found")

    def resolve_prefix(self, prefix: str) -> list[str]:
        """Expand a prefix (e.g., 'embedded-zephyr') to all matching names."""
        results: list[str] = []
        seen: set[str] = set()
        for base in self.plugins_dirs:
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                if d.is_dir() and d.name.startswith(prefix + "-"):
                    if d.name not in seen:
                        seen.add(d.name)
                        results.append(d.name)
        return results

    def resolve_companions(self, plugin: Plugin) -> list[Plugin]:
        """Resolve companion plugins declared in ctl.json."""
        companions: list[Plugin] = []
        for comp_name in plugin.companions:
            try:
                companions.append(self.find(comp_name))
            except PluginNotFoundError:
                continue
        return companions

    def resolve_core_plugins(self, domain: str) -> list[Plugin]:
        """Find all core-* plugins matching a domain (+ universal)."""
        matches: list[Plugin] = []
        seen: set[str] = set()
        for base in self.plugins_dirs:
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir() or not d.name.startswith("core-"):
                    continue
                if d.name in seen:
                    continue
                ctl = self._read_ctl(d)
                ctl_domain = ctl.get("domain")
                if ctl_domain == "universal" or ctl_domain == domain:
                    seen.add(d.name)
                    matches.append(self._build_plugin(d.name, d))
        return matches

    def expand_kit(self, kit_name: str) -> list[Plugin]:
        """Full kit expansion: resolve the named plugin, its companions,
        and domain-matched core plugins. Returns deduplicated list.

        Core plugins come first (foundational knowledge), then companions,
        then the requested plugins.

        Emits plugin.loaded for each plugin if telemetry is configured.

        Raises PluginNotFoundError if the kit cannot be resolved.
        """
        prefix_result = self.resolve_prefix(kit_name)
        plugin_names = prefix_result if prefix_result else [kit_name]

        seen: set[str] = set()
        team_result: list[Plugin] = []

        for pname in plugin_names:
            plugin = self.find(pname)

            # Resolve companions first
            for comp in self.resolve_companions(plugin):
                if comp.name not in seen:
                    seen.add(comp.name)
                    team_result.append(comp)

            if pname not in seen:
                seen.add(pname)
                team_result.append(plugin)

        # Determine domain from first resolved plugin
        domain = None
        for p in team_result:
            if p.domain:
                domain = p.domain
                break

        # Auto-load core plugins matching the domain
        core_result: list[Plugin] = []
        if domain:
            for core in self.resolve_core_plugins(domain):
                if core.name not in seen:
                    seen.add(core.name)
                    core_result.append(core)

        result = core_result + team_result

        # Emit telemetry for each loaded plugin
        if self.telemetry:
            for p in result:
                self.telemetry.emit(
                    "plugin.loaded",
                    {
                        "plugin": p.name,
                        "role": p.role,
                        "domain": p.domain,
                    },
                )

        return result

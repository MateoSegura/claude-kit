"""Scenario loader — parse YAML scenario definitions into typed structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Turn:
    """A single turn in a conversation scenario.

    Roles:
        user        — message sent to Claude as a user turn
        expected    — validation against the previous assistant response
        human_sim   — simulated human follow-up injected as a user message
    """

    role: str
    content: str = ""
    contains: list[str] = field(default_factory=list)
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        valid_roles = {"user", "expected", "human_sim"}
        if self.role not in valid_roles:
            raise ValueError(
                f"Invalid turn role '{self.role}'. Must be one of: {valid_roles}"
            )


@dataclass
class Validation:
    """A post-scenario validation check.

    Types:
        response_contains — assert that the final response contains a string
        no_error          — assert that no API errors occurred during the run
    """

    type: str
    value: str = ""

    def __post_init__(self) -> None:
        valid_types = {"response_contains", "no_error"}
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid validation type '{self.type}'. Must be one of: {valid_types}"
            )


@dataclass
class Scenario:
    """A complete test scenario parsed from a YAML file."""

    name: str
    description: str
    model: str
    max_tokens: int
    turns: list[Turn]
    plugins: list[str] = field(default_factory=list)
    validations: list[Validation] = field(default_factory=list)
    mode: str = "subprocess"  # "subprocess" or "library"
    source_path: str = ""


def _parse_turn(raw: dict[str, Any]) -> Turn:
    """Parse a single turn dictionary from YAML into a Turn object."""
    return Turn(
        role=raw["role"],
        content=raw.get("content", ""),
        contains=raw.get("contains", []),
        max_tokens=raw.get("max_tokens"),
    )


def _parse_validation(raw: dict[str, Any]) -> Validation:
    """Parse a single validation dictionary from YAML into a Validation object."""
    return Validation(
        type=raw["type"],
        value=raw.get("value", ""),
    )


def load_scenario(path: Path) -> Scenario:
    """Load and parse a single scenario YAML file.

    Args:
        path: Path to a .yml scenario file.

    Returns:
        A fully parsed Scenario object.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the YAML is malformed.
        KeyError: If required fields are missing.
    """
    with open(path) as f:
        raw = yaml.safe_load(f)

    turns = [_parse_turn(t) for t in raw.get("turns", [])]
    validations = [_parse_validation(v) for v in raw.get("validations", [])]

    return Scenario(
        name=raw["name"],
        description=raw.get("description", ""),
        model=raw.get("model", "claude-sonnet-4-20250514"),
        max_tokens=raw.get("max_tokens", 4096),
        turns=turns,
        plugins=raw.get("plugins", []),
        validations=validations,
        mode=raw.get("mode", "subprocess"),
        source_path=str(path),
    )


def load_all_scenarios(directory: Path) -> list[Scenario]:
    """Load all .yml scenario files from a directory (non-recursive).

    Args:
        directory: Path to a directory containing scenario YAML files.

    Returns:
        List of parsed Scenario objects, sorted by filename.
    """
    paths = sorted(directory.glob("*.yml"))
    return [load_scenario(p) for p in paths]

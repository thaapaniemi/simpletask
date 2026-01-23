"""Predefined quality requirement presets for common tech stacks.

This module provides quality configurations for popular programming languages
and frameworks, allowing quick setup of linting, type checking, and testing.

Presets can be loaded from YAML files in the following locations (in order):
1. Project-specific: .simpletask/presets.yaml
2. User-specific: ~/.config/simpletask/presets.yaml
3. Built-in: Hardcoded QUALITY_PRESETS

Custom presets take precedence over built-in presets with the same name.
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from simpletask.core.models import (
    LintingConfig,
    QualityRequirements,
    SecurityCheckConfig,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
)

# Predefined quality presets for common tech stacks
QUALITY_PRESETS: dict[str, QualityRequirements] = {
    "python": QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
        type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
        testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
        security_check=SecurityCheckConfig(enabled=False, tool=None, args=[]),
    ),
    "typescript": QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.ESLINT, args=[".", "--ext", ".ts,.tsx"]),
        type_checking=TypeCheckConfig(enabled=True, tool=ToolName.TSC, args=["--noEmit"]),
        testing=TestingConfig(enabled=True, tool=ToolName.NPM, args=["test"], min_coverage=80),
        security_check=SecurityCheckConfig(enabled=False, tool=None, args=[]),
    ),
    "node": QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.ESLINT, args=["."]),
        type_checking=None,
        testing=TestingConfig(enabled=True, tool=ToolName.NPM, args=["test"], min_coverage=75),
        security_check=SecurityCheckConfig(enabled=True, tool=ToolName.NPM, args=["audit"]),
    ),
    "go": QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.GOLANGCI_LINT, args=["run"]),
        type_checking=None,  # Go has built-in type checking at compile time
        testing=TestingConfig(enabled=True, tool=ToolName.GO, args=["test", "./..."], min_coverage=80),
        security_check=SecurityCheckConfig(enabled=True, tool=ToolName.GOSEC, args=["./..."]),
    ),
    "rust": QualityRequirements(
        linting=LintingConfig(
            enabled=True, tool=ToolName.CARGO, args=["clippy", "--", "-D", "warnings"]
        ),
        type_checking=None,  # Rust has built-in type checking at compile time
        testing=TestingConfig(enabled=True, tool=ToolName.CARGO, args=["test"], min_coverage=75),
        security_check=SecurityCheckConfig(enabled=True, tool=ToolName.CARGO, args=["audit"]),
    ),
    "java-maven": QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.MVN, args=["checkstyle:check"]),
        type_checking=None,  # Java has built-in type checking at compile time
        testing=TestingConfig(enabled=True, tool=ToolName.MVN, args=["test"], min_coverage=80),
        security_check=SecurityCheckConfig(
            enabled=True, tool=ToolName.MVN, args=["dependency-check:check"]
        ),
    ),
    "java-gradle": QualityRequirements(
        linting=LintingConfig(
            enabled=True, tool=ToolName.GRADLE, args=["checkstyleMain", "checkstyleTest"]
        ),
        type_checking=None,  # Java has built-in type checking at compile time
        testing=TestingConfig(enabled=True, tool=ToolName.GRADLE, args=["test"], min_coverage=80),
        security_check=SecurityCheckConfig(
            enabled=True, tool=ToolName.GRADLE, args=["dependencyCheckAnalyze"]
        ),
    ),
}


def build_command(tool: ToolName, args: list[str]) -> list[str]:
    """Build a command list from tool name and arguments for subprocess execution.

    Args:
        tool: The whitelisted tool to execute
        args: Arguments to pass to the tool

    Returns:
        Command list ready for subprocess.run()

    Example:
        >>> build_command(ToolName.RUFF, ["check", "."])
        ["ruff", "check", "."]
    """
    return [tool.value, *args]


def get_preset_search_paths() -> list[Path]:
    """Get list of paths to search for custom preset files.

    Returns:
        List of paths in priority order (first found wins):
        1. .simpletask/presets.yaml (project-specific)
        2. ~/.config/simpletask/presets.yaml (user-specific)
    """
    paths = []

    # Project-specific preset file
    project_preset = Path(".simpletask/presets.yaml")
    if project_preset.exists():
        paths.append(project_preset)

    # User-specific preset file
    user_config_dir = Path.home() / ".config" / "simpletask"
    user_preset = user_config_dir / "presets.yaml"
    if user_preset.exists():
        paths.append(user_preset)

    return paths


def load_presets_from_file(path: Path) -> dict[str, QualityRequirements]:
    """Load custom quality presets from a YAML file.

    Args:
        path: Path to the YAML preset file

    Returns:
        Dictionary mapping preset names to QualityRequirements

    Raises:
        ValueError: If the file is invalid or contains validation errors
        FileNotFoundError: If the file does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Preset file not found: {path}")

    try:
        with path.open("r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise TypeError(
                f"Preset file must contain a YAML dictionary, got {type(data).__name__}"
            )

        presets: dict[str, QualityRequirements] = {}

        for name, config in data.items():
            if not isinstance(config, dict):
                raise TypeError(
                    f"Preset '{name}' must be a dictionary, got {type(config).__name__}"
                )

            try:
                # Parse the quality requirements using Pydantic
                preset = QualityRequirements.model_validate(config)
                presets[name] = preset
            except ValidationError as e:
                raise ValueError(f"Invalid preset '{name}': {e}") from e

        return presets

    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML file {path}: {e}") from e


def load_all_presets() -> dict[str, QualityRequirements]:
    """Load all available presets (custom + built-in).

    Custom presets from files take precedence over built-in presets
    with the same name.

    Returns:
        Dictionary mapping preset names to QualityRequirements
    """
    # Start with built-in presets
    all_presets = QUALITY_PRESETS.copy()

    # Load custom presets from files (in reverse order so earlier paths take precedence)
    for path in reversed(get_preset_search_paths()):
        try:
            custom_presets = load_presets_from_file(path)
            all_presets.update(custom_presets)
        except (ValueError, FileNotFoundError):
            # Silently skip invalid or missing preset files
            pass

    return all_presets


def get_preset(name: str) -> QualityRequirements:
    """Get a quality requirements preset by name.

    Searches for presets in this order:
    1. Custom presets from .simpletask/presets.yaml (project-specific)
    2. Custom presets from ~/.config/simpletask/presets.yaml (user-specific)
    3. Built-in presets

    Args:
        name: The preset name (e.g., 'python', 'typescript', 'node', 'go', 'rust',
              'java-maven', 'java-gradle')

    Returns:
        The QualityRequirements preset configuration

    Raises:
        ValueError: If the preset name is not found
    """
    all_presets = load_all_presets()

    if name not in all_presets:
        available = ", ".join(sorted(all_presets.keys()))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")

    return all_presets[name]


def list_presets() -> list[str]:
    """Get a list of available preset names (custom + built-in).

    Returns:
        List of preset names sorted alphabetically
    """
    all_presets = load_all_presets()
    return sorted(all_presets.keys())


def apply_preset(
    existing: QualityRequirements | None, preset_name: str
) -> tuple[QualityRequirements, dict[str, bool]]:
    """Apply a preset to existing quality requirements using fill-gaps-only strategy.

    This function only fills in missing configurations. Existing configurations
    are preserved.

    Args:
        existing: The existing quality requirements (or None if not set)
        preset_name: The preset name to apply

    Returns:
        A tuple of:
        - The merged QualityRequirements
        - A dict indicating which fields were applied from preset

    Raises:
        ValueError: If the preset name is not found
    """
    preset = get_preset(preset_name)

    # Track what was applied
    applied: dict[str, bool] = {
        "linting": False,
        "type_checking": False,
        "testing": False,
        "security_check": False,
    }

    # If no existing config, use preset directly
    if existing is None:
        return (
            preset,
            {"linting": True, "type_checking": True, "testing": True, "security_check": True},
        )

    # Fill gaps only
    linting = existing.linting
    type_checking = existing.type_checking
    testing = existing.testing
    security_check = existing.security_check

    # Apply preset values only for missing fields
    # Note: linting and testing are required in the model, so they should always exist
    # We only fill type_checking and security_check if they're None

    if type_checking is None and preset.type_checking is not None:
        type_checking = preset.type_checking
        applied["type_checking"] = True

    if security_check is None and preset.security_check is not None:
        security_check = preset.security_check
        applied["security_check"] = True

    merged = QualityRequirements(
        linting=linting,
        type_checking=type_checking,
        testing=testing,
        security_check=security_check,
    )

    return merged, applied


__all__ = [
    "QUALITY_PRESETS",
    "apply_preset",
    "build_command",
    "get_preset",
    "get_preset_search_paths",
    "list_presets",
    "load_all_presets",
    "load_presets_from_file",
]

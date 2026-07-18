"""AI template management for OpenCode, GitHub Copilot, and Pi resources."""

import importlib.resources
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

EditorType = Literal["opencode", "copilot", "pi"]


@dataclass(frozen=True)
class EditorConfig:
    """Configuration for an editor's template system."""

    display_name: str
    template_subdir: str
    file_extension: str
    global_config_dir: tuple[str, ...]
    local_config_dir: tuple[str, ...]
    global_base_dir: tuple[str, ...] = ()
    global_agents_dir: tuple[str, ...] | None = None
    local_agents_dir: tuple[str, ...] | None = None


EDITOR_CONFIGS: dict[EditorType, EditorConfig] = {
    "opencode": EditorConfig(
        display_name="OpenCode",
        template_subdir="opencode",
        file_extension=".md",
        global_config_dir=(".config", "opencode", "commands"),
        local_config_dir=(".opencode", "commands"),
        global_base_dir=(".config", "opencode"),
        global_agents_dir=(".config", "opencode", "agents"),
        local_agents_dir=(".opencode", "agents"),
    ),
    "copilot": EditorConfig(
        display_name="GitHub Copilot",
        template_subdir="copilot",
        file_extension=".prompt.md",
        global_config_dir=(".github", "prompts"),
        local_config_dir=(".github", "prompts"),
        global_base_dir=(".github",),
    ),
    "pi": EditorConfig(
        display_name="Pi",
        template_subdir="pi",
        file_extension=".md",
        global_config_dir=(".pi", "agent", "prompts"),
        local_config_dir=(".pi", "prompts"),
        global_base_dir=(".pi",),
    ),
}


def _get_config(editor: EditorType) -> EditorConfig:
    """Return configuration for a supported editor."""
    try:
        return EDITOR_CONFIGS[editor]
    except KeyError as error:
        raise ValueError(f"Unsupported editor: {editor}") from error


def _get_templates_dir(editor: EditorType) -> Path:
    """Get the path to bundled templates for an editor."""
    config = _get_config(editor)
    try:
        package_files = importlib.resources.files("simpletask")
        return Path(str(package_files / "templates" / config.template_subdir))
    except AttributeError:
        import simpletask

        package_dir = Path(simpletask.__file__).parent
        return package_dir / "templates" / config.template_subdir


def _get_bundled_templates(editor: EditorType) -> list[Path]:
    """Get bundled template files for an editor."""
    config = _get_config(editor)
    templates_dir = _get_templates_dir(editor)
    if not templates_dir.exists():
        return []
    return sorted(templates_dir.glob(f"*{config.file_extension}"))


def _get_global_commands_dir(editor: EditorType) -> Path:
    """Get an editor's global prompt or command directory."""
    config = _get_config(editor)
    return Path.home().joinpath(*config.global_config_dir)


def _get_local_commands_dir(editor: EditorType) -> Path:
    """Get an editor's project-local prompt or command directory."""
    config = _get_config(editor)
    return Path.cwd().joinpath(*config.local_config_dir)


def get_editor_base_dir(editor: EditorType) -> Path:
    """Get the global base directory used to detect an editor installation."""
    config = _get_config(editor)
    return Path.home().joinpath(*config.global_base_dir)


def is_editor_installed(editor: EditorType) -> bool:
    """Return whether an editor's global base directory exists."""
    return get_editor_base_dir(editor).exists()


def _install_files(
    files: list[Path],
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install files and return names grouped as installed, skipped, overwritten."""
    target_dir.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    skipped: list[str] = []
    overwritten: list[str] = []

    for source_path in files:
        target_path = target_dir / source_path.name
        if target_path.exists():
            if no_overwrite:
                skipped.append(source_path.name)
                continue
            overwritten.append(source_path.name)
        else:
            installed.append(source_path.name)
        shutil.copy2(source_path, target_path)

    return installed, skipped, overwritten


def _install_templates(
    editor: EditorType,
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install an editor's bundled templates to *target_dir*."""
    config = _get_config(editor)
    templates = _get_bundled_templates(editor)
    if not templates:
        raise FileNotFoundError(f"No {config.display_name} templates found in package")
    return _install_files(templates, target_dir, no_overwrite)


def _get_installed_status(editor: EditorType) -> dict[str, dict[str, bool]]:
    """Return global and local installation status for an editor's templates."""
    templates = _get_bundled_templates(editor)
    global_dir = _get_global_commands_dir(editor)
    local_dir = _get_local_commands_dir(editor)
    return {
        template_path.name: {
            "global": (global_dir / template_path.name).exists(),
            "local": (local_dir / template_path.name).exists(),
        }
        for template_path in templates
    }


def _get_bundled_agents(editor: EditorType) -> list[Path]:
    """Get bundled agent files for an editor, if it supports agents."""
    config = _get_config(editor)
    if config.global_agents_dir is None:
        return []
    agents_dir = _get_templates_dir(editor) / "agents"
    if not agents_dir.exists():
        return []
    return sorted(agents_dir.glob(f"*{config.file_extension}"))


def _get_global_agents_dir(editor: EditorType) -> Path:
    """Get an editor's global agent directory."""
    config = _get_config(editor)
    if config.global_agents_dir is None:
        raise ValueError(f"{config.display_name} does not support agents")
    return Path.home().joinpath(*config.global_agents_dir)


def _get_local_agents_dir(editor: EditorType) -> Path:
    """Get an editor's local agent directory."""
    config = _get_config(editor)
    if config.local_agents_dir is None:
        raise ValueError(f"{config.display_name} does not support agents")
    return Path.cwd().joinpath(*config.local_agents_dir)


def _install_agents(
    editor: EditorType,
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install bundled agents to *target_dir*."""
    config = _get_config(editor)
    agents = _get_bundled_agents(editor)
    if not agents:
        raise FileNotFoundError(f"No {config.display_name} agents found in package")
    return _install_files(agents, target_dir, no_overwrite)


def _get_agents_installed_status(editor: EditorType) -> dict[str, dict[str, bool]]:
    """Return global and local installation status for bundled agents."""
    agents = _get_bundled_agents(editor)
    if not agents:
        return {}
    global_dir = _get_global_agents_dir(editor)
    local_dir = _get_local_agents_dir(editor)
    return {
        agent_path.name: {
            "global": (global_dir / agent_path.name).exists(),
            "local": (local_dir / agent_path.name).exists(),
        }
        for agent_path in agents
    }


class EditorAPI:
    """Generic API for template and agent operations for a supported editor."""

    def __init__(self, editor: EditorType) -> None:
        self._editor = editor

    def templates_dir(self) -> Path:
        """Return the bundled templates directory."""
        return _get_templates_dir(self._editor)

    def bundled_templates(self) -> list[Path]:
        """Return bundled template files."""
        return _get_bundled_templates(self._editor)

    def global_commands_dir(self) -> Path:
        """Return the global prompt or command directory."""
        return _get_global_commands_dir(self._editor)

    def local_commands_dir(self) -> Path:
        """Return the local prompt or command directory."""
        return _get_local_commands_dir(self._editor)

    def install(
        self, target_dir: Path, no_overwrite: bool = False
    ) -> tuple[list[str], list[str], list[str]]:
        """Install bundled templates to *target_dir*."""
        return _install_templates(self._editor, target_dir, no_overwrite)

    def installed_status(self) -> dict[str, dict[str, bool]]:
        """Return installation status for bundled templates."""
        return _get_installed_status(self._editor)

    def bundled_agents(self) -> list[Path]:
        """Return bundled agent files, or an empty list if unsupported."""
        return _get_bundled_agents(self._editor)

    def global_agents_dir(self) -> Path:
        """Return the global agents directory."""
        return _get_global_agents_dir(self._editor)

    def local_agents_dir(self) -> Path:
        """Return the local agents directory."""
        return _get_local_agents_dir(self._editor)

    def install_agents(
        self, target_dir: Path, no_overwrite: bool = False
    ) -> tuple[list[str], list[str], list[str]]:
        """Install bundled agents to *target_dir*."""
        return _install_agents(self._editor, target_dir, no_overwrite)

    def agents_installed_status(self) -> dict[str, dict[str, bool]]:
        """Return installation status for bundled agents."""
        return _get_agents_installed_status(self._editor)


def get_editor_api(editor: EditorType) -> EditorAPI:
    """Return the generic API for a supported editor."""
    _get_config(editor)
    return EditorAPI(editor)


# OpenCode compatibility helpers.
def get_templates_dir() -> Path:
    """Get the bundled OpenCode templates directory."""
    return _get_templates_dir("opencode")


def get_bundled_templates() -> list[Path]:
    """Get bundled OpenCode command templates."""
    return _get_bundled_templates("opencode")


def get_global_commands_dir() -> Path:
    """Get the global OpenCode commands directory."""
    return _get_global_commands_dir("opencode")


def get_local_commands_dir() -> Path:
    """Get the local OpenCode commands directory."""
    return _get_local_commands_dir("opencode")


def install_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install OpenCode command templates to *target_dir*."""
    return _install_templates("opencode", target_dir, no_overwrite)


def get_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status for OpenCode command templates."""
    return _get_installed_status("opencode")


# Copilot helpers use the documented ~/.github/prompts and .github/prompts locations.
def get_copilot_templates_dir() -> Path:
    """Get the bundled GitHub Copilot prompt directory."""
    return _get_templates_dir("copilot")


def get_bundled_copilot_templates() -> list[Path]:
    """Get bundled GitHub Copilot prompt templates."""
    return _get_bundled_templates("copilot")


def get_global_copilot_commands_dir() -> Path:
    """Get the global GitHub Copilot prompts directory."""
    return _get_global_commands_dir("copilot")


def get_local_copilot_commands_dir() -> Path:
    """Get the local GitHub Copilot prompts directory."""
    return _get_local_commands_dir("copilot")


def install_copilot_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install GitHub Copilot prompt templates to *target_dir*."""
    return _install_templates("copilot", target_dir, no_overwrite)


def get_copilot_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status for GitHub Copilot prompt templates."""
    return _get_installed_status("copilot")


# Pi compatibility helpers.
def get_pi_templates_dir() -> Path:
    """Get the bundled Pi prompt directory."""
    return _get_templates_dir("pi")


def get_bundled_pi_templates() -> list[Path]:
    """Get bundled Pi prompt templates."""
    return _get_bundled_templates("pi")


def get_global_pi_commands_dir() -> Path:
    """Get the global Pi prompts directory."""
    return _get_global_commands_dir("pi")


def get_local_pi_commands_dir() -> Path:
    """Get the local Pi prompts directory."""
    return _get_local_commands_dir("pi")


def install_pi_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install Pi prompt templates to *target_dir*."""
    return _install_templates("pi", target_dir, no_overwrite)


def get_pi_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status for Pi prompt templates."""
    return _get_installed_status("pi")


# OpenCode agent compatibility helpers.
def get_bundled_agents() -> list[Path]:
    """Get bundled OpenCode agent files."""
    return _get_bundled_agents("opencode")


def get_global_agents_dir() -> Path:
    """Get the global OpenCode agents directory."""
    return _get_global_agents_dir("opencode")


def get_local_agents_dir() -> Path:
    """Get the local OpenCode agents directory."""
    return _get_local_agents_dir("opencode")


def install_agents(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install OpenCode agents to *target_dir*."""
    return _install_agents("opencode", target_dir, no_overwrite)


def get_agents_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status for OpenCode agents."""
    return _get_agents_installed_status("opencode")

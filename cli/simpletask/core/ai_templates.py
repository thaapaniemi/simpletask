"""AI template management for OpenCode, Qwen, Gemini, Pi, and Vibe resources."""

import importlib.resources
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

EditorType = Literal["opencode", "qwen", "gemini", "pi", "vibe"]


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
    is_directory_based: bool = False


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
    "qwen": EditorConfig(
        display_name="Qwen",
        template_subdir="qwen",
        file_extension=".md",
        global_config_dir=(".qwen", "commands"),
        local_config_dir=(".qwen", "commands"),
        global_base_dir=(".qwen",),
    ),
    "gemini": EditorConfig(
        display_name="Gemini CLI",
        template_subdir="gemini",
        file_extension=".toml",
        global_config_dir=(".gemini", "commands"),
        local_config_dir=(".gemini", "commands"),
        global_base_dir=(".gemini",),
    ),
    "pi": EditorConfig(
        display_name="Pi",
        template_subdir="pi",
        file_extension=".md",
        # Global Pi uses ~/.pi/agent/prompts/ (3 segments) because Pi organises its global
        # prompt library under an 'agent' sub-level. Local project installs use the
        # shorter .pi/prompts/ path (2 segments) — Pi resolves project-local prompts there.
        global_config_dir=(".pi", "agent", "prompts"),
        local_config_dir=(".pi", "prompts"),
        global_base_dir=(".pi",),
    ),
    "vibe": EditorConfig(
        display_name="Mistral Vibe",
        template_subdir="vibe",
        file_extension=".md",
        global_config_dir=(".vibe", "skills"),
        local_config_dir=(".vibe", "skills"),
        global_base_dir=(".vibe",),
        is_directory_based=True,
    ),
}


def _get_templates_dir(editor: EditorType) -> Path:
    """Get path to bundled templates directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        Path to the templates directory within the package.
    """
    config = EDITOR_CONFIGS[editor]
    try:
        # Python 3.11+ preferred method
        package_files = importlib.resources.files("simpletask")
        templates_path = package_files / "templates" / config.template_subdir
        return Path(str(templates_path))
    except AttributeError:
        # Fallback for older Python versions
        import simpletask

        package_dir = Path(simpletask.__file__).parent
        return package_dir / "templates" / config.template_subdir


def _get_bundled_templates(editor: EditorType) -> list[Path]:
    """Get list of template files or skill directories bundled with the package.

    For flat-file editors (OpenCode, Qwen, Gemini), returns file paths matching
    the editor's file extension. For directory-based editors (Vibe), returns
    skill directory paths (each containing a SKILL.md).

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        List of Path objects for each template file or skill directory.
    """
    config = EDITOR_CONFIGS[editor]
    templates_dir = _get_templates_dir(editor)
    if not templates_dir.exists():
        return []

    if config.is_directory_based:
        return sorted(
            p for p in templates_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
        )

    return sorted(templates_dir.glob(f"*{config.file_extension}"))


def _get_global_commands_dir(editor: EditorType) -> Path:
    """Get global commands directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        Path to global commands directory.
    """
    config = EDITOR_CONFIGS[editor]
    return Path.home().joinpath(*config.global_config_dir)


def _get_local_commands_dir(editor: EditorType) -> Path:
    """Get local commands directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        Path to local commands directory in current working directory.
    """
    config = EDITOR_CONFIGS[editor]
    return Path.cwd().joinpath(*config.local_config_dir)


def get_editor_base_dir(editor: EditorType) -> Path:
    """Get the global base directory for an editor.

    This is the top-level directory whose existence indicates whether the
    editor is installed on the machine (e.g. ~/.config/opencode for OpenCode).

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        Path to the editor's global base directory.
    """
    config = EDITOR_CONFIGS[editor]
    return Path.home().joinpath(*config.global_base_dir)


def is_editor_installed(editor: EditorType) -> bool:
    """Check whether an editor is installed on the current machine.

    An editor is considered installed if its global base directory exists.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        True if the editor's global base directory exists, False otherwise.
    """
    return get_editor_base_dir(editor).exists()


def _install_files(
    files: list[Path],
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install files from a list to target directory.

    This is a shared helper for installing templates and agents.

    Args:
        files: List of source file Path objects to install
        target_dir: Directory to install files into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.
    """
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
    overwritten = []

    for source_path in files:
        target_path = target_dir / source_path.name

        if target_path.exists():
            if no_overwrite:
                skipped.append(source_path.name)
                continue
            else:
                overwritten.append(source_path.name)
        else:
            installed.append(source_path.name)

        # Copy the file
        shutil.copy2(source_path, target_path)

    return installed, skipped, overwritten


def _install_skill_dirs(
    skill_dirs: list[Path],
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install skill directories to target directory.

    For directory-based editors (like Vibe), each skill is a directory
    containing a SKILL.md file. This copies entire directories instead
    of individual files.

    Args:
        skill_dirs: List of source skill directory Path objects to install
        target_dir: Directory to install skill directories into
        no_overwrite: If True, skip existing directories instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) directory names.
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
    overwritten = []

    for source_dir in skill_dirs:
        target_path = target_dir / source_dir.name

        if target_path.exists():
            if no_overwrite:
                skipped.append(source_dir.name)
                continue
            else:
                overwritten.append(source_dir.name)
        else:
            installed.append(source_dir.name)

        shutil.copytree(source_dir, target_path, dirs_exist_ok=True)

    return installed, skipped, overwritten


def _install_templates(
    editor: EditorType,
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install templates to target directory for an editor.

    Dispatches to _install_files() for flat-file editors or
    _install_skill_dirs() for directory-based editors.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")
        target_dir: Directory to install templates into
        no_overwrite: If True, skip existing files/directories instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    config = EDITOR_CONFIGS[editor]
    templates = _get_bundled_templates(editor)

    if not templates:
        raise FileNotFoundError(f"No {config.display_name} templates found in package")

    if config.is_directory_based:
        return _install_skill_dirs(templates, target_dir, no_overwrite)

    return _install_files(templates, target_dir, no_overwrite)


def _get_installed_status(editor: EditorType) -> dict[str, dict[str, bool]]:
    """Get installation status of each template for an editor.

    For directory-based editors, checks for directory existence instead of
    file existence.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe")

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
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
    """Get list of agent files bundled with the package for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", or "gemini")

    Returns:
        List of Path objects for each agent file. Empty list if editor has
        no agent support.
    """
    config = EDITOR_CONFIGS[editor]
    if config.global_agents_dir is None:
        return []

    templates_dir = _get_templates_dir(editor)
    agents_dir = templates_dir / "agents"
    if not agents_dir.exists():
        return []

    return sorted(agents_dir.glob(f"*{config.file_extension}"))


def _get_global_agents_dir(editor: EditorType) -> Path:
    """Get global agents directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", or "gemini")

    Returns:
        Path to global agents directory.

    Raises:
        ValueError: If editor does not support agents (agents_dir is None).
    """
    config = EDITOR_CONFIGS[editor]
    if config.global_agents_dir is None:
        raise ValueError(f"{config.display_name} does not support agents")
    return Path.home().joinpath(*config.global_agents_dir)


def _get_local_agents_dir(editor: EditorType) -> Path:
    """Get local agents directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", or "gemini")

    Returns:
        Path to local agents directory in current working directory.

    Raises:
        ValueError: If editor does not support agents (agents_dir is None).
    """
    config = EDITOR_CONFIGS[editor]
    if config.local_agents_dir is None:
        raise ValueError(f"{config.display_name} does not support agents")
    return Path.cwd().joinpath(*config.local_agents_dir)


def _install_agents(
    editor: EditorType,
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install agents to target directory for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", or "gemini")
        target_dir: Directory to install agents into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If no agents are found or editor has no agent
            support.
    """
    config = EDITOR_CONFIGS[editor]
    agents = _get_bundled_agents(editor)

    if not agents:
        raise FileNotFoundError(f"No {config.display_name} agents found in package")

    return _install_files(agents, target_dir, no_overwrite)


def _get_agents_installed_status(editor: EditorType) -> dict[str, dict[str, bool]]:
    """Get installation status of each agent for an editor.

    Args:
        editor: Editor type ("opencode", "qwen", or "gemini")

    Returns:
        Dict mapping agent name to {"global": bool, "local": bool}

    Note:
        The early return when no bundled agents are found is safe because
        _get_bundled_agents() returns an empty list for editors without agent
        support (Qwen and Gemini), so the early return prevents unnecessary
        directory access errors for those editors.
    """
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
    """Unified API for all editor-specific operations.

    Wraps the private generic functions so new editors only need an entry
    in ``EDITOR_CONFIGS`` — no new public wrapper functions are required.

    Usage::

        api = get_editor_api("pi")
        api.templates_dir()
        api.bundled_templates()
        api.global_commands_dir()
        api.local_commands_dir()
        api.install(target_dir)
        api.installed_status()
        api.bundled_agents()
        api.global_agents_dir()
        api.local_agents_dir()
        api.install_agents(target_dir)
        api.agents_installed_status()
    """

    def __init__(self, editor: EditorType) -> None:
        self._editor = editor

    def templates_dir(self) -> Path:
        """Return the bundled templates directory for this editor."""
        return _get_templates_dir(self._editor)

    def bundled_templates(self) -> list[Path]:
        """Return bundled template files or skill dirs for this editor."""
        return _get_bundled_templates(self._editor)

    def global_commands_dir(self) -> Path:
        """Return the global commands directory for this editor."""
        return _get_global_commands_dir(self._editor)

    def local_commands_dir(self) -> Path:
        """Return the local commands directory for this editor."""
        return _get_local_commands_dir(self._editor)

    def install(
        self, target_dir: Path, no_overwrite: bool = False
    ) -> tuple[list[str], list[str], list[str]]:
        """Install templates to *target_dir*.

        Returns:
            Tuple of (installed, skipped, overwritten) names.
        """
        return _install_templates(self._editor, target_dir, no_overwrite)

    def installed_status(self) -> dict[str, dict[str, bool]]:
        """Return installation status of each template for this editor."""
        return _get_installed_status(self._editor)

    def bundled_agents(self) -> list[Path]:
        """Return bundled agent files for this editor (empty list if unsupported)."""
        return _get_bundled_agents(self._editor)

    def global_agents_dir(self) -> Path:
        """Return the global agents directory for this editor.

        Raises:
            ValueError: If this editor does not support agents.
        """
        return _get_global_agents_dir(self._editor)

    def local_agents_dir(self) -> Path:
        """Return the local agents directory for this editor.

        Raises:
            ValueError: If this editor does not support agents.
        """
        return _get_local_agents_dir(self._editor)

    def install_agents(
        self, target_dir: Path, no_overwrite: bool = False
    ) -> tuple[list[str], list[str], list[str]]:
        """Install agents to *target_dir*.

        Returns:
            Tuple of (installed, skipped, overwritten) file names.

        Raises:
            FileNotFoundError: If no agents found or editor has no agent support.
        """
        return _install_agents(self._editor, target_dir, no_overwrite)

    def agents_installed_status(self) -> dict[str, dict[str, bool]]:
        """Return installation status of each agent for this editor."""
        return _get_agents_installed_status(self._editor)


def get_editor_api(editor: EditorType) -> EditorAPI:
    """Return an :class:`EditorAPI` for the given editor.

    This is the preferred way to interact with an editor's templates and
    agents.  Adding a new editor only requires an entry in
    :data:`EDITOR_CONFIGS` — no new public wrapper functions are needed.

    Args:
        editor: Editor type ("opencode", "qwen", "gemini", "pi", or "vibe").

    Returns:
        An :class:`EditorAPI` instance for *editor*.
    """
    return EditorAPI(editor)


def get_templates_dir() -> Path:
    """Get path to bundled OpenCode templates directory.

    Returns:
        Path to the templates/opencode directory within the package.
    """
    return _get_templates_dir("opencode")


def get_qwen_templates_dir() -> Path:
    """Get path to bundled Qwen templates directory.

    Returns:
        Path to the templates/qwen directory within the package.
    """
    return _get_templates_dir("qwen")


def get_gemini_templates_dir() -> Path:
    """Get path to bundled Gemini templates directory.

    Returns:
        Path to the templates/gemini directory within the package.
    """
    return _get_templates_dir("gemini")


def get_pi_templates_dir() -> Path:
    """Get path to bundled Pi templates directory.

    Returns:
        Path to the templates/pi directory within the package.
    """
    return _get_templates_dir("pi")


def get_bundled_templates() -> list[Path]:
    """Get list of OpenCode template files bundled with the package.

    Returns:
        List of Path objects for each template file.
    """
    return _get_bundled_templates("opencode")


def get_bundled_qwen_templates() -> list[Path]:
    """Get list of Qwen template files bundled with the package.

    Returns:
        List of Path objects for each template file.
    """
    return _get_bundled_templates("qwen")


def get_bundled_gemini_templates() -> list[Path]:
    """Get list of Gemini template files bundled with the package.

    Returns:
        List of Path objects for each template file.
    """
    return _get_bundled_templates("gemini")


def get_bundled_pi_templates() -> list[Path]:
    """Get list of Pi prompt template files bundled with the package.

    Returns:
        List of Path objects for each prompt template file.
    """
    return _get_bundled_templates("pi")


def get_global_commands_dir() -> Path:
    """Get global OpenCode commands directory.

    Returns:
        Path to ~/.config/opencode/commands/
    """
    return _get_global_commands_dir("opencode")


def get_global_qwen_commands_dir() -> Path:
    """Get global Qwen commands directory.

    Returns:
        Path to ~/.qwen/commands/
    """
    return _get_global_commands_dir("qwen")


def get_global_gemini_commands_dir() -> Path:
    """Get global Gemini commands directory.

    Returns:
        Path to ~/.gemini/commands/
    """
    return _get_global_commands_dir("gemini")


def get_global_pi_commands_dir() -> Path:
    """Get global Pi prompts directory.

    Returns:
        Path to ~/.pi/agent/prompts/
    """
    return _get_global_commands_dir("pi")


def get_local_commands_dir() -> Path:
    """Get local OpenCode commands directory.

    Returns:
        Path to .opencode/commands/ in current directory.
    """
    return _get_local_commands_dir("opencode")


def get_local_qwen_commands_dir() -> Path:
    """Get local Qwen commands directory.

    Returns:
        Path to .qwen/commands/ in current directory.
    """
    return _get_local_commands_dir("qwen")


def get_local_gemini_commands_dir() -> Path:
    """Get local Gemini commands directory.

    Returns:
        Path to .gemini/commands/ in current directory.
    """
    return _get_local_commands_dir("gemini")


def get_local_pi_commands_dir() -> Path:
    """Get local Pi prompts directory.

    Returns:
        Path to .pi/prompts/ in current directory.
    """
    return _get_local_commands_dir("pi")


def install_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install OpenCode templates to target directory.

    Args:
        target_dir: Directory to install templates into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    return _install_templates("opencode", target_dir, no_overwrite)


def install_qwen_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install Qwen templates to target directory.

    Args:
        target_dir: Directory to install templates into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    return _install_templates("qwen", target_dir, no_overwrite)


def install_gemini_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install Gemini templates to target directory.

    Args:
        target_dir: Directory to install templates into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    return _install_templates("gemini", target_dir, no_overwrite)


def install_pi_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install Pi prompt templates to target directory.

    Args:
        target_dir: Directory to install prompts into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    return _install_templates("pi", target_dir, no_overwrite)


def get_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each OpenCode template.

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
    return _get_installed_status("opencode")


def get_qwen_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each Qwen template.

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
    return _get_installed_status("qwen")


def get_gemini_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each Gemini template.

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
    return _get_installed_status("gemini")


def get_pi_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each Pi prompt template.

    Returns:
        Dict mapping prompt template name to {"global": bool, "local": bool}
    """
    return _get_installed_status("pi")


def get_bundled_agents() -> list[Path]:
    """Get list of OpenCode agent files bundled with the package.

    Returns:
        List of Path objects for each agent file.
    """
    return _get_bundled_agents("opencode")


def get_global_agents_dir() -> Path:
    """Get global OpenCode agents directory.

    Returns:
        Path to ~/.config/opencode/agents/
    """
    return _get_global_agents_dir("opencode")


def get_local_agents_dir() -> Path:
    """Get local OpenCode agents directory.

    Returns:
        Path to .opencode/agents/ in current directory.
    """
    return _get_local_agents_dir("opencode")


def install_agents(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install OpenCode agents to target directory.

    Args:
        target_dir: Directory to install agents into
        no_overwrite: If True, skip existing files instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) file names.

    Raises:
        FileNotFoundError: If agents directory doesn't exist
    """
    return _install_agents("opencode", target_dir, no_overwrite)


def get_agents_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each OpenCode agent.

    Returns:
        Dict mapping agent name to {"global": bool, "local": bool}
    """
    return _get_agents_installed_status("opencode")


def get_vibe_templates_dir() -> Path:
    """Get path to bundled Vibe templates directory.

    Returns:
        Path to the templates/vibe directory within the package.
    """
    return _get_templates_dir("vibe")


def get_bundled_vibe_templates() -> list[Path]:
    """Get list of Vibe skill directories bundled with the package.

    Returns:
        List of Path objects for each skill directory.
    """
    return _get_bundled_templates("vibe")


def get_global_vibe_commands_dir() -> Path:
    """Get global Vibe skills directory.

    Returns:
        Path to ~/.vibe/skills/
    """
    return _get_global_commands_dir("vibe")


def get_local_vibe_commands_dir() -> Path:
    """Get local Vibe skills directory.

    Returns:
        Path to .vibe/skills/ in current directory.
    """
    return _get_local_commands_dir("vibe")


def install_vibe_templates(
    target_dir: Path,
    no_overwrite: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    """Install Vibe skill directories to target directory.

    Args:
        target_dir: Directory to install skills into
        no_overwrite: If True, skip existing directories instead of overwriting

    Returns:
        Tuple of (installed, skipped, overwritten) directory names.

    Raises:
        FileNotFoundError: If templates directory doesn't exist
    """
    return _install_templates("vibe", target_dir, no_overwrite)


def get_vibe_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each Vibe skill.

    Returns:
        Dict mapping skill directory name to {"global": bool, "local": bool}
    """
    return _get_installed_status("vibe")

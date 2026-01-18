"""AI template management for OpenCode and Qwen command files."""

import importlib.resources
import shutil
from pathlib import Path


def get_templates_dir() -> Path:
    """Get path to bundled OpenCode templates directory.

    Returns:
        Path to the templates/opencode directory within the package.
    """
    # Use importlib.resources to get the package path
    try:
        # Python 3.11+ preferred method
        package_files = importlib.resources.files("simpletask")
        templates_path = package_files / "templates" / "opencode"
        return Path(str(templates_path))
    except AttributeError:
        # Fallback for older Python versions
        import simpletask

        package_dir = Path(simpletask.__file__).parent
        return package_dir / "templates" / "opencode"


def get_qwen_templates_dir() -> Path:
    """Get path to bundled Qwen templates directory.

    Returns:
        Path to the templates/qwen directory within the package.
    """
    try:
        # Python 3.11+ preferred method
        package_files = importlib.resources.files("simpletask")
        templates_path = package_files / "templates" / "qwen"
        return Path(str(templates_path))
    except AttributeError:
        # Fallback for older Python versions
        import simpletask

        package_dir = Path(simpletask.__file__).parent
        return package_dir / "templates" / "qwen"


def get_bundled_templates() -> list[Path]:
    """Get list of OpenCode template files bundled with the package.

    Returns:
        List of Path objects for each template file.
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return []

    return sorted(templates_dir.glob("*.md"))


def get_bundled_qwen_templates() -> list[Path]:
    """Get list of Qwen template files bundled with the package.

    Returns:
        List of Path objects for each template file.
    """
    templates_dir = get_qwen_templates_dir()
    if not templates_dir.exists():
        return []

    return sorted(templates_dir.glob("*.toml"))


def get_global_commands_dir() -> Path:
    """Get global OpenCode commands directory.

    Returns:
        Path to ~/.config/opencode/commands/
    """
    return Path.home() / ".config" / "opencode" / "commands"


def get_global_qwen_commands_dir() -> Path:
    """Get global Qwen commands directory.

    Returns:
        Path to ~/.qwen/commands/
    """
    return Path.home() / ".qwen" / "commands"


def get_local_commands_dir() -> Path:
    """Get local OpenCode commands directory.

    Returns:
        Path to .opencode/commands/ in current directory.
    """
    return Path.cwd() / ".opencode" / "commands"


def get_local_qwen_commands_dir() -> Path:
    """Get local Qwen commands directory.

    Returns:
        Path to .qwen/commands/ in current directory.
    """
    return Path.cwd() / ".qwen" / "commands"


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
    templates = get_bundled_templates()

    if not templates:
        raise FileNotFoundError("No OpenCode templates found in package")

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
    overwritten = []

    for template_path in templates:
        target_path = target_dir / template_path.name

        if target_path.exists():
            if no_overwrite:
                skipped.append(template_path.name)
                continue
            else:
                overwritten.append(template_path.name)
        else:
            installed.append(template_path.name)

        # Copy the file
        shutil.copy2(template_path, target_path)

    return installed, skipped, overwritten


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
    templates = get_bundled_qwen_templates()

    if not templates:
        raise FileNotFoundError("No Qwen templates found in package")

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
    overwritten = []

    for template_path in templates:
        target_path = target_dir / template_path.name

        if target_path.exists():
            if no_overwrite:
                skipped.append(template_path.name)
                continue
            else:
                overwritten.append(template_path.name)
        else:
            installed.append(template_path.name)

        # Copy the file
        shutil.copy2(template_path, target_path)

    return installed, skipped, overwritten


def get_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each OpenCode template.

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
    templates = get_bundled_templates()
    global_dir = get_global_commands_dir()
    local_dir = get_local_commands_dir()

    status = {}

    for template_path in templates:
        name = template_path.name
        status[name] = {
            "global": (global_dir / name).exists(),
            "local": (local_dir / name).exists(),
        }

    return status


def get_qwen_installed_status() -> dict[str, dict[str, bool]]:
    """Get installation status of each Qwen template.

    Returns:
        Dict mapping template name to {"global": bool, "local": bool}
    """
    templates = get_bundled_qwen_templates()
    global_dir = get_global_qwen_commands_dir()
    local_dir = get_local_qwen_commands_dir()

    status = {}

    for template_path in templates:
        name = template_path.name
        status[name] = {
            "global": (global_dir / name).exists(),
            "local": (local_dir / name).exists(),
        }

    return status

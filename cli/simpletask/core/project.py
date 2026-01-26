"""Project management utilities for simpletask."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml

from ..utils.console import warning
from .git import current_branch, is_git_repo
from .yaml_parser import parse_task_file

# Constants
TASK_FILE_EXTENSION = ".yml"
_DOUBLEDOT_MARKER = "\x00DOUBLEDOT\x00"  # Internal: security marker during normalization


def normalize_branch_name(branch: str, max_length: int = 200) -> str:
    """Normalize branch name to a safe filename.

    Converts branch names to filesystem-safe filenames by:
    - Converting to lowercase
    - Replacing slashes and special characters with hyphens
    - Converting unicode to ASCII (NFD decomposition + ASCII filter)
    - Replacing .. with -- (security: prevent parent traversal)
    - Collapsing multiple hyphens to single
    - Trimming leading/trailing hyphens
    - Limiting length

    Args:
        branch: Git branch name
        max_length: Maximum filename length (default: 200)

    Returns:
        Normalized filename (without .yml extension)

    Raises:
        ValueError: If branch normalizes to empty string

    Examples:
        >>> normalize_branch_name("feature/user-auth")
        'feature-user-auth'
        >>> normalize_branch_name("Fix: Bug in <Module>")
        'fix-bug-in-module'
    """
    # Convert to lowercase
    normalized = branch.lower()

    # Convert unicode to ASCII (NFD decomposition + ASCII filter)
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")

    # Replace .. with special marker before other replacements (security: prevent parent traversal)
    # Use a character that won't be affected by other replacements
    normalized = normalized.replace("..", _DOUBLEDOT_MARKER)

    # Replace special characters and slashes with hyphens
    # Keep dots, underscores, and hyphens; replace everything else
    normalized = re.sub(r'[/\\:*?"<>|\s()[\]{}]', "-", normalized)

    # Collapse multiple hyphens to single
    normalized = re.sub(r"-+", "-", normalized)

    # Restore double dots as double dashes (after collapsing)
    normalized = normalized.replace(_DOUBLEDOT_MARKER, "--")

    # Trim leading/trailing hyphens (but not double dashes in middle)
    normalized = normalized.strip("-")

    # Limit length
    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip("-")

    # Ensure not empty
    if not normalized:
        raise ValueError(f"Branch name '{branch}' normalizes to empty string")

    return normalized


class Project:
    """Project management utilities."""

    def __init__(self, root: Path | None = None):
        """Initialize project with root path."""
        resolved_root = root or self._find_root()
        if not resolved_root:
            raise ValueError("Could not find project root. Not in a git repository.")
        self.root: Path = resolved_root

    @staticmethod
    def _find_root() -> Path | None:
        """Find project root by searching for .git directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return None

    @property
    def tasks_dir(self) -> Path:
        """Get tasks directory."""
        return self.root / ".tasks"

    def get_task_file(self, branch: str) -> Path:
        """Get task file path for a branch.

        Args:
            branch: Original branch name (will be normalized)

        Returns:
            Path to normalized task file (.tasks/<normalized-branch>.yml)
        """
        normalized = normalize_branch_name(branch)
        return self.tasks_dir / f"{normalized}{TASK_FILE_EXTENSION}"

    def has_task(self, branch: str) -> bool:
        """Check if task file exists for branch."""
        return self.get_task_file(branch).exists()

    def list_tasks(self) -> list[str]:
        """List all task branch names in project.

        Reads the 'branch' field from each YAML file to return original branch names,
        not normalized filenames.

        Optimized for performance: only parses the 'branch' field without full
        Pydantic validation to avoid expensive I/O during MCP server initialization.

        Returns:
            List of branch names (original, not normalized), sorted alphabetically
        """
        if not self.tasks_dir.exists():
            return []

        tasks = []
        for item in sorted(self.tasks_dir.iterdir()):
            if item.is_file() and item.suffix == TASK_FILE_EXTENSION:
                try:
                    # Lightweight parsing: only extract branch field
                    content = item.read_text(encoding="utf-8")
                    data = yaml.safe_load(content)
                    if isinstance(data, dict) and "branch" in data:
                        tasks.append(data["branch"])
                except Exception:
                    # Skip invalid files silently during lightweight listing
                    # Full validation happens when files are actually loaded
                    continue

        return sorted(tasks)

    def list_tasks_by_mtime(self) -> list[tuple[str, Path, datetime]]:
        """List all task branch names sorted by file modification time (oldest first).

        Reads the 'branch' field from each YAML file to return original branch names,
        not normalized filenames. Returns tuples of (branch_name, file_path, mtime)
        sorted by modification time in ascending order (oldest to newest).

        Optimized for performance: only parses the 'branch' field without full
        Pydantic validation to avoid expensive I/O.

        Returns:
            List of (branch_name, file_path, mtime) tuples, sorted by mtime ascending
        """
        if not self.tasks_dir.exists():
            return []

        tasks = []
        for item in self.tasks_dir.iterdir():
            if item.is_file() and item.suffix == TASK_FILE_EXTENSION:
                try:
                    # Lightweight parsing: only extract branch field
                    content = item.read_text(encoding="utf-8")
                    data = yaml.safe_load(content)
                    if isinstance(data, dict) and "branch" in data:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        tasks.append((data["branch"], item, mtime))
                except Exception:
                    # Skip invalid files silently during lightweight listing
                    # Full validation happens when files are actually loaded
                    continue

        # Sort by modification time (oldest first)
        return sorted(tasks, key=lambda x: x[2], reverse=False)

    def is_git_project(self) -> bool:
        """Check if project uses Git."""
        return is_git_repo(self.root)

    def ensure_tasks_dir(self) -> Path:
        """Ensure tasks directory exists, create if needed."""
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        return self.tasks_dir


def find_project() -> Project | None:
    """Find and return the current project."""
    root = Project._find_root()
    if root:
        try:
            return Project(root)
        except ValueError:
            pass
    return None


def ensure_project() -> Project:
    """Ensure project exists, find or raise error."""
    project = find_project()
    if not project:
        raise ValueError("Not in a git repository. Initialize git first: git init")
    return project


def get_task_file_path(branch: str | None = None) -> Path:
    """Get task file path, using git branch if not specified.

    Args:
        branch: Branch name, or None to use current git branch

    Returns:
        Path to task file

    Raises:
        ValueError: If branch is None and not in a git repo or detached HEAD
    """
    project = ensure_project()

    if branch is None:
        branch = current_branch()
        if branch is None:
            raise ValueError(
                "Not on a git branch (detached HEAD) or git not available. "
                "Use --branch flag to specify task file."
            )

    return project.get_task_file(branch)


# Export public API
__all__ = [
    "Project",
    "ensure_project",
    "find_project",
    "get_task_file_path",
    "normalize_branch_name",
]

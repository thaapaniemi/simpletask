"""Project management utilities for simpletask."""

from pathlib import Path

from .git import current_branch, is_git_repo


class Project:
    """Project management utilities."""

    def __init__(self, root: Path | None = None):
        """Initialize project with root path."""
        self.root = root or self._find_root()
        if not self.root:
            raise ValueError("Could not find project root. Not in a git repository.")

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
        """Get task file path for a branch."""
        return self.tasks_dir / f"{branch}.yml"

    def has_task(self, branch: str) -> bool:
        """Check if task file exists for branch."""
        return self.get_task_file(branch).exists()

    def list_tasks(self) -> list[str]:
        """List all task branch names in project.

        Returns:
            List of branch names (without .yml extension)
        """
        if not self.tasks_dir.exists():
            return []

        tasks = []
        for item in sorted(self.tasks_dir.iterdir()):
            if item.is_file() and item.suffix == ".yml":
                tasks.append(item.stem)  # Remove .yml extension
        return tasks

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
    "find_project",
    "ensure_project",
    "get_task_file_path",
]

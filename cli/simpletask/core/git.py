"""Git operations for simpletask."""

from pathlib import Path

try:
    import git
    from git.exc import GitCommandError, InvalidGitRepositoryError

    GIT_AVAILABLE = True
except ImportError:
    git = None  # type: ignore
    GitCommandError = Exception  # type: ignore
    InvalidGitRepositoryError = Exception  # type: ignore
    GIT_AVAILABLE = False


def is_git_repo(path: Path | None = None) -> bool:
    """Check if current or specified path is a Git repository."""
    if not GIT_AVAILABLE:
        return False

    try:
        repo_path = path or Path.cwd()
        git.Repo(repo_path, search_parent_directories=True)
        return True
    except (InvalidGitRepositoryError, Exception):
        return False


def get_git_repo(path: Path | None = None) -> "git.Repo | None":
    """Get Git repository object."""
    if not GIT_AVAILABLE:
        return None

    try:
        repo_path = path or Path.cwd()
        return git.Repo(repo_path, search_parent_directories=True)
    except (InvalidGitRepositoryError, Exception):
        return None


def current_branch(repo_path: Path | None = None) -> str | None:
    """Get current branch name."""
    repo = get_git_repo(repo_path)
    if not repo:
        return None

    try:
        if repo.head.is_detached:
            return None
        return repo.active_branch.name
    except Exception:
        return None


def is_main_branch(branch_name: str | None = None) -> bool:
    """Check if current or specified branch is main/master."""
    if branch_name is None:
        branch_name = current_branch()

    if branch_name is None:
        return False

    return branch_name in ("main", "master")


def create_branch(branch_name: str, repo_path: Path | None = None) -> tuple[bool, str]:
    """Create and checkout a new branch.

    Returns:
        Tuple of (success, message)
    """
    repo = get_git_repo(repo_path)
    if not repo:
        return False, "Not a git repository"

    try:
        # Check if branch already exists
        if branch_name in repo.heads:
            return False, f"Branch '{branch_name}' already exists"

        # Create and checkout branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        return True, f"Created and checked out branch '{branch_name}'"
    except GitCommandError as e:
        return False, f"Git error: {e}"
    except Exception as e:
        return False, f"Error creating branch: {e}"


def branch_exists(branch_name: str, repo_path: Path | None = None) -> bool:
    """Check if branch exists locally."""
    repo = get_git_repo(repo_path)
    if not repo:
        return False

    return branch_name in repo.heads


# Export public API
__all__ = [
    "GIT_AVAILABLE",
    "branch_exists",
    "create_branch",
    "current_branch",
    "get_git_repo",
    "is_git_repo",
    "is_main_branch",
]

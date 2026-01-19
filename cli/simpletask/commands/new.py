"""New command - Create a new task file and git branch."""

import typer

from ..core.git import create_branch, current_branch, is_main_branch
from ..core.project import ensure_project
from ..core.task_file_ops import create_task_file
from ..utils.console import confirm, error, info, success, warning


def new(
    branch: str = typer.Argument(..., help="Branch name (also task identifier)"),
    prompt: str = typer.Argument(..., help="Original prompt/description for this task"),
    skip_confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
) -> None:
    """Create a new task file and git branch.

    Creates:
    - Task YAML file at ./.tasks/<branch>.yml
    - Git branch named <branch> (if in a git repo)

    Warns if not currently on main/master branch.

    Examples:
        simpletask new add-dark-mode "Add dark mode toggle to settings"
        simpletask new fix-login "Fix login bug with OAuth" -y
    """
    try:
        # Ensure we're in a project
        project = ensure_project()

        # Check if task already exists
        if project.has_task(branch):
            error(f"Task '{branch}' already exists at {project.get_task_file(branch)}")

        # Check current branch
        curr_branch = current_branch()
        if curr_branch and not is_main_branch(curr_branch):
            warning(
                f"Creating task from branch '{curr_branch}' instead of main/master.\n"
                f"         The new branch '{branch}' will be created from '{curr_branch}'."
            )
            if not skip_confirm:
                if not confirm("Continue?", default=True):
                    info("Cancelled")
                    raise typer.Exit(0)

        # Create task file using shared function
        title = prompt.split("\n")[0] if "\n" in prompt else prompt  # First line as title
        create_task_file(
            project=project,
            branch=branch,
            title=title,
            prompt=prompt,
            criteria=None,  # Will add placeholder AC1
        )

        # Get task file path for display
        task_file = project.get_task_file(branch)
        success(f"Created task file: {task_file.relative_to(project.root)}")

        # Create git branch
        if project.is_git_project():
            branch_success, branch_msg = create_branch(branch, project.root)
            if branch_success:
                success(f"Created and checked out git branch: {branch}")
            else:
                warning(f"Could not create git branch: {branch_msg}")
        else:
            info("Not in a git repository - skipping branch creation")

        # Next steps
        info(
            f"\nNext steps:\n"
            f"  1. Edit {task_file.relative_to(project.root)} to add acceptance criteria\n"
            f"  2. Add implementation tasks with: simpletask task add <name>\n"
            f"  3. Check status with: simpletask status"
        )

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")

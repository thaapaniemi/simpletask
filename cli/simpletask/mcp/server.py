"""MCP server implementation for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

from mcp.server.fastmcp import FastMCP

from ..core.project import ensure_project, get_task_file_path
from ..core.validation import validate_task_file
from ..core.yaml_parser import parse_task_file
from .models import SimpleTaskGetResponse, ValidationResult, compute_status_summary

# Initialize FastMCP server
mcp = FastMCP("simpletask")

__all__ = ["mcp", "run_server", "simpletask_get", "simpletask_list"]


@mcp.tool()
def simpletask_get(
    branch: str | None = None,
    validate: bool = False,
) -> SimpleTaskGetResponse:
    """Get complete task specification with status summary.

    Returns the full task specification from .tasks/<branch>.yml with
    pre-computed status counts. Optionally validates against JSON schema.

    Args:
        branch: Branch name, or None to use current git branch. The branch name
                will be normalized to a safe filename (e.g., 'feature/auth' -> 'feature-auth.yml').
        validate: Whether to include schema validation result (default: False).
                  Opt-in to reduce overhead for simple queries.

    Returns:
        SimpleTaskGetResponse with spec, file_path, summary, and optional validation.

    Raises:
        ValueError: If not in a git repository, or branch is None and not on a git branch.
        FileNotFoundError: If task file doesn't exist for the specified branch.
        InvalidTaskFileError: If YAML file is malformed or invalid.
    """
    # Get file path (normalizes branch name and validates git repo)
    file_path = get_task_file_path(branch)

    # Parse task file
    spec = parse_task_file(file_path)

    # Compute status summary
    summary = compute_status_summary(spec)

    # Optionally validate
    validation = None
    if validate:
        errors = validate_task_file(file_path)
        validation = ValidationResult(valid=len(errors) == 0, errors=errors)

    return SimpleTaskGetResponse(
        spec=spec,
        file_path=str(file_path),
        summary=summary,
        validation=validation,
    )


@mcp.tool()
def simpletask_list() -> list[str]:
    """List all task file branch names in the project.

    Returns the original branch names (not normalized filenames) from
    all task files in .tasks/ directory.

    Returns:
        List of branch names, sorted alphabetically.

    Raises:
        ValueError: If not in a git repository.
    """
    project = ensure_project()
    return project.list_tasks()


def run_server() -> None:
    """Run the MCP server on stdio transport.

    This is the entry point called by the 'simpletask serve' command.
    The server runs until the client disconnects or the process is terminated.
    """
    mcp.run()

"""Task file operations for creating task files."""

from datetime import UTC, datetime

from .models import AcceptanceCriterion, SimpleTaskSpec
from .project import Project
from .yaml_parser import write_task_file

# Default description for acceptance criterion when none are provided
DEFAULT_CRITERION_DESCRIPTION = "All tasks completed and quality checks pass"


def create_task_file(
    project: Project,
    branch: str,
    title: str,
    prompt: str,
    criteria: list[str] | None = None,
) -> SimpleTaskSpec:
    """Create a new task file without git branch creation.

    Args:
        project: Project instance
        branch: Branch/task identifier
        title: Human-readable task title
        prompt: Original user prompt/request
        criteria: Optional list of acceptance criteria descriptions.
                 None or [] adds default criterion.

    Returns:
        The created SimpleTaskSpec

    Raises:
        ValueError: If task file already exists for branch
    """
    if project.has_task(branch):
        raise ValueError(f"Task '{branch}' already exists")

    # Build acceptance criteria
    if criteria:
        ac_list = [
            AcceptanceCriterion(id=f"AC{i + 1}", description=desc, completed=False)
            for i, desc in enumerate(criteria)
        ]
    else:
        # None or empty list both get default criterion
        ac_list = [
            AcceptanceCriterion(
                id="AC1",
                description=DEFAULT_CRITERION_DESCRIPTION,
                completed=False,
            )
        ]

    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch=branch,
        title=title,
        original_prompt=prompt,
        created=datetime.now(UTC),
        acceptance_criteria=ac_list,
        constraints=None,
        context=None,
        tasks=None,
    )

    project.ensure_tasks_dir()
    task_file = project.get_task_file(branch)
    write_task_file(task_file, spec)

    return spec

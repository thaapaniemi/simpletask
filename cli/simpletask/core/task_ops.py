"""Task operations for CRUD on implementation tasks in task files."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from .models import CodeExample, FileAction, SimpleTaskSpec, Task, TaskStatus
from .repair import repair_task_file
from .yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file

if TYPE_CHECKING:
    from ..mcp.models import BatchTaskOperation


class _UnsetType:
    """Singleton sentinel to distinguish 'not provided' from 'explicitly set to None'.

    Using a typed singleton rather than a bare object() ensures that mypy can
    reason about the sentinel throughout the call chain without requiring cast().
    """

    _instance: "_UnsetType | None" = None

    def __new__(cls) -> "_UnsetType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


_UNSET = _UnsetType()


def get_next_task_id(tasks: list[Task]) -> str:
    """Generate next sequential task ID.

    Args:
        tasks: Existing tasks

    Returns:
        Next task ID (e.g., "T003")
    """
    if not tasks:
        return "T001"
    max_num = max(int(t.id[1:]) for t in tasks)
    return f"T{max_num + 1:03d}"


def add_implementation_task(
    file_path: Path,
    name: str,
    goal: str | None = None,
    status: TaskStatus = TaskStatus.NOT_STARTED,
    steps: list[str] | None = None,
    done_when: list[str] | None = None,
    prerequisites: list[str] | None = None,
    files: list[FileAction] | None = None,
    code_examples: list[CodeExample] | None = None,
    iteration: int | None = None,
) -> tuple[str, SimpleTaskSpec]:
    """Add a new implementation task to the task file.

    Args:
        file_path: Path to task YAML file
        name: Task name
        goal: Optional task goal/description (defaults to name if not provided)
        status: Initial status (default: not_started)
        steps: Optional list of task steps. None or [] adds placeholder step.
        done_when: Optional list of completion verification conditions
        prerequisites: Optional list of prerequisite task IDs
        files: Optional list of FileAction objects specifying files to modify
        code_examples: Optional list of CodeExample objects with implementation patterns
        iteration: Optional iteration ID to assign this task to

    Returns:
        Tuple of (new task ID, updated SimpleTaskSpec in-memory)

    Raises:
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file cannot be repaired
    """
    # Parse existing file (with automatic repair if needed)
    try:
        spec = parse_task_file(file_path)
    except InvalidTaskFileError:
        # Attempt automatic repair for common issues
        spec = repair_task_file(file_path)

    # Default goal to name if not provided
    if goal is None:
        goal = name

    # Default steps to placeholder if not provided or empty
    if not steps:
        steps = ["To be defined"]

    # Generate new ID
    tasks = spec.tasks or []
    new_id = get_next_task_id(tasks)

    # Create new task with required fields
    new_task = Task(
        id=new_id,
        name=name,
        goal=goal,
        status=status,
        steps=steps,
        done_when=done_when,
        prerequisites=prerequisites,
        files=files,
        code_examples=code_examples,
        notes=None,
        iteration=iteration,
    )

    # Append task
    if spec.tasks is None:
        spec.tasks = []
    spec.tasks.append(new_task)

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)

    return new_id, spec


def update_implementation_task(
    file_path: Path,
    task_id: str,
    name: str | None = None,
    goal: str | None = None,
    status: TaskStatus | None = None,
    steps: list[str] | None = None,
    done_when: list[str] | None = None,
    prerequisites: list[str] | None = None,
    files: list[FileAction] | None = None,
    code_examples: list[CodeExample] | None = None,
    iteration: int | None | _UnsetType = _UNSET,
) -> SimpleTaskSpec:
    """Update an existing implementation task.

    Args:
        file_path: Path to task YAML file
        task_id: Task ID to update
        name: New name (optional)
        goal: New goal (optional)
        status: New status (optional)
        steps: New steps list (optional, replaces existing)
        done_when: New completion conditions (optional, replaces existing)
        prerequisites: New prerequisite list (optional, replaces existing)
        files: New files list (optional, replaces existing)
        code_examples: New code examples list (optional, replaces existing)
        iteration: Iteration ID to assign (int), None to unassign, or _UNSET to
            preserve the existing value (default).

    Returns:
        Updated SimpleTaskSpec in-memory (after write)

    Raises:
        ValueError: If task not found
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file cannot be repaired
    """
    # Parse existing file (with automatic repair if needed)
    try:
        spec = parse_task_file(file_path)
    except InvalidTaskFileError:
        # Attempt automatic repair for common issues
        spec = repair_task_file(file_path)

    if not spec.tasks:
        raise ValueError(f"No tasks defined in {file_path}")

    # Find task
    task = next((t for t in spec.tasks if t.id == task_id), None)
    if not task:
        available = [t.id for t in spec.tasks]
        raise ValueError(f"Task {task_id} not found. Available: {available}")

    # Update fields
    if name is not None:
        task.name = name
    if goal is not None:
        task.goal = goal
    if status is not None:
        task.status = status
    if steps is not None:
        task.steps = steps
    if done_when is not None:
        task.done_when = done_when
    if prerequisites is not None:
        task.prerequisites = prerequisites
    if files is not None:
        task.files = files
    if code_examples is not None:
        task.code_examples = code_examples
    if not isinstance(iteration, _UnsetType):
        task.iteration = iteration  # type: ignore[assignment]  # narrowed to int | None

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)

    return spec


def remove_implementation_task(
    file_path: Path,
    task_id: str,
) -> SimpleTaskSpec:
    """Remove an implementation task.

    Args:
        file_path: Path to task YAML file
        task_id: Task ID to remove

    Returns:
        Updated SimpleTaskSpec in-memory (after write)

    Raises:
        ValueError: If task not found
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file cannot be repaired
    """
    # Parse existing file (with automatic repair if needed)
    try:
        spec = parse_task_file(file_path)
    except InvalidTaskFileError:
        # Attempt automatic repair for common issues
        spec = repair_task_file(file_path)

    if not spec.tasks:
        raise ValueError(f"No tasks defined in {file_path}")

    # Find task index
    task_index = next((i for i, t in enumerate(spec.tasks) if t.id == task_id), None)
    if task_index is None:
        available = [t.id for t in spec.tasks]
        raise ValueError(f"Task {task_id} not found. Available: {available}")

    # Remove task
    removed_id = spec.tasks[task_index].id
    del spec.tasks[task_index]

    # Clean up prerequisite references to the removed task
    for task in spec.tasks:
        if task.prerequisites:
            task.prerequisites = [p for p in task.prerequisites if p != removed_id]
            if not task.prerequisites:  # Clean up empty list
                task.prerequisites = None

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)

    return spec


def batch_tasks(
    file_path: Path, operations: list[Union[dict[str, Any], "BatchTaskOperation"]]
) -> tuple[list[str], SimpleTaskSpec]:
    """Perform multiple task operations atomically.

    All operations are performed in memory before writing. If any operation
    fails, none of the changes are written to disk.

    Args:
        file_path: Path to task YAML file
        operations: List of BatchTaskOperation dicts or objects

    Returns:
        Tuple of (list of newly created task IDs, updated SimpleTaskSpec in-memory)

    Raises:
        ValueError: If any operation fails validation
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file cannot be repaired
    """
    # Parse existing file (with automatic repair if needed)
    try:
        spec = parse_task_file(file_path)
    except InvalidTaskFileError:
        # Attempt automatic repair for common issues
        spec = repair_task_file(file_path)

    # Ensure tasks list exists
    if spec.tasks is None:
        spec.tasks = []

    # Convert all operations to dicts once upfront for efficiency
    ops_as_dicts: list[dict[str, Any]] = [
        op if isinstance(op, dict) else op.model_dump(exclude_unset=True)  # type: ignore[union-attr]
        for op in operations
    ]

    # Validate all operations upfront (fail fast before making any changes)
    existing_task_ids = {t.id for t in spec.tasks}
    remove_ids = {
        op_dict.get("task_id") for op_dict in ops_as_dicts if op_dict.get("op") == "remove"
    }

    for i, op_dict in enumerate(ops_as_dicts):
        op_type = op_dict.get("op")
        task_id = op_dict.get("task_id")

        # Validate remove/update operations have existing task_id
        if op_type in ("remove", "update"):
            if not task_id:
                raise ValueError(f"Operation {i}: task_id required for {op_type}")
            if task_id not in existing_task_ids:
                raise ValueError(
                    f"Operation {i}: task {task_id} not found. "
                    f"Available: {sorted(existing_task_ids)}"
                )

        # Critical: Detect remove+update conflicts
        if op_type == "update":
            if task_id in remove_ids:
                raise ValueError(
                    f"Operation {i}: Cannot update task {task_id} - "
                    f"it is being removed in the same batch"
                )

        # Validate add operations have name
        if op_type == "add":
            if not op_dict.get("name"):
                raise ValueError(f"Operation {i}: name required for add operation")

        # Validate prerequisites for update operations
        if op_type == "update" and op_dict.get("prerequisites") is not None:
            valid_task_ids = existing_task_ids - remove_ids
            for prereq_id in op_dict["prerequisites"]:
                if prereq_id not in valid_task_ids:
                    raise ValueError(
                        f"Operation {i}: Invalid prerequisite '{prereq_id}' - "
                        f"task does not exist. Available: {sorted(valid_task_ids)}"
                    )

        # Validate iteration ID for update operations
        if op_type == "update" and "iteration" in op_dict and op_dict["iteration"] is not None:
            valid_iteration_ids = {it.id for it in (spec.iterations or [])}
            if op_dict["iteration"] not in valid_iteration_ids:
                raise ValueError(
                    f"Operation {i}: Invalid iteration '{op_dict['iteration']}' - "
                    f"iteration does not exist. Available: {sorted(valid_iteration_ids)}"
                )

        # Validate status values for update operations
        if op_type == "update" and op_dict.get("status") is not None:
            try:
                TaskStatus(op_dict["status"])
            except ValueError:
                valid = [s.value for s in TaskStatus]
                raise ValueError(
                    f"Operation {i}: Invalid status '{op_dict['status']}'. Valid values: {valid}"
                ) from None

    # Process remove operations (single-pass optimization)
    if remove_ids:
        spec.tasks = [t for t in spec.tasks if t.id not in remove_ids]

        # Clean up prerequisite references to removed tasks
        for task in spec.tasks:
            if task.prerequisites:
                task.prerequisites = [p for p in task.prerequisites if p not in remove_ids]
                if not task.prerequisites:  # Clean up empty list
                    task.prerequisites = None

    # Process update operations
    for op_dict in ops_as_dicts:
        if op_dict.get("op") == "update":
            task_id = op_dict["task_id"]
            # Find task
            task_maybe = next((t for t in spec.tasks if t.id == task_id), None)
            if not task_maybe:  # Should not happen due to validation
                continue
            task = task_maybe

            # Update fields if provided
            if op_dict.get("name") is not None:
                task.name = op_dict["name"]
            if op_dict.get("goal") is not None:
                task.goal = op_dict["goal"]
            if op_dict.get("status") is not None:
                task.status = TaskStatus(op_dict["status"])

            # Update new fields if provided
            if op_dict.get("steps") is not None:
                task.steps = op_dict["steps"]
            if op_dict.get("done_when") is not None:
                task.done_when = op_dict["done_when"]
            if op_dict.get("prerequisites") is not None:
                task.prerequisites = op_dict["prerequisites"]

            # Update files field with conversion
            if op_dict.get("files") is not None:
                task.files = [FileAction(**f) for f in op_dict["files"]]

            # Update code_examples field with conversion
            if op_dict.get("code_examples") is not None:
                task.code_examples = [CodeExample(**c) for c in op_dict["code_examples"]]

            # Update iteration field if provided (None means unassign)
            if "iteration" in op_dict:
                task.iteration = op_dict["iteration"]

    # Process add operations
    new_task_ids: list[str] = []
    for i, op_dict in enumerate(ops_as_dicts):
        if op_dict.get("op") == "add":
            # Generate new task ID
            new_id = get_next_task_id(spec.tasks)

            # Default goal to name if not provided
            goal = op_dict.get("goal") or op_dict["name"]

            # Default steps to placeholder if not provided or empty
            steps = op_dict.get("steps")
            if not steps:
                steps = ["To be defined"]

            # Extract new fields
            done_when = op_dict.get("done_when")
            prerequisites = op_dict.get("prerequisites")

            # Validate prerequisites reference existing or newly-added task IDs
            if prerequisites:
                # Build set of all valid task IDs: existing + already added in this batch
                valid_task_ids = existing_task_ids | (set(new_task_ids) - remove_ids)
                for prereq_id in prerequisites:
                    if prereq_id not in valid_task_ids:
                        raise ValueError(
                            f"Operation {i}: Invalid prerequisite '{prereq_id}' - "
                            f"task does not exist. Available: {sorted(valid_task_ids)}"
                        )

            # Validate iteration ID for add operations
            iteration_id = op_dict.get("iteration")
            if iteration_id is not None:
                valid_iteration_ids = {it.id for it in (spec.iterations or [])}
                if iteration_id not in valid_iteration_ids:
                    raise ValueError(
                        f"Operation {i}: Invalid iteration '{iteration_id}' - "
                        f"iteration does not exist. Available: {sorted(valid_iteration_ids)}"
                    )

            # Convert files list[dict] to list[FileAction]
            files = None
            if op_dict.get("files"):
                files = [FileAction(**f) for f in op_dict["files"]]

            # Convert code_examples list[dict] to list[CodeExample]
            code_examples = None
            if op_dict.get("code_examples"):
                code_examples = [CodeExample(**c) for c in op_dict["code_examples"]]

            # Create new task
            new_task = Task(
                id=new_id,
                name=op_dict["name"],
                goal=goal,
                status=TaskStatus.NOT_STARTED,
                steps=steps,
                done_when=done_when,
                prerequisites=prerequisites,
                files=files,
                code_examples=code_examples,
                notes=None,
                iteration=op_dict.get("iteration"),
            )

            spec.tasks.append(new_task)
            new_task_ids.append(new_id)

    # Write back atomically (single write after all operations succeed)
    write_task_file(file_path, spec)

    return new_task_ids, spec

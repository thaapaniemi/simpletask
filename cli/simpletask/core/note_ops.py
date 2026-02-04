"""Note operations for simpletask.

This module provides CRUD operations for both root-level and task-level notes.
"""

from .models import SimpleTaskSpec


def add_note(
    spec: SimpleTaskSpec,
    content: str,
    task_id: str | None = None,
) -> SimpleTaskSpec:
    """Add a note to root-level or task-level notes.

    Args:
        spec: The task specification to modify
        content: The note content to add
        task_id: Optional task ID. If provided, adds note to task; otherwise adds to root

    Returns:
        Modified SimpleTaskSpec with the note added

    Raises:
        ValueError: If task_id is provided but task not found
    """
    if task_id is None:
        # Add to root-level notes
        if spec.notes is None:
            spec.notes = []
        spec.notes.append(content)
    else:
        # Add to task-level notes
        if spec.tasks is None:
            raise ValueError("No tasks defined in spec")

        task = next((t for t in spec.tasks if t.id == task_id), None)
        if task is None:
            raise ValueError(f"Task '{task_id}' not found")

        if task.notes is None:
            task.notes = []
        task.notes.append(content)

    return spec


def remove_note(
    spec: SimpleTaskSpec,
    index: int | None = None,
    task_id: str | None = None,
    all: bool = False,
) -> SimpleTaskSpec:
    """Remove notes from root-level or task-level.

    Args:
        spec: The task specification to modify
        index: Optional index of note to remove (0-based)
        task_id: Optional task ID. If provided, removes from task; otherwise from root
        all: If True, removes all notes

    Returns:
        Modified SimpleTaskSpec with note(s) removed

    Raises:
        ValueError: If task_id provided but task not found, or if index is invalid
    """
    if task_id is None:
        # Remove from root-level notes
        if all:
            spec.notes = None
        elif index is not None:
            if spec.notes is None or index < 0 or index >= len(spec.notes):
                if spec.notes is None:
                    raise ValueError(f"Invalid note index: {index}. No notes exist.")
                raise ValueError(
                    f"Invalid note index: {index}. Valid range: 0-{len(spec.notes) - 1}"
                )
            spec.notes.pop(index)
            # Set to None if empty
            if not spec.notes:
                spec.notes = None
        else:
            raise ValueError("Must provide either index or all=True")
    else:
        # Remove from task-level notes
        if spec.tasks is None:
            raise ValueError("No tasks defined in spec")

        task = next((t for t in spec.tasks if t.id == task_id), None)
        if task is None:
            raise ValueError(f"Task '{task_id}' not found")

        if all:
            task.notes = None
        elif index is not None:
            if task.notes is None or index < 0 or index >= len(task.notes):
                if task.notes is None:
                    raise ValueError(
                        f"Invalid note index: {index} for task {task_id}. No notes exist."
                    )
                raise ValueError(
                    f"Invalid note index: {index} for task {task_id}. "
                    f"Valid range: 0-{len(task.notes) - 1}"
                )
            task.notes.pop(index)
            # Set to None if empty
            if not task.notes:
                task.notes = None
        else:
            raise ValueError("Must provide either index or all=True")

    return spec


def list_notes(
    spec: SimpleTaskSpec,
    task_id: str | None = None,
    root_only: bool = False,
) -> tuple[list[str] | None, dict[str, list[str]]]:
    """List notes from root-level and/or task-level.

    Args:
        spec: The task specification to read from
        task_id: Optional task ID. If provided, only returns notes for that task
        root_only: If True, only returns root-level notes

    Returns:
        Tuple of (root_notes, task_notes_dict) where:
        - root_notes: list of root-level notes or None
        - task_notes_dict: dict mapping task_id to list of notes (sparse, only tasks with notes)

    Raises:
        ValueError: If task_id provided but task not found
    """
    root_notes = spec.notes

    if root_only:
        return (root_notes, {})

    task_notes_dict: dict[str, list[str]] = {}

    if task_id is not None:
        # Return notes for specific task only
        if spec.tasks is None:
            raise ValueError("No tasks defined in spec")

        task = next((t for t in spec.tasks if t.id == task_id), None)
        if task is None:
            raise ValueError(f"Task '{task_id}' not found")

        if task.notes is not None:
            task_notes_dict[task.id] = task.notes
    else:
        # Return notes for all tasks that have notes
        if spec.tasks is not None:
            for task in spec.tasks:
                if task.notes is not None:
                    task_notes_dict[task.id] = task.notes

    return (root_notes, task_notes_dict)

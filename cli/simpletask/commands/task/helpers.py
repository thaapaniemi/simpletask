"""Shared helpers for task CLI commands."""

from simpletask.core.models import FileAction

VALID_FILE_ACTIONS = {"create", "modify", "delete"}


def _parse_file_actions(files: list[str]) -> list[FileAction]:
    """Parse --file arguments into FileAction objects.

    Args:
        files: List of file specifications in 'path:action' format.

    Returns:
        List of FileAction objects.

    Raises:
        ValueError: If any entry has invalid format or unknown action.
    """
    if not files:
        return []

    parsed = []
    for entry in files:
        parts = entry.rsplit(":", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid --file format '{entry}': expected path:action "
                f"where action is one of {sorted(VALID_FILE_ACTIONS)}"
            )

        path, action = parts
        if action not in VALID_FILE_ACTIONS:
            raise ValueError(
                f"Invalid --file format '{entry}': expected path:action "
                f"where action is one of {sorted(VALID_FILE_ACTIONS)}"
            )

        parsed.append(FileAction(path=path, action=action))

    return parsed

"""Output format utilities for CLI commands."""

import json
import sys
from enum import Enum

from simpletask.utils.console import console


class OutputFormat(str, Enum):
    """Output format options for CLI commands."""

    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"


def resolve_format(fmt: OutputFormat) -> OutputFormat:
    """Resolve output format, auto-downgrading RICH to PLAIN when not in a terminal.

    Args:
        fmt: The requested output format.

    Returns:
        PLAIN if fmt is RICH and not in a terminal, otherwise fmt unchanged.
    """
    if fmt == OutputFormat.RICH and not console.is_terminal:
        return OutputFormat.PLAIN
    return fmt


def json_error(message: str) -> None:
    """Print an error as valid JSON to stderr.

    Args:
        message: Error message to include in the JSON object.
    """
    output = {"success": False, "message": message}
    print(json.dumps(output, indent=2), file=sys.stderr)


def json_success(data: dict) -> None:
    """Print a success response as valid JSON to stdout.

    Args:
        data: Dictionary to serialize as JSON.
    """
    print(json.dumps(data, indent=2))


def build_task_summary(spec) -> dict:
    """Build a complete status summary dict from a SimpleTaskSpec.

    Args:
        spec: SimpleTaskSpec instance.

    Returns:
        Dict with all task status counts and criteria counts.
    """
    tasks = spec.tasks or []
    criteria = spec.acceptance_criteria or []
    return {
        "tasks_total": len(tasks),
        "tasks_completed": sum(1 for t in tasks if t.status.value == "completed"),
        "tasks_not_started": sum(1 for t in tasks if t.status.value == "not_started"),
        "tasks_in_progress": sum(1 for t in tasks if t.status.value == "in_progress"),
        "tasks_blocked": sum(1 for t in tasks if t.status.value == "blocked"),
        "tasks_paused": sum(1 for t in tasks if t.status.value == "paused"),
        "criteria_total": len(criteria),
        "criteria_completed": sum(1 for c in criteria if c.completed),
    }


def build_write_response(action: str, message: str, spec, file_path: str, **extra) -> dict:
    """Build a standard write command JSON response dict.

    Args:
        action: Action string (e.g., 'task_added', 'criterion_removed').
        message: Human-readable success message.
        spec: SimpleTaskSpec instance used to compute the summary.
        file_path: Path to the task file.
        **extra: Additional key-value pairs inserted after 'action' (e.g., task_id).

    Returns:
        Dict ready for json_success().
    """
    response: dict = {"success": True, "action": action}
    response.update(extra)
    response["message"] = message
    response["file_path"] = file_path
    response["summary"] = build_task_summary(spec)
    return response


def serialize_quality_reqs(quality_reqs) -> dict:
    """Serialize a QualityRequirements object to a JSON-serializable dict.

    Args:
        quality_reqs: QualityRequirements instance to serialize.

    Returns:
        Dictionary representation suitable for JSON output.
    """
    return {
        "linting": {
            "enabled": quality_reqs.linting.enabled,
            "tool": quality_reqs.linting.tool.value if quality_reqs.linting.tool else None,
            "args": quality_reqs.linting.args,
        },
        "type_checking": (
            {
                "enabled": quality_reqs.type_checking.enabled,
                "tool": (
                    quality_reqs.type_checking.tool.value
                    if quality_reqs.type_checking.tool
                    else None
                ),
                "args": quality_reqs.type_checking.args,
            }
            if quality_reqs.type_checking
            else None
        ),
        "testing": (
            {
                "enabled": quality_reqs.testing.enabled,
                "tool": quality_reqs.testing.tool.value if quality_reqs.testing.tool else None,
                "args": quality_reqs.testing.args,
                "min_coverage": quality_reqs.testing.min_coverage,
            }
            if quality_reqs.testing
            else None
        ),
        "security_check": (
            {
                "enabled": quality_reqs.security_check.enabled,
                "tool": (
                    quality_reqs.security_check.tool.value
                    if quality_reqs.security_check.tool
                    else None
                ),
                "args": quality_reqs.security_check.args,
            }
            if quality_reqs.security_check
            else None
        ),
    }


__all__ = [
    "OutputFormat",
    "build_task_summary",
    "build_write_response",
    "json_error",
    "json_success",
    "resolve_format",
    "serialize_quality_reqs",
]

"""MCP server module for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

from .models import SimpleTaskGetResponse, StatusSummary, ValidationResult
from .server import criteria, get, list, mcp, new, run_server, task

__all__ = [
    "SimpleTaskGetResponse",
    "StatusSummary",
    "ValidationResult",
    "criteria",
    "get",
    "list",
    "mcp",
    "new",
    "run_server",
    "task",
]

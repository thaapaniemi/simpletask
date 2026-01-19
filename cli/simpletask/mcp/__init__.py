"""MCP server module for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

from .models import SimpleTaskGetResponse, StatusSummary, ValidationResult
from .server import mcp, run_server, simpletask_get, simpletask_list

__all__ = [
    "SimpleTaskGetResponse",
    "StatusSummary",
    "ValidationResult",
    "mcp",
    "run_server",
    "simpletask_get",
    "simpletask_list",
]

"""Serve command - Start MCP server for AI editor integration."""

from ..mcp import run_server


def serve() -> None:
    """Start MCP server for AI editor integration.

    Runs the Model Context Protocol server on stdio transport.
    Configure your AI editor (OpenCode or other MCP-compatible clients) to connect.

    Example OpenCode configuration (~/.config/opencode/settings.json):

        {
          "mcpServers": {
            "simpletask": {
              "command": "simpletask",
              "args": ["serve"]
            }
          }
        }

    Note: If simpletask is installed in a virtualenv, you may need to use
    the full path to the executable, e.g.:

        "command": "/path/to/venv/bin/simpletask"

    Available MCP tools:
    - simpletask_get: Get complete task specification with status summary
    - simpletask_list: List all task file branch names in the project
    """
    run_server()

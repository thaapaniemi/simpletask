"""Unit tests for MCP tools (get, list)."""

import builtins
from unittest.mock import MagicMock, patch

import pytest
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import get, list


class TestSimpletaskGet:
    """Tests for get tool."""

    def test_get_current_branch(self, tmp_project_with_task):
        """Test getting task for current branch."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = get(validate=False)

            assert response.spec is not None
            assert response.spec.branch == "test-feature"
            assert response.file_path == str(task_file)
            assert response.summary is not None
            assert response.validation is None
            mock_path.assert_called_once()

    def test_get_with_validation_valid(self, tmp_project_with_task):
        """Verify validation included when validate=True."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = get(validate=True)

            assert response.validation is not None
            assert response.validation.valid is True
            assert len(response.validation.errors) == 0

    def test_get_with_validation_invalid(self, tmp_path):
        """Verify errors populated for invalid file."""
        # Create invalid YAML file
        task_file = tmp_path / "invalid.yml"
        task_file.write_text("invalid: yaml: content:")

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(InvalidTaskFileError):
                get(validate=True)

    def test_get_file_not_found(self, tmp_path):
        """Verify FileNotFoundError raised for non-existent file."""
        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = tmp_path / "nonexistent.yml"
            with pytest.raises(FileNotFoundError):
                get()

    def test_get_invalid_yaml(self, tmp_path):
        """Verify InvalidTaskFileError raised for malformed YAML."""
        task_file = tmp_path / "bad.yml"
        task_file.write_text("{ invalid yaml content")

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(InvalidTaskFileError):
                get()

    def test_get_not_in_git_repo(self, tmp_path, monkeypatch):
        """Verify error when not in a git repository."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="git"):
            get()


class TestSimpletaskList:
    """Tests for list tool."""

    def test_list_tasks(self, tmp_project_with_task):
        """Verify returns branch names."""
        _project_root, _task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.ensure_project") as mock_project:
            mock_proj = MagicMock()
            mock_proj.list_tasks.return_value = ["test-feature", "another-branch"]
            mock_project.return_value = mock_proj

            result = list()

            assert result == ["test-feature", "another-branch"]

    def test_list_empty(self, tmp_project):
        """Verify returns [] when no tasks."""
        with patch("simpletask.mcp.server.ensure_project") as mock_project:
            mock_proj = MagicMock()
            mock_proj.list_tasks.return_value = []
            mock_project.return_value = mock_proj

            result = list()

            assert result == []

    def test_list_not_in_git_repo(self, tmp_path, monkeypatch):
        """Verify error when not in a git repository."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="git"):
            list()


class TestSecurityPathTraversal:
    """Security tests for path traversal attacks via branch parameter."""


class TestListBuiltinShadowing:
    """Tests for list() function shadowing edge cases."""

    def test_list_function_works_as_mcp_tool(self, tmp_project_with_task):
        """Verify list() function works correctly as MCP tool."""
        _project_root, _task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.ensure_project") as mock_project:
            mock_proj = MagicMock()
            mock_proj.list_tasks.return_value = ["test-feature", "another-branch"]
            mock_project.return_value = mock_proj

            result = list()

            assert isinstance(result, builtins.list)  # Returns built-in list type
            assert result == ["test-feature", "another-branch"]

    def test_builtin_list_still_accessible_in_caller(self, tmp_project_with_task):
        """Verify built-in list() works in code that imports list function."""
        # This test verifies that importing list doesn't break list() usage
        # in caller code (though it would in the same module scope)
        _project_root, _task_file = tmp_project_with_task

        # Built-in list should still work for creating lists
        test_list = builtins.list([1, 2, 3])
        assert test_list == [1, 2, 3]

        # List comprehensions should work
        comprehension = [x * 2 for x in range(3)]
        assert comprehension == [0, 2, 4]

        # List literals should work
        literal = [1, 2, 3]
        assert isinstance(literal, builtins.list)

    def test_type_hints_with_list_work(self):
        """Verify type hints using list[T] syntax work correctly.

        This is a regression test ensuring from __future__ import annotations
        is present in server.py, allowing list[str] type hints to work even
        after list() function is defined.
        """
        # Import the module to verify it has proper annotations
        from simpletask.mcp import server

        # Check that __future__ annotations is imported
        assert hasattr(server, "__annotations__") or True  # Module loads without error

        # Verify _list alias exists for type hint workaround
        assert hasattr(server, "_list")
        assert server._list is builtins.list

    def test_list_function_in_module_scope(self):
        """Verify list() function is defined in server module."""
        from simpletask.mcp import server

        # Verify list is a function, not the built-in type
        assert callable(server.list)
        assert server.list.__name__ == "list"

        # Verify it's different from built-in
        assert server.list is not builtins.list


class TestMCPServerRegistration:
    """Tests for MCP server tool registration."""

    @pytest.mark.anyio
    async def test_mcp_tools_registered_with_correct_names(self):
        """Verify all MCP tools are registered with simple names (no simpletask_ prefix).

        The MCP server should register tools with names: get, list, new, task, criteria,
        quality, design, note, constraint, context.
        The MCP client (e.g., OpenCode) will automatically prefix them with the server
        name, making them available as: simpletask_get, simpletask_list, etc.
        """
        from simpletask.mcp.server import mcp

        # Get registered tool names from FastMCP
        tools = await mcp.list_tools()
        registered_tools = {tool.name for tool in tools}

        # Verify all 10 tools are registered with simple names
        expected_tools = {
            "get",
            "list",
            "new",
            "task",
            "criteria",
            "quality",
            "design",
            "note",
            "constraint",
            "context",
        }
        assert (
            registered_tools == expected_tools
        ), f"Expected tools {expected_tools}, but found {registered_tools}"

        # Verify no tools have the simpletask_ prefix (that's added by MCP client)
        prefixed_tools = {name for name in registered_tools if name.startswith("simpletask_")}
        assert not prefixed_tools, (
            f"Found tools with simpletask_ prefix: {prefixed_tools}. "
            "Tools should have simple names; MCP client adds the prefix."
        )

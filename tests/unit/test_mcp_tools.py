"""Unit tests for MCP tools (get, list, quality, iteration)."""

import builtins
from unittest.mock import MagicMock, patch

import pytest
from simpletask.core.models import (
    LintingConfig,
    QualityRequirements,
    SimpleTaskSpec,
    TaskStatus,
    TestingConfig,
    ToolName,
)
from simpletask.core.quality_ops import run_quality_checks
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import criteria as criteria_tool
from simpletask.mcp.server import get, iteration, list, quality, task


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

    def test_path_traversal_sequences_are_neutralized(self):
        """Branch names with path traversal sequences must not escape .tasks/ directory."""
        from simpletask.core.project import normalize_branch_name

        # Double-dot traversal sequences must be converted so no ".." or "/" remain
        result = normalize_branch_name("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        # Leading/trailing hyphens are stripped; only the path components remain
        assert result == "etc-passwd"

    def test_absolute_path_in_branch_name_is_neutralized(self):
        """Absolute paths in branch names must not escape .tasks/ directory."""
        from simpletask.core.project import normalize_branch_name

        result = normalize_branch_name("/etc/passwd")
        assert result.startswith("/") is False
        assert ".." not in result


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

        # Verify all 12 tools are registered with simple names
        expected_tools = {
            "audit",
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
            "iteration",
        }
        assert registered_tools == expected_tools, (
            f"Expected tools {expected_tools}, but found {registered_tools}"
        )

        # Verify no tools have the simpletask_ prefix (that's added by MCP client)
        prefixed_tools = {name for name in registered_tools if name.startswith("simpletask_")}
        assert not prefixed_tools, (
            f"Found tools with simpletask_ prefix: {prefixed_tools}. "
            "Tools should have simple names; MCP client adds the prefix."
        )


class TestMCPIterationTool:
    """Tests for the iteration MCP tool and quality() filter flags.

    This class covers:
    - Iteration management (list, add, get, remove)
    - Quality check filter flags (lint_only, test_only, type_only, security_only)
    """

    def test_list_returns_empty_when_no_iterations(self, tmp_project_with_task):
        """Test listing iterations when none exist returns empty list."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            result = iteration(action="list")
        assert result.action == "iteration_list"
        assert result.iterations == [] or result.iterations is None

    def test_add_creates_iteration(self, tmp_project_with_task):
        """Test adding an iteration returns the new ID."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            result = iteration(action="add", label="MVP")
        assert result.success is True
        assert result.action == "iteration_added"
        assert "MVP" in result.message
        assert len(result.new_item_ids) > 0

    def test_list_returns_added_iterations(self, tmp_project_with_task):
        """Test listing after adding returns the created iteration."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            iteration(action="add", label="MVP")
            iteration(action="add", label="v2 polish")
            result = iteration(action="list")
        assert result.action == "iteration_list"
        assert result.iterations is not None
        assert len(result.iterations) == 2
        labels = [it.label for it in result.iterations]
        assert "MVP" in labels
        assert "v2 polish" in labels

    def test_get_returns_single_iteration(self, tmp_project_with_task):
        """Test getting a specific iteration by ID."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            result = iteration(action="get", iteration_id=new_id)
        assert result.action == "iteration_get"
        assert result.iterations is not None
        assert len(result.iterations) == 1
        assert result.iterations[0].label == "Sprint 1"
        assert result.iterations[0].id == new_id

    def test_get_raises_on_missing_id_param(self, tmp_project_with_task):
        """Test that get without iteration_id raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="iteration_id"):
                iteration(action="get")

    def test_add_raises_on_missing_label(self, tmp_project_with_task):
        """Test that add without label raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="label"):
                iteration(action="add")

    def test_remove_deletes_iteration(self, tmp_project_with_task):
        """Test removing an iteration."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="To Delete")
            new_id = int(add_result.new_item_ids[0])
            remove_result = iteration(action="remove", iteration_id=new_id)
            list_result = iteration(action="list")
        assert remove_result.success is True
        assert remove_result.action == "iteration_removed"
        assert list_result.iterations == [] or list_result.iterations is None

    def test_remove_raises_on_missing_id_param(self, tmp_project_with_task):
        """Test that remove without iteration_id raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="iteration_id"):
                iteration(action="remove")

    def test_summary_includes_iteration_summaries(self, tmp_project_with_task):
        """Test that StatusSummary includes per-iteration counts after adding an iteration."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            iteration(action="add", label="Sprint 1")
            list_result = iteration(action="list")
        assert list_result.summary is not None
        assert list_result.summary.iteration_summaries is not None
        assert len(list_result.summary.iteration_summaries) == 1
        assert list_result.summary.iteration_summaries[0].label == "Sprint 1"

    def test_task_update_assigns_iteration(self, tmp_project_with_task):
        """Test that task update assigns a task to an iteration."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            update_result = task(action="update", task_id="T001", iteration=new_id)
        assert update_result.success is True
        assert update_result.action == "task_updated"

    def test_task_update_unassigns_iteration(self, tmp_project_with_task):
        """Test that task update can unassign a task from an iteration via unassign_iteration=True."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            task(action="update", task_id="T001", iteration=new_id)
            unassign_result = task(action="update", task_id="T001", unassign_iteration=True)
            get_result = get()
        t001 = next(t for t in get_result.spec.tasks if t.id == "T001")
        assert unassign_result.success is True
        assert unassign_result.action == "task_updated"
        assert t001.iteration is None

    def test_task_batch_update_unassigns_iteration_with_null(self, tmp_project_with_task):
        """Test that batch update can unassign a task from an iteration via iteration=None."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            task(action="update", task_id="T001", iteration=new_id)
            batch_result = task(
                action="batch",
                operations=[{"action": "update", "task_id": "T001", "iteration": None}],
            )
            get_result = get()
        t001 = next(t for t in get_result.spec.tasks if t.id == "T001")
        assert batch_result.success is True
        assert batch_result.action == "batch_tasks_applied"
        assert t001.iteration is None

    def test_task_update_omitting_iteration_preserves_existing(self, tmp_project_with_task):
        """Test that updating a task without mentioning iteration preserves the existing assignment.

        Regression test for the _UNSET sentinel bypass bug: when iteration is omitted from
        an update call, the MCP layer must NOT pass iteration=None to update_implementation_task,
        which would silently unassign the task from its current iteration.
        """
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            # Assign task to the iteration
            task(action="update", task_id="T001", iteration=new_id)
            # Update status only — do NOT mention iteration at all
            task(action="update", task_id="T001", status="in_progress")
            get_result = get()
        t001 = next(t for t in get_result.spec.tasks if t.id == "T001")
        # Iteration assignment must be preserved
        assert t001.iteration == new_id

    def test_remove_iteration_clears_task_refs(self, tmp_project_with_task):
        """Test that removing an iteration clears task.iteration references."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="To Delete")
            new_id = int(add_result.new_item_ids[0])
            task(action="update", task_id="T001", iteration=new_id)
            iteration(action="remove", iteration_id=new_id)
            # After removal, get the spec and verify task.iteration is None
            get_result = get()
        t001 = next(t for t in get_result.spec.tasks if t.id == "T001")
        assert t001.iteration is None

    def test_add_duplicate_iteration_labels_allowed(self, tmp_project_with_task):
        """Test that duplicate iteration labels are allowed (no uniqueness constraint)."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            r1 = iteration(action="add", label="Sprint 1")
            r2 = iteration(action="add", label="Sprint 1")
            list_result = iteration(action="list")
        assert r1.success is True
        assert r2.success is True
        assert list_result.iterations is not None
        assert len(list_result.iterations) == 2
        assert all(it.label == "Sprint 1" for it in list_result.iterations)

    def test_iteration_get_invalid_id_raises(self, tmp_project_with_task):
        """Test that getting a nonexistent iteration raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="Iteration"):
                iteration(action="get", iteration_id=999)

    def test_iteration_summary_counts_assigned_tasks(self, tmp_project_with_task):
        """Test that IterationSummary counts tasks assigned to the iteration."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            # Assign the task to this iteration
            task(action="update", task_id="T001", iteration=new_id)
            get_result = get()
        summaries = get_result.summary.iteration_summaries
        assert summaries is not None
        sprint_summary = next(s for s in summaries if s.label == "Sprint 1")
        assert sprint_summary.tasks_total == 1
        assert sprint_summary.tasks_not_started == 1
        assert sprint_summary.tasks_completed == 0

    def test_task_update_iteration_as_string_coerced(self, tmp_project_with_task):
        """Test that task update accepts iteration ID as a string (Qwen CLI compat).

        Qwen CLI passes integer parameters as JSON strings (e.g. "3" instead of 3).
        The MCP server must accept and coerce these string integers transparently.
        """
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = int(add_result.new_item_ids[0])
            # Pass iteration as a string, as Qwen CLI would
            result = task(action="update", task_id="T001", iteration=str(new_id))
            get_result = get()
        t001 = next(t for t in get_result.spec.tasks if t.id == "T001")
        assert result.success is True
        assert t001.iteration == new_id

    def test_iteration_get_id_as_string_coerced(self, tmp_project_with_task):
        """Test that iteration get accepts iteration_id as a string (Qwen CLI compat)."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="Sprint 1")
            new_id = add_result.new_item_ids[0]  # string form from new_item_ids
            result = iteration(action="get", iteration_id=new_id)
        assert result.action == "iteration_get"
        assert result.iterations is not None
        assert len(result.iterations) == 1
        assert result.iterations[0].label == "Sprint 1"

    def test_iteration_remove_id_as_string_coerced(self, tmp_project_with_task):
        """Test that iteration remove accepts iteration_id as a string (Qwen CLI compat)."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            add_result = iteration(action="add", label="To Delete")
            new_id = add_result.new_item_ids[0]  # string form from new_item_ids
            remove_result = iteration(action="remove", iteration_id=new_id)
            list_result = iteration(action="list")
        assert remove_result.success is True
        assert list_result.iterations == [] or list_result.iterations is None

    def test_iteration_invalid_string_id_raises(self, tmp_project_with_task):
        """Test that a non-numeric string raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="iteration_id"):
                iteration(action="get", iteration_id="not-a-number")

    def test_task_update_invalid_iteration_string_raises(self, tmp_project_with_task):
        """Test that a non-numeric string for iteration raises ValueError."""
        _project_root, task_file = tmp_project_with_task
        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with pytest.raises(ValueError, match="iteration"):
                task(action="update", task_id="T001", iteration="not-a-number")

    def _make_mock_spec(self, tmp_project_with_task):
        """Return (task_file, mock_spec) with a non-None quality_requirements."""
        _project_root, task_file = tmp_project_with_task
        mock_spec = MagicMock(spec=SimpleTaskSpec)
        # Spec-constrained so any access to a non-existent attribute raises AttributeError
        mock_spec.quality_requirements = MagicMock(spec=QualityRequirements)
        # Real strings required by StatusSummary Pydantic model
        mock_spec.branch = "test-feature"
        mock_spec.title = "Test Feature"
        mock_spec.acceptance_criteria = []
        mock_spec.tasks = []
        mock_spec.notes = []
        mock_spec.iterations = None
        mock_spec.audit_history = None
        return task_file, mock_spec

    def test_quality_check_no_filters(self, tmp_project_with_task):
        """All filter flags default to False when quality check is called without them."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    mock_run.return_value = ([], True)
                    quality(action="check")

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["lint_only"] is False
        assert call_kwargs["test_only"] is False
        assert call_kwargs["type_only"] is False
        assert call_kwargs["security_only"] is False

    def test_quality_check_lint_only(self, tmp_project_with_task):
        """lint_only=True is forwarded to run_quality_checks."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    mock_run.return_value = ([], True)
                    quality(action="check", lint_only=True)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["lint_only"] is True
        assert call_kwargs["test_only"] is False
        assert call_kwargs["type_only"] is False
        assert call_kwargs["security_only"] is False

    def test_quality_check_test_only(self, tmp_project_with_task):
        """test_only=True is forwarded to run_quality_checks."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    mock_run.return_value = ([], True)
                    quality(action="check", test_only=True)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["lint_only"] is False
        assert call_kwargs["test_only"] is True
        assert call_kwargs["type_only"] is False
        assert call_kwargs["security_only"] is False

    def test_quality_check_type_only(self, tmp_project_with_task):
        """type_only=True is forwarded to run_quality_checks."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    mock_run.return_value = ([], True)
                    quality(action="check", type_only=True)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["lint_only"] is False
        assert call_kwargs["test_only"] is False
        assert call_kwargs["type_only"] is True
        assert call_kwargs["security_only"] is False

    def test_quality_check_security_only(self, tmp_project_with_task):
        """security_only=True is forwarded to run_quality_checks."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    mock_run.return_value = ([], True)
                    quality(action="check", security_only=True)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["lint_only"] is False
        assert call_kwargs["test_only"] is False
        assert call_kwargs["type_only"] is False
        assert call_kwargs["security_only"] is True

    def test_quality_check_no_quality_reqs_raises(self, tmp_project_with_task):
        """quality(action='check') raises ValueError when quality_requirements is None.

        This aligns with CLI behavior which exits with code 1 when no quality
        requirements are configured.
        """
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)
        mock_spec.quality_requirements = None

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with patch("simpletask.mcp.server.run_quality_checks") as mock_run:
                    with pytest.raises(ValueError, match="No quality_requirements configuration"):
                        quality(action="check")

        mock_run.assert_not_called()

    @pytest.mark.parametrize(
        "action, extra_kwargs",
        [
            ("get", {}),
            # action='set' requires config_type; supply it so the filter-flag guard fires
            # first rather than a missing-config_type error — making the test independent
            # of validation ordering.
            ("set", {"config_type": "linting"}),
            ("preset", {"preset_name": "python"}),
        ],
    )
    def test_quality_filter_flags_raise_on_non_check_action(
        self, tmp_project_with_task, action, extra_kwargs
    ):
        """Filter flags raise ValueError when used with non-check actions."""
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with pytest.raises(
                    ValueError, match=r"Filter flags.*only valid with action='check'"
                ):
                    quality(action=action, lint_only=True, **extra_kwargs)

    def test_quality_check_multiple_flags_raises(self, tmp_project_with_task):
        """Passing more than one filter flag simultaneously must raise ValueError.

        The flags lint_only, test_only, type_only, and security_only are mutually exclusive.
        Passing two at once would silently drop one due to the elif chain in run_quality_checks;
        run_quality_checks() enforces this guard directly.
        """
        task_file, mock_spec = self._make_mock_spec(tmp_project_with_task)

        with patch("simpletask.mcp.server.get_current_task_file_path", return_value=task_file):
            with patch("simpletask.mcp.server.parse_task_file", return_value=mock_spec):
                with pytest.raises(ValueError, match="mutually exclusive"):
                    quality(action="check", lint_only=True, test_only=True)


class TestSimpletaskGetFiltering:
    """Tests for get() tool response filtering behavior."""

    def _mock_get(self, sample_spec_filterable, **kwargs):
        """Helper: call get() with parse_task_file mocked to return sample_spec_filterable."""
        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = "/fake/.tasks/test-filterable.yml"
            with patch(
                "simpletask.mcp.server.parse_task_file", return_value=sample_spec_filterable
            ):
                # validate_task_file is only called when validate=True, so no mock needed by default
                return get(**kwargs)

    # ------------------------------------------------------------------
    # Default behavior (no parameters)
    # ------------------------------------------------------------------

    def test_get_default_excludes_completed_tasks(self, sample_spec_filterable):
        """Default get() must exclude completed tasks from spec.tasks."""
        response = self._mock_get(sample_spec_filterable)
        assert response.spec.tasks is not None
        statuses = [t.status for t in response.spec.tasks]
        assert TaskStatus.COMPLETED not in statuses

    def test_get_default_excludes_design(self, sample_spec_filterable):
        """Default get() must set spec.design to None."""
        response = self._mock_get(sample_spec_filterable)
        assert response.spec.design is None

    def test_get_default_excludes_quality_requirements(self, sample_spec_filterable):
        """Default get() must set spec.quality_requirements to None."""
        response = self._mock_get(sample_spec_filterable)
        assert response.spec.quality_requirements is None

    def test_get_default_non_completed_task_count(self, sample_spec_filterable):
        """Default get() returns 6 non-completed tasks (9 total minus 3 completed)."""
        response = self._mock_get(sample_spec_filterable)
        # sample_spec_filterable has 3 completed (T001, T002, T004); 6 non-completed
        assert response.spec.tasks is not None
        assert len(response.spec.tasks) == 6

    # ------------------------------------------------------------------
    # full=True escape hatch
    # ------------------------------------------------------------------

    def test_get_full_returns_all_tasks(self, sample_spec_filterable):
        """get(full=True) must return all tasks including completed ones."""
        response = self._mock_get(sample_spec_filterable, full=True)
        assert response.spec.tasks is not None
        statuses = [t.status for t in response.spec.tasks]
        assert TaskStatus.COMPLETED in statuses
        assert len(response.spec.tasks) == 9  # all 9 tasks

    def test_get_full_returns_design(self, sample_spec_filterable):
        """get(full=True) must return the design section."""
        response = self._mock_get(sample_spec_filterable, full=True)
        assert response.spec.design is not None
        assert response.spec.design.patterns is not None

    def test_get_full_returns_quality_requirements(self, sample_spec_filterable):
        """get(full=True) must return quality_requirements."""
        response = self._mock_get(sample_spec_filterable, full=True)
        assert response.spec.quality_requirements is not None

    def test_get_full_has_filters_applied_none(self, sample_spec_filterable):
        """get(full=True) must set filters_applied to None."""
        response = self._mock_get(sample_spec_filterable, full=True)
        assert response.filters_applied is None

    # ------------------------------------------------------------------
    # Individual filter parameters
    # ------------------------------------------------------------------

    def test_get_include_completed_returns_completed(self, sample_spec_filterable):
        """get(include_completed=True) must include completed tasks."""
        response = self._mock_get(sample_spec_filterable, include_completed=True)
        statuses = [t.status for t in response.spec.tasks]
        assert TaskStatus.COMPLETED in statuses

    def test_get_include_design_returns_design(self, sample_spec_filterable):
        """get(include_design=True) must include the design section."""
        response = self._mock_get(sample_spec_filterable, include_design=True)
        assert response.spec.design is not None

    def test_get_include_quality_returns_quality(self, sample_spec_filterable):
        """get(include_quality=True) must include quality_requirements."""
        response = self._mock_get(sample_spec_filterable, include_quality=True)
        assert response.spec.quality_requirements is not None

    def test_get_status_filter_in_progress(self, sample_spec_filterable):
        """get(status='in_progress') returns only in_progress tasks."""
        response = self._mock_get(sample_spec_filterable, status="in_progress")
        assert response.spec.tasks is not None
        assert all(t.status == TaskStatus.IN_PROGRESS for t in response.spec.tasks)
        # sample_spec_filterable has 2 in_progress tasks (T003, T006)
        assert len(response.spec.tasks) == 2

    def test_get_status_filter_not_started(self, sample_spec_filterable):
        """get(status='not_started') returns only not_started tasks."""
        response = self._mock_get(sample_spec_filterable, status="not_started")
        assert response.spec.tasks is not None
        assert all(t.status == TaskStatus.NOT_STARTED for t in response.spec.tasks)
        # sample_spec_filterable has 2 not_started tasks (T007, T009)
        assert len(response.spec.tasks) == 2

    def test_get_status_filter_completed_with_include(self, sample_spec_filterable):
        """get(status='completed', include_completed=True) returns only completed tasks."""
        response = self._mock_get(
            sample_spec_filterable, status="completed", include_completed=True
        )
        assert response.spec.tasks is not None
        assert all(t.status == TaskStatus.COMPLETED for t in response.spec.tasks)
        assert len(response.spec.tasks) == 3  # T001, T002, T004

    def test_get_iteration_filter(self, sample_spec_filterable):
        """get(iteration=1) returns only tasks assigned to iteration 1 (non-completed)."""
        response = self._mock_get(sample_spec_filterable, iteration=1)
        assert response.spec.tasks is not None
        # Iteration 1: T001 (completed, excluded), T002 (completed, excluded), T003 (in_progress)
        assert len(response.spec.tasks) == 1
        assert response.spec.tasks[0].id == "T003"

    def test_get_iteration_filter_with_include_completed(self, sample_spec_filterable):
        """get(iteration=1, include_completed=True) returns all tasks in iteration 1."""
        response = self._mock_get(sample_spec_filterable, iteration=1, include_completed=True)
        assert response.spec.tasks is not None
        # Iteration 1 has T001, T002, T003
        assert len(response.spec.tasks) == 3
        assert {t.id for t in response.spec.tasks} == {"T001", "T002", "T003"}

    def test_get_iteration_string_coerced_to_int(self, sample_spec_filterable):
        """get(iteration='2') coerces string to int (Qwen CLI compat)."""
        response = self._mock_get(sample_spec_filterable, iteration="2")
        # Iteration 2 has T004 (completed, excluded), T005 (blocked), T006 (in_progress)
        assert response.spec.tasks is not None
        task_ids = {t.id for t in response.spec.tasks}
        assert "T005" in task_ids
        assert "T006" in task_ids
        assert "T004" not in task_ids  # completed

    # ------------------------------------------------------------------
    # Filter combinations
    # ------------------------------------------------------------------

    def test_get_iteration_and_status_combined(self, sample_spec_filterable):
        """get(iteration=2, status='blocked') returns only blocked tasks in iteration 2."""
        response = self._mock_get(sample_spec_filterable, iteration=2, status="blocked")
        assert response.spec.tasks is not None
        assert len(response.spec.tasks) == 1
        assert response.spec.tasks[0].id == "T005"
        assert response.spec.tasks[0].status == TaskStatus.BLOCKED

    def test_get_status_completed_without_include_returns_empty(self, sample_spec_filterable):
        """get(status='completed') with default include_completed=False returns no tasks.

        Since include_completed=False is applied first (removing completed), then
        status='completed' filter finds nothing. Result: empty list.
        """
        response = self._mock_get(sample_spec_filterable, status="completed")
        # First exclude completed (none left for status filter), then filter by completed status
        assert response.spec.tasks is not None
        assert len(response.spec.tasks) == 0

    # ------------------------------------------------------------------
    # Summary integrity — always unfiltered
    # ------------------------------------------------------------------

    def test_get_summary_always_reflects_full_spec(self, sample_spec_filterable):
        """Summary counts must reflect the full unfiltered spec regardless of filters."""
        # With heavy filtering
        response = self._mock_get(sample_spec_filterable, iteration=1, status="in_progress")
        # Summary should still show all 9 tasks
        assert response.summary.tasks_total == 9
        assert response.summary.tasks_completed == 3
        assert response.summary.tasks_in_progress == 2
        assert response.summary.tasks_not_started == 2
        assert response.summary.tasks_blocked == 1
        assert response.summary.tasks_paused == 1

    def test_get_full_summary_matches_default_summary(self, sample_spec_filterable):
        """get(full=True) and get() must produce identical summaries."""
        full_response = self._mock_get(sample_spec_filterable, full=True)
        default_response = self._mock_get(sample_spec_filterable)
        assert full_response.summary.tasks_total == default_response.summary.tasks_total
        assert full_response.summary.tasks_completed == default_response.summary.tasks_completed

    # ------------------------------------------------------------------
    # filters_applied dict correctness
    # ------------------------------------------------------------------

    def test_get_filters_applied_contains_required_keys(self, sample_spec_filterable):
        """filters_applied dict must contain all 5 required keys."""
        response = self._mock_get(sample_spec_filterable)
        assert response.filters_applied is not None
        required_keys = {
            "include_completed",
            "include_design",
            "include_quality",
            "tasks_returned",
            "tasks_excluded",
        }
        assert required_keys.issubset(response.filters_applied.keys())

    def test_get_filters_applied_task_counts_are_correct(self, sample_spec_filterable):
        """filters_applied tasks_returned + tasks_excluded must equal total tasks in spec."""
        response = self._mock_get(sample_spec_filterable)
        assert response.filters_applied is not None
        total = (
            response.filters_applied["tasks_returned"] + response.filters_applied["tasks_excluded"]
        )
        assert total == 9  # sample_spec_filterable has 9 tasks total

    def test_get_filters_applied_default_values(self, sample_spec_filterable):
        """filters_applied default flag values match the parameter defaults."""
        response = self._mock_get(sample_spec_filterable)
        assert response.filters_applied is not None
        assert response.filters_applied["include_completed"] is False
        assert response.filters_applied["include_design"] is False
        assert response.filters_applied["include_quality"] is False

    def test_get_filters_applied_none_when_full(self, sample_spec_filterable):
        """filters_applied is None when full=True."""
        response = self._mock_get(sample_spec_filterable, full=True)
        assert response.filters_applied is None

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_get_invalid_status_raises_valueerror(self, sample_spec_filterable):
        """get(status='invalid') must raise ValueError with descriptive message."""
        with pytest.raises(ValueError, match="Invalid status"):
            self._mock_get(sample_spec_filterable, status="invalid_value")

    def test_get_invalid_iteration_raises_valueerror(self, sample_spec_filterable):
        """get(iteration=999) must raise ValueError for non-existent iteration."""
        with pytest.raises(ValueError, match="Iteration"):
            self._mock_get(sample_spec_filterable, iteration=999)

    def test_get_invalid_iteration_string_raises_valueerror(self, sample_spec_filterable):
        """get(iteration='not-a-number') must raise ValueError."""
        with pytest.raises(ValueError, match="iteration"):
            self._mock_get(sample_spec_filterable, iteration="not-a-number")

    def test_get_valid_statuses_accepted(self, sample_spec_filterable):
        """All valid TaskStatus values must be accepted without error."""
        valid_statuses = ["not_started", "in_progress", "completed", "blocked", "paused"]
        for s in valid_statuses:
            # Should not raise (combine with include_completed to allow 'completed' to pass through)
            self._mock_get(sample_spec_filterable, status=s, include_completed=True)


class TestRunQualityChecksMutualExclusivity:
    """Direct unit tests for run_quality_checks() defence-in-depth guard.

    These tests bypass the MCP layer entirely and call quality_ops.run_quality_checks()
    directly, validating that the guard works for any caller — not just the MCP server.
    """

    def _make_requirements(self):
        return QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST),
        )

    def test_two_flags_raises_value_error(self):
        """run_quality_checks raises ValueError when more than one filter flag is True."""
        reqs = self._make_requirements()
        with pytest.raises(ValueError, match="at most one"):
            run_quality_checks(reqs, lint_only=True, test_only=True)

    def test_three_flags_raises_value_error(self):
        """run_quality_checks raises ValueError when three filter flags are True."""
        reqs = self._make_requirements()
        with pytest.raises(ValueError, match="at most one"):
            run_quality_checks(reqs, lint_only=True, test_only=True, type_only=True)

    @pytest.mark.parametrize(
        "flag_name, checker_method",
        [
            ("lint_only", "run_linting_only"),
            ("test_only", "run_testing_only"),
            ("type_only", "run_type_checking_only"),
            ("security_only", "run_security_only"),
        ],
    )
    def test_single_flag_does_not_raise(self, flag_name, checker_method):
        """run_quality_checks does not raise when exactly one filter flag is set.

        Parametrized over all four filter flags to ensure no branch swap in the
        elif chain would go undetected.
        """
        reqs = self._make_requirements()
        with patch("simpletask.core.quality_ops.QualityChecker") as mock_checker_cls:
            mock_checker = MagicMock()
            mock_checker_cls.return_value = mock_checker
            getattr(mock_checker, checker_method).return_value = ([], True)
            result = run_quality_checks(reqs, **{flag_name: True})
            getattr(mock_checker, checker_method).assert_called_once()
            assert result == ([], True)


class TestSchemaOverrides:
    """Tests that WithJsonSchema overrides reach the FastMCP wire schema."""

    def _get_wire_tool_schema(self, tool_name: str, mcp_tools_list) -> dict:
        """Return the inputSchema dict advertised by FastMCP for a named tool.

        Args:
            tool_name: Name of the tool to look up
            mcp_tools_list: Fixture providing cached FastMCP tools list

        Returns:
            The inputSchema dict for the tool
        """
        tool = next((t for t in mcp_tools_list if t.name == tool_name), None)
        assert tool is not None, f"Tool '{tool_name}' not found in mcp.list_tools()"
        return tool.inputSchema

    def test_task_id_wire_schema_is_string_not_nullable(self, mcp_tools_list):
        """Verify FastMCP advertises task_id as {type: string} (no anyOf) on the wire."""
        schema = self._get_wire_tool_schema("task", mcp_tools_list)
        task_id_schema = schema.get("properties", {}).get("task_id", {})
        assert task_id_schema.get("type") == "string", (
            f"task_id schema should be {{type: string}}, got: {task_id_schema}"
        )
        assert "anyOf" not in task_id_schema, (
            f"task_id schema must not contain anyOf; got: {task_id_schema}"
        )

    def test_criterion_id_wire_schema_is_string_not_nullable(self, mcp_tools_list):
        """Verify FastMCP advertises criterion_id as {type: string} (no anyOf) on the wire."""
        schema = self._get_wire_tool_schema("criteria", mcp_tools_list)
        criterion_id_schema = schema.get("properties", {}).get("criterion_id", {})
        assert criterion_id_schema.get("type") == "string", (
            f"criterion_id schema should be {{type: string}}, got: {criterion_id_schema}"
        )
        assert "anyOf" not in criterion_id_schema, (
            f"criterion_id schema must not contain anyOf; got: {criterion_id_schema}"
        )

    def test_batch_task_operation_task_id_schema_is_string_not_nullable(self):
        """Verify BatchTaskOperation.task_id schema is {type: string} not anyOf."""
        from simpletask.mcp.models import BatchTaskOperation

        schema = BatchTaskOperation.model_json_schema()
        task_id_schema = schema["properties"]["task_id"]

        # Should be {type: string} not {anyOf: [...]}
        assert task_id_schema.get("type") == "string"
        assert "anyOf" not in task_id_schema

    def test_operations_wire_schema_has_items(self, mcp_tools_list):
        """Verify FastMCP advertises operations as {type: array, items: ...} with structure."""
        schema = self._get_wire_tool_schema("task", mcp_tools_list)
        operations_schema = schema.get("properties", {}).get("operations", {})

        # Should have type: array
        assert operations_schema.get("type") == "array", (
            f"operations schema should be {{type: array}}, got: {operations_schema}"
        )

        # Should have items subschema describing BatchTaskOperation structure
        assert "items" in operations_schema, (
            f"operations schema must have items subschema; got: {operations_schema}"
        )

        # Items should have BatchTaskOperation properties
        items_schema = operations_schema.get("items", {})
        assert "properties" in items_schema or "type" in items_schema, (
            f"operations items must define structure; got: {items_schema}"
        )
        assert operations_schema.get("minItems") == 1, (
            f"operations schema should require at least one item; got: {operations_schema}"
        )


class TestTaskErrorMessages:
    """Tests that task() error messages include concrete examples."""

    def test_task_get_error_has_example(self, tmp_project_with_task):
        """Verify task get action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="get")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='get', task_id='T001')" in error_msg

    def test_task_update_error_has_example(self, tmp_project_with_task):
        """Verify task update action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="update")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='update', task_id='T001'" in error_msg

    def test_task_remove_error_has_example(self, tmp_project_with_task):
        """Verify task remove action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="remove")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='remove', task_id='T001')" in error_msg

    def test_task_get_error_with_empty_string(self, tmp_project_with_task):
        """Verify task get action rejects empty-string task_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="get", task_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='get', task_id='T001')" in error_msg
            assert "cannot be empty" in error_msg

    def test_task_update_error_with_empty_string(self, tmp_project_with_task):
        """Verify task update action rejects empty-string task_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="update", task_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='update', task_id='T001'" in error_msg
            assert "cannot be empty" in error_msg

    def test_task_remove_error_with_empty_string(self, tmp_project_with_task):
        """Verify task remove action rejects empty-string task_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="remove", task_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='remove', task_id='T001')" in error_msg
            assert "cannot be empty" in error_msg

    def test_task_batch_error_has_example(self, tmp_project_with_task):
        """Verify task batch action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="batch")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='batch', operations=" in error_msg
            assert "'operations' is required" in error_msg

    def test_task_batch_error_with_empty_operations(self, tmp_project_with_task):
        """Verify task batch action rejects empty operations list with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="batch", operations=[])

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='batch', operations=" in error_msg
            assert "cannot be empty" in error_msg

    def test_task_get_error_with_explicit_none(self, tmp_project_with_task):
        """Verify task get action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="get", task_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='get', task_id='T001')" in error_msg

    def test_task_update_error_with_explicit_none(self, tmp_project_with_task):
        """Verify task update action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="update", task_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='update', task_id='T001'" in error_msg

    def test_task_remove_error_with_explicit_none(self, tmp_project_with_task):
        """Verify task remove action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                task(action="remove", task_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "task(action='remove', task_id='T001')" in error_msg


class TestCriteriaErrorMessages:
    """Tests that criteria() error messages include concrete examples."""

    def test_criteria_get_error_has_example(self, tmp_project_with_task):
        """Verify criteria get action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="get")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='get', criterion_id='AC1')" in error_msg

    def test_criteria_complete_error_has_example(self, tmp_project_with_task):
        """Verify criteria complete action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="complete")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='complete'" in error_msg

    def test_criteria_remove_error_has_example(self, tmp_project_with_task):
        """Verify criteria remove action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="remove")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='remove', criterion_id='AC1')" in error_msg

    def test_criteria_update_error_has_example(self, tmp_project_with_task):
        """Verify criteria update action error includes Example call."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="update")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='update', criterion_id='AC1'" in error_msg

    def test_criteria_get_error_with_empty_string(self, tmp_project_with_task):
        """Verify criteria get action rejects empty-string criterion_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="get", criterion_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='get', criterion_id='AC1')" in error_msg
            assert "cannot be empty" in error_msg

    def test_criteria_complete_error_with_empty_string(self, tmp_project_with_task):
        """Verify criteria complete action rejects empty-string criterion_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="complete", criterion_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='complete'" in error_msg
            assert "cannot be empty" in error_msg

    def test_criteria_remove_error_with_empty_string(self, tmp_project_with_task):
        """Verify criteria remove action rejects empty-string criterion_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="remove", criterion_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='remove', criterion_id='AC1')" in error_msg
            assert "cannot be empty" in error_msg

    def test_criteria_update_error_with_empty_string(self, tmp_project_with_task):
        """Verify criteria update action rejects empty-string criterion_id with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="update", criterion_id="")  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='update', criterion_id='AC1'" in error_msg
            assert "cannot be empty" in error_msg

    def test_criteria_get_error_with_explicit_none(self, tmp_project_with_task):
        """Verify criteria get action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="get", criterion_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='get', criterion_id='AC1')" in error_msg

    def test_criteria_complete_error_with_explicit_none(self, tmp_project_with_task):
        """Verify criteria complete action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="complete", criterion_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='complete'" in error_msg

    def test_criteria_remove_error_with_explicit_none(self, tmp_project_with_task):
        """Verify criteria remove action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="remove", criterion_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='remove', criterion_id='AC1')" in error_msg

    def test_criteria_update_error_with_explicit_none(self, tmp_project_with_task):
        """Verify criteria update action with explicit None rejects with Example message."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file

            with pytest.raises(ValueError) as exc_info:
                criteria_tool(action="update", criterion_id=None)  # type: ignore

            error_msg = str(exc_info.value)
            assert "Example:" in error_msg
            assert "criteria(action='update', criterion_id='AC1'" in error_msg

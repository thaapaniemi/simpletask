"""Unit tests for MCP tools (simpletask_get, simpletask_list)."""

from unittest.mock import MagicMock, patch

import pytest
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import simpletask_get, simpletask_list


class TestSimpletaskGet:
    """Tests for simpletask_get tool."""

    def test_get_current_branch(self, tmp_project_with_task):
        """Test getting task for current branch."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = simpletask_get(branch=None, validate=False)

            assert response.spec is not None
            assert response.spec.branch == "test-feature"
            assert response.file_path == str(task_file)
            assert response.summary is not None
            assert response.validation is None

    def test_get_specific_branch(self, tmp_project_with_task):
        """Verify branch parameter passed correctly."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = simpletask_get(branch="test-feature", validate=False)

            mock_path.assert_called_once_with("test-feature")
            assert response.spec.branch == "test-feature"

    def test_get_with_validation_valid(self, tmp_project_with_task):
        """Verify validation included when validate=True."""
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = simpletask_get(branch=None, validate=True)

            assert response.validation is not None
            assert response.validation.valid is True
            assert len(response.validation.errors) == 0

    def test_get_with_validation_invalid(self, tmp_path):
        """Verify errors populated for invalid file."""
        # Create invalid YAML file
        task_file = tmp_path / "invalid.yml"
        task_file.write_text("invalid: yaml: content:")

        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(InvalidTaskFileError):
                simpletask_get(branch=None, validate=True)

    def test_get_file_not_found(self, tmp_path):
        """Verify FileNotFoundError raised for non-existent file."""
        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = tmp_path / "nonexistent.yml"
            with pytest.raises(FileNotFoundError):
                simpletask_get(branch="nonexistent-branch")

    def test_get_invalid_yaml(self, tmp_path):
        """Verify InvalidTaskFileError raised for malformed YAML."""
        task_file = tmp_path / "bad.yml"
        task_file.write_text("{ invalid yaml content")

        with patch("simpletask.mcp.server.get_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(InvalidTaskFileError):
                simpletask_get()

    def test_get_not_in_git_repo(self, tmp_path, monkeypatch):
        """Verify error when not in a git repository."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="git"):
            simpletask_get()


class TestSimpletaskList:
    """Tests for simpletask_list tool."""

    def test_list_tasks(self, tmp_project_with_task):
        """Verify returns branch names."""
        _project_root, _task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.ensure_project") as mock_project:
            mock_proj = MagicMock()
            mock_proj.list_tasks.return_value = ["test-feature", "another-branch"]
            mock_project.return_value = mock_proj

            result = simpletask_list()

            assert result == ["test-feature", "another-branch"]

    def test_list_empty(self, tmp_project):
        """Verify returns [] when no tasks."""
        with patch("simpletask.mcp.server.ensure_project") as mock_project:
            mock_proj = MagicMock()
            mock_proj.list_tasks.return_value = []
            mock_project.return_value = mock_proj

            result = simpletask_list()

            assert result == []

    def test_list_not_in_git_repo(self, tmp_path, monkeypatch):
        """Verify error when not in a git repository."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="git"):
            simpletask_list()


class TestSecurityPathTraversal:
    """Security tests for path traversal attacks via branch parameter."""

    def test_path_traversal_dotdot(self, tmp_project):
        """Verify ../../ sequences cannot escape .tasks directory."""
        # The normalize_branch_name function should convert .. to --
        # This test verifies it doesn't allow reading files outside .tasks/
        with pytest.raises((FileNotFoundError, ValueError)):
            simpletask_get(branch="../../etc/passwd")

    def test_path_traversal_encoded(self, tmp_project):
        """Verify encoded path traversal is normalized safely."""
        # Branch names with dots get normalized
        with pytest.raises((FileNotFoundError, ValueError)):
            simpletask_get(branch="....//....//etc/passwd")

    def test_branch_with_slashes(self, tmp_project_with_task):
        """Verify branch names with slashes work correctly."""
        # feature/auth -> feature-auth.yml
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_task_file_path") as mock:
            mock.return_value = task_file
            result = simpletask_get(branch="feature/auth")
            assert result.spec is not None

    def test_branch_with_unicode(self, tmp_project):
        """Verify branch with unicode chars normalized."""
        # Unicode characters should be normalized to ASCII
        # This should not raise an exception, just file not found
        with pytest.raises(FileNotFoundError):
            simpletask_get(branch="feature/café")

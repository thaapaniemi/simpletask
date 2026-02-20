"""Integration tests for branch name normalization.

Tests verify that branches with slashes in their names are properly handled
across the entire workflow, addressing issue #4.
"""

import subprocess

import pytest


class TestBranchNormalizationIntegration:
    """Integration tests for branch names with slashes."""

    def test_show_command_with_slash_branch(self, tmp_git_project_with_task):
        """Test that 'simpletask show' works with branch names containing slashes.

        This specifically tests the fix for issue #4:
        - Branch: feature/mcp-server-support
        - File: .tasks/feature-mcp-server-support.yml
        - Command: simpletask show (should work without manual path construction)
        """
        project_root, _branch_name, task_file = tmp_git_project_with_task

        # Verify file exists with normalized name
        assert task_file.exists(), f"Task file should exist at {task_file}"
        assert task_file.name == "feature-mcp-server-support.yml", (
            "File should have normalized name with hyphens"
        )

        # Run simpletask show command
        result = subprocess.run(
            ["simpletask", "show"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Command should succeed
        assert result.returncode == 0, f"simpletask show failed: {result.stderr}\n{result.stdout}"

        # Output should contain the original branch name (not normalized)
        assert "feature/mcp-server-support" in result.stdout, (
            f"Output should show original branch name with slash, got: {result.stdout}"
        )

        # Output should show the task title
        assert "Test Task" in result.stdout, f"Output should contain task title: {result.stdout}"

    def test_manual_path_construction_fails(self, tmp_git_project_with_task):
        """Verify that manual .tasks/ path construction with slashes fails.

        This demonstrates the original issue #4 problem:
        ls .tasks/$(git branch --show-current).yml fails because
        it doesn't normalize the branch name.
        """
        project_root, _branch_name, _task_file = tmp_git_project_with_task

        # This bash command represents the OLD broken approach
        bash_cmd = "ls .tasks/$(git branch --show-current).yml"

        result = subprocess.run(
            ["bash", "-c", bash_cmd],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # This SHOULD fail because bash doesn't normalize branch names
        assert result.returncode != 0, (
            "Manual path construction should fail with slash-containing branches"
        )
        assert (
            "No such file or directory" in result.stderr or "cannot access" in result.stderr.lower()
        ), f"Should get file-not-found error, got: {result.stderr}"

    def test_cli_commands_all_work_with_slash_branches(self, tmp_git_project_with_task):
        """Test that all major CLI commands work with slash-containing branches."""
        project_root, _branch_name, _task_file = tmp_git_project_with_task

        # Test 'simpletask show'
        result = subprocess.run(
            ["simpletask", "show"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"show failed: {result.stderr}"

        # Test 'simpletask task list'
        result = subprocess.run(
            ["simpletask", "task", "list"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"task list failed: {result.stderr}"

        # Test 'simpletask criteria list'
        result = subprocess.run(
            ["simpletask", "criteria", "list"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"criteria list failed: {result.stderr}"

        # Test 'simpletask list'
        result = subprocess.run(
            ["simpletask", "list"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"list failed: {result.stderr}"

        # Test 'simpletask schema validate'
        result = subprocess.run(
            ["simpletask", "schema", "validate"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"schema validate failed: {result.stderr}"

    @pytest.mark.parametrize(
        "branch_name,expected_filename",
        [
            ("feature/user-auth", "feature-user-auth.yml"),
            ("bugfix/issue-123", "bugfix-issue-123.yml"),
            ("hotfix/critical-bug", "hotfix-critical-bug.yml"),
            ("refactor/code-cleanup", "refactor-code-cleanup.yml"),
            ("feat/add-api", "feat-add-api.yml"),
        ],
    )
    def test_various_branch_patterns(self, tmp_path, branch_name, expected_filename):
        """Test that various common branch naming patterns are normalized correctly."""
        from simpletask.core.project import normalize_branch_name

        normalized = normalize_branch_name(branch_name)
        expected = expected_filename.replace(".yml", "")

        assert normalized == expected, (
            f"Branch '{branch_name}' should normalize to '{expected}', got '{normalized}'"
        )

"""Tests for migrate command."""

from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from simpletask.commands.migrate import migrate
from simpletask.core.models import AcceptanceCriterion, SimpleTaskSpec, TaskStatus
from simpletask.core.yaml_parser import write_task_file


@pytest.fixture
def nested_task_structure(tmp_project: Path) -> Path:
    """Create nested task structure for migration testing."""
    tasks_dir = tmp_project / ".tasks"

    # Create nested directories
    feature_dir = tasks_dir / "feature"
    feature_dir.mkdir()
    bugfix_dir = tasks_dir / "bugfix"
    bugfix_dir.mkdir()

    # Create task specs with different branch names
    spec1 = SimpleTaskSpec(
        schema_version="1.0",
        branch="feature/user-auth",
        title="User Auth",
        original_prompt="Test",
        status=TaskStatus.NOT_STARTED,
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Test", completed=False)],
    )
    spec2 = SimpleTaskSpec(
        schema_version="1.0",
        branch="bugfix/login-issue",
        title="Login Bug",
        original_prompt="Test",
        status=TaskStatus.NOT_STARTED,
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Test", completed=False)],
    )
    spec3 = SimpleTaskSpec(
        schema_version="1.0",
        branch="main-task",
        title="Main Task",
        original_prompt="Test",
        status=TaskStatus.NOT_STARTED,
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Test", completed=False)],
    )

    # Write files in nested structure
    write_task_file(feature_dir / "user-auth.yml", spec1, update_timestamp=False)
    write_task_file(bugfix_dir / "login-issue.yml", spec2, update_timestamp=False)
    write_task_file(tasks_dir / "main-task.yml", spec3, update_timestamp=False)

    return tmp_project


class TestMigrateDryRun:
    """Tests for migrate command in dry-run mode."""

    def test_dry_run_shows_plan(self, nested_task_structure):
        """Test dry-run mode shows migration plan without changes."""
        tasks_dir = nested_task_structure / ".tasks"

        # Verify nested structure exists
        assert (tasks_dir / "feature" / "user-auth.yml").exists()
        assert (tasks_dir / "bugfix" / "login-issue.yml").exists()

        # Run migrate in dry-run mode
        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = nested_task_structure
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=True, force=False)

        # Verify files still in nested structure
        assert (tasks_dir / "feature" / "user-auth.yml").exists()
        assert (tasks_dir / "bugfix" / "login-issue.yml").exists()
        assert (tasks_dir / "main-task.yml").exists()

        # Verify no flat files created
        assert not (tasks_dir / "feature-user-auth.yml").exists()
        assert not (tasks_dir / "bugfix-login-issue.yml").exists()

    def test_dry_run_no_tasks_dir(self, tmp_project):
        """Test dry-run when no .tasks directory exists."""
        tasks_dir = tmp_project / ".tasks"
        tasks_dir.rmdir()  # Remove tasks dir

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            # Should not raise error
            migrate(dry_run=True, force=False)


class TestMigrateExecution:
    """Tests for migrate command execution."""

    def test_migrate_nested_to_flat(self, nested_task_structure):
        """Test migrating nested structure to flat."""
        tasks_dir = nested_task_structure / ".tasks"

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = nested_task_structure
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=False)

        # Verify old nested files removed
        assert not (tasks_dir / "feature" / "user-auth.yml").exists()
        assert not (tasks_dir / "bugfix" / "login-issue.yml").exists()

        # Verify new flat files created with normalized names
        assert (tasks_dir / "feature-user-auth.yml").exists()
        assert (tasks_dir / "bugfix-login-issue.yml").exists()
        assert (tasks_dir / "main-task.yml").exists()

        # Verify empty directories removed
        assert not (tasks_dir / "feature").exists()
        assert not (tasks_dir / "bugfix").exists()

    def test_migrate_already_normalized(self, tmp_project):
        """Test migrate when files already in correct location."""
        tasks_dir = tmp_project / ".tasks"

        # Create task already in normalized location
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="feature-task",
            title="Feature",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(tasks_dir / "feature-task.yml", spec, update_timestamp=False)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=False)

        # File should still exist in same location
        assert (tasks_dir / "feature-task.yml").exists()

    def test_migrate_with_conflicts(self, nested_task_structure):
        """Test migrate handles conflicts without force flag."""
        tasks_dir = nested_task_structure / ".tasks"

        # Create conflicting file
        (tasks_dir / "feature-user-auth.yml").write_text("conflict")

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = nested_task_structure
            mock_project.return_value.tasks_dir = tasks_dir

            # Should detect conflict and not overwrite
            with pytest.raises(typer.Exit):
                migrate(dry_run=False, force=False)

        # Conflict file should still contain "conflict"
        assert (tasks_dir / "feature-user-auth.yml").read_text() == "conflict"

        # Original nested file should still exist
        assert (tasks_dir / "feature" / "user-auth.yml").exists()

    def test_migrate_with_force_overwrites(self, nested_task_structure):
        """Test migrate overwrites conflicts with force flag."""
        tasks_dir = nested_task_structure / ".tasks"

        # Create conflicting file
        (tasks_dir / "feature-user-auth.yml").write_text("conflict")

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = nested_task_structure
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=True)

        # Conflict should be overwritten with valid YAML
        assert (tasks_dir / "feature-user-auth.yml").exists()
        content = (tasks_dir / "feature-user-auth.yml").read_text()
        assert "schema_version" in content
        assert "conflict" not in content

        # Original nested file should be removed
        assert not (tasks_dir / "feature" / "user-auth.yml").exists()

    def test_migrate_preserves_content(self, nested_task_structure):
        """Test migrate preserves task content exactly."""
        tasks_dir = nested_task_structure / ".tasks"

        # Read original content
        original_path = tasks_dir / "feature" / "user-auth.yml"
        original_content = original_path.read_text()

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = nested_task_structure
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=False)

        # Read migrated content
        migrated_path = tasks_dir / "feature-user-auth.yml"
        migrated_content = migrated_path.read_text()

        # Content should be identical (except maybe formatting)
        assert "branch: feature/user-auth" in migrated_content
        assert "title: User Auth" in migrated_content

    def test_migrate_skips_invalid_files(self, tmp_project):
        """Test migrate skips files with invalid YAML."""
        tasks_dir = tmp_project / ".tasks"

        # Create invalid YAML file
        invalid_dir = tasks_dir / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "bad.yml").write_text("not: valid: yaml: content:")

        # Create valid file
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="valid-task",
            title="Valid",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(tasks_dir / "valid-task.yml", spec, update_timestamp=False)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            # Should not raise, should skip invalid file
            migrate(dry_run=False, force=False)

        # Valid file should still exist
        assert (tasks_dir / "valid-task.yml").exists()

        # Invalid file should remain in place (not migrated)
        assert (invalid_dir / "bad.yml").exists()


class TestMigrateEdgeCases:
    """Tests for edge cases in migrate command."""

    def test_migrate_deeply_nested(self, tmp_project):
        """Test migrate with deeply nested directory structure."""
        tasks_dir = tmp_project / ".tasks"

        # Create deeply nested structure
        deep_dir = tasks_dir / "a" / "b" / "c"
        deep_dir.mkdir(parents=True)

        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="deep/nested/task",
            title="Deep Task",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(deep_dir / "task.yml", spec, update_timestamp=False)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=False)

        # Should be flattened to root with normalized name
        assert (tasks_dir / "deep-nested-task.yml").exists()

        # All nested directories should be removed
        assert not (tasks_dir / "a").exists()

    def test_migrate_empty_tasks_dir(self, tmp_project):
        """Test migrate with empty .tasks directory."""
        tasks_dir = tmp_project / ".tasks"

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            # Should not raise error
            migrate(dry_run=False, force=False)

    def test_migrate_special_characters_in_branch(self, tmp_project):
        """Test migrate normalizes special characters correctly."""
        tasks_dir = tmp_project / ".tasks"
        nested_dir = tasks_dir / "feature"
        nested_dir.mkdir()

        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="feature/Fix: Bug in <Module>",
            title="Special Chars",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(nested_dir / "weird-name.yml", spec, update_timestamp=False)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            migrate(dry_run=False, force=False)

        # Should normalize to safe filename
        assert (tasks_dir / "feature-fix-bug-in-module.yml").exists()
        assert not (nested_dir / "weird-name.yml").exists()

    def test_migrate_rejects_symlink_outside_tasks_dir(self, tmp_project):
        """Test that symlinks pointing outside tasks_dir are rejected for security.

        This prevents path traversal attacks where a symlink could be used to
        delete or overwrite files outside the .tasks directory.
        """
        tasks_dir = tmp_project / ".tasks"

        # Create a file outside tasks directory
        outside_dir = tmp_project / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "target.yml"

        # Create a valid task spec
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="evil/symlink-task",
            title="Evil Task",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(outside_file, spec, update_timestamp=False)

        # Create a symlink inside tasks_dir pointing outside
        nested_dir = tasks_dir / "evil"
        nested_dir.mkdir()
        symlink = nested_dir / "symlink.yml"
        symlink.symlink_to(outside_file)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            # Migration should handle the symlink safely
            migrate(dry_run=False, force=False)

        # Outside file should still exist (not deleted by migration)
        assert outside_file.exists(), "Outside file should not be deleted"

        # Symlink should remain (migration skipped it with warning)
        assert symlink.exists(), "Symlink should remain in place"

    def test_migrate_collision_shows_branch_names(self, tmp_project, capsys):
        """Test that collision error messages show both conflicting branch names.

        When two different branches normalize to the same filename, the error
        message should clearly show which branch names are in conflict.
        """
        tasks_dir = tmp_project / ".tasks"

        # Create first branch that normalizes to "feature-user-auth.yml"
        spec1 = SimpleTaskSpec(
            schema_version="1.0",
            branch="feature/user-auth",
            title="First Task",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        # Already in normalized location
        write_task_file(tasks_dir / "feature-user-auth.yml", spec1, update_timestamp=False)

        # Create second branch in nested dir that also normalizes to "feature-user-auth.yml"
        nested_dir = tasks_dir / "feature-user"
        nested_dir.mkdir()
        spec2 = SimpleTaskSpec(
            schema_version="1.0",
            branch="feature-user/auth",  # Different branch, same normalization!
            title="Second Task",
            original_prompt="Test",
            status=TaskStatus.NOT_STARTED,
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Test", completed=False)
            ],
        )
        write_task_file(nested_dir / "auth.yml", spec2, update_timestamp=False)

        with patch("simpletask.commands.migrate.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_project
            mock_project.return_value.tasks_dir = tasks_dir

            # Should detect collision and show both branch names
            with pytest.raises(typer.Exit):
                migrate(dry_run=False, force=False)

        # Check that output includes both branch names
        captured = capsys.readouterr()
        assert "feature/user-auth" in captured.out, "Should show first branch name"
        assert "feature-user/auth" in captured.out, "Should show second branch name"
        assert "collides with" in captured.out, "Should clearly indicate collision"
        assert "feature-user-auth.yml" in captured.out, "Should show normalized filename"

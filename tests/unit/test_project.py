"""Tests for project management utilities."""

from unittest.mock import Mock, patch

import pytest
from simpletask.core.project import (
    Project,
    ensure_project,
    find_project,
    get_task_file_path,
)


class TestProject:
    """Tests for Project class initialization."""

    def test_init_with_explicit_root(self, tmp_path):
        """Test initializing Project with explicit root path."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        project = Project(root=tmp_path)
        assert project.root == tmp_path

    def test_init_finds_root(self, tmp_project):
        """Test Project finds root automatically."""
        project = Project()
        assert project.root is not None
        assert (project.root / ".git").exists()

    def test_init_no_git_repo_raises(self, tmp_path):
        """Test initializing Project without git repo raises error."""
        with patch.object(Project, "_find_root", return_value=None):
            with pytest.raises(ValueError, match="Could not find project root"):
                Project()

    def test_tasks_dir_property(self, tmp_project):
        """Test tasks_dir property returns correct path."""
        project = Project(root=tmp_project)
        assert project.tasks_dir == tmp_project / ".tasks"

    def test_get_task_file(self, tmp_project):
        """Test get_task_file returns correct path."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("feature-branch")
        assert task_file == tmp_project / ".tasks" / "feature-branch.yml"


class TestProjectGetTaskFileNormalized:
    """Tests for get_task_file with normalization."""

    def test_get_task_file_with_slash(self, tmp_project):
        """Test get_task_file normalizes slashes."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("feature/auth")
        assert task_file == tmp_project / ".tasks" / "feature-auth.yml"

    def test_get_task_file_with_special_chars(self, tmp_project):
        """Test get_task_file normalizes special characters."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("feat: add auth")
        assert task_file == tmp_project / ".tasks" / "feat-add-auth.yml"

    def test_get_task_file_with_uppercase(self, tmp_project):
        """Test get_task_file converts to lowercase."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("Feature/Auth")
        assert task_file == tmp_project / ".tasks" / "feature-auth.yml"

    def test_get_task_file_complex_normalization(self, tmp_project):
        """Test get_task_file with complex branch names."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("refactor/dry-violations-cleanup")
        assert task_file == tmp_project / ".tasks" / "refactor-dry-violations-cleanup.yml"


class TestProjectFindRoot:
    """Tests for Project._find_root() static method."""

    def test_find_root_current_dir(self, tmp_path, monkeypatch):
        """Test finding root in current directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        root = Project._find_root()
        assert root == tmp_path

    def test_find_root_parent_dir(self, tmp_path, monkeypatch):
        """Test finding root in parent directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "src" / "nested"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = Project._find_root()
        assert root == tmp_path

    def test_find_root_not_found(self, tmp_path, monkeypatch):
        """Test finding root returns None when not in git repo."""
        monkeypatch.chdir(tmp_path)
        root = Project._find_root()
        assert root is None


class TestProjectHasTask:
    """Tests for Project.has_task() method."""

    def test_has_task_exists(self, tmp_project_with_task):
        """Test has_task returns True for existing task file."""
        project_root, _task_file = tmp_project_with_task
        project = Project(root=project_root)
        assert project.has_task("test-feature")

    def test_has_task_not_exists(self, tmp_project):
        """Test has_task returns False for non-existent task file."""
        project = Project(root=tmp_project)
        assert not project.has_task("nonexistent-branch")


class TestProjectListTasks:
    """Tests for Project.list_tasks() method."""

    def test_list_tasks_empty(self, tmp_path):
        """Test list_tasks returns empty list when no tasks exist."""
        # Create project without .tasks directory
        project_root = tmp_path / "empty-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        tasks = project.list_tasks()
        assert tasks == []

    def test_list_tasks_single(self, tmp_project_with_task):
        """Test list_tasks returns single task."""
        project_root, _task_file = tmp_project_with_task
        project = Project(root=project_root)
        tasks = project.list_tasks()
        assert tasks == ["test-feature"]

    def test_list_tasks_multiple(self, tmp_project):
        """Test list_tasks returns multiple tasks sorted."""
        tasks_dir = tmp_project / ".tasks"

        # Create YAML files with branch field matching expected names
        yaml_a = """schema_version: '1.0'
branch: feature-a
title: Feature A
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        yaml_b = """schema_version: '1.0'
branch: feature-b
title: Feature B
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        yaml_x = """schema_version: '1.0'
branch: bugfix-x
title: Bugfix X
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        (tasks_dir / "feature-a.yml").write_text(yaml_a)
        (tasks_dir / "feature-b.yml").write_text(yaml_b)
        (tasks_dir / "bugfix-x.yml").write_text(yaml_x)

        project = Project(root=tmp_project)
        tasks = project.list_tasks()
        assert tasks == ["bugfix-x", "feature-a", "feature-b"]

    def test_list_tasks_warns_on_invalid_files(self, tmp_project, capsys):
        """Test that list_tasks silently skips invalid task files for performance."""
        tasks_dir = tmp_project / ".tasks"

        # Create invalid YAML file
        (tasks_dir / "invalid.yml").write_text("this is: not: valid: yaml:::")

        # Create valid YAML file
        valid_yaml = """schema_version: '1.0'
branch: valid-task
title: Valid Task
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        (tasks_dir / "valid-task.yml").write_text(valid_yaml)

        project = Project(root=tmp_project)
        tasks = project.list_tasks()

        # Should only include the valid task (invalid file skipped silently)
        assert tasks == ["valid-task"]

        # Performance optimization: no warnings during lightweight listing
        # Full validation happens when files are actually loaded
        captured = capsys.readouterr()
        assert captured.out == ""  # No output during listing

    def test_list_tasks_ignores_directories(self, tmp_project):
        """Test list_tasks ignores directories."""
        tasks_dir = tmp_project / ".tasks"

        # Create YAML with branch matching expected name
        yaml_content = """schema_version: '1.0'
branch: feature
title: Feature
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        (tasks_dir / "feature.yml").write_text(yaml_content)
        (tasks_dir / "subdir").mkdir()

        project = Project(root=tmp_project)
        tasks = project.list_tasks()
        assert tasks == ["feature"]

    def test_list_tasks_no_tasks_dir(self, tmp_path):
        """Test list_tasks returns empty when .tasks/ doesn't exist."""
        # Create project without tasks directory
        project_root = tmp_path / "no-tasks-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        tasks = project.list_tasks()
        assert tasks == []


class TestProjectIsGitProject:
    """Tests for Project.is_git_project() method."""

    @patch("simpletask.core.project.is_git_repo")
    def test_is_git_project_true(self, mock_is_git_repo, tmp_project):
        """Test is_git_project returns True for git repo."""
        mock_is_git_repo.return_value = True
        project = Project(root=tmp_project)
        assert project.is_git_project()
        mock_is_git_repo.assert_called_once_with(tmp_project)

    @patch("simpletask.core.project.is_git_repo")
    def test_is_git_project_false(self, mock_is_git_repo, tmp_project):
        """Test is_git_project returns False for non-git directory."""
        mock_is_git_repo.return_value = False
        project = Project(root=tmp_project)
        assert not project.is_git_project()


class TestProjectEnsureTasksDir:
    """Tests for Project.ensure_tasks_dir() method."""

    def test_ensure_tasks_dir_creates(self, tmp_path):
        """Test ensure_tasks_dir creates directory if missing."""
        # Create project without tasks directory
        project_root = tmp_path / "no-tasks-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        assert not project.tasks_dir.exists()

        result = project.ensure_tasks_dir()
        assert result == project.tasks_dir
        assert project.tasks_dir.exists()
        assert project.tasks_dir.is_dir()

    def test_ensure_tasks_dir_exists(self, tmp_project):
        """Test ensure_tasks_dir works when directory already exists."""
        project = Project(root=tmp_project)
        # tasks_dir already exists from tmp_project fixture
        assert project.tasks_dir.exists()

        result = project.ensure_tasks_dir()
        assert result == project.tasks_dir
        assert project.tasks_dir.exists()


class TestFindProject:
    """Tests for find_project() function."""

    @patch.object(Project, "_find_root")
    def test_find_project_success(self, mock_find_root, tmp_project):
        """Test find_project returns Project when found."""
        mock_find_root.return_value = tmp_project
        project = find_project()
        assert project is not None
        assert isinstance(project, Project)
        assert project.root == tmp_project

    @patch.object(Project, "_find_root")
    def test_find_project_not_found(self, mock_find_root):
        """Test find_project returns None when not found."""
        mock_find_root.return_value = None
        project = find_project()
        assert project is None

    @patch.object(Project, "_find_root")
    def test_find_project_init_error(self, mock_find_root, tmp_path):
        """Test find_project returns None when Project init raises."""
        mock_find_root.return_value = tmp_path
        # Second call will raise ValueError in __init__
        with patch.object(Project, "__init__", side_effect=ValueError("Error")):
            project = find_project()
            assert project is None


class TestEnsureProject:
    """Tests for ensure_project() function."""

    @patch("simpletask.core.project.find_project")
    def test_ensure_project_success(self, mock_find_project, tmp_project):
        """Test ensure_project returns project when found."""
        mock_project = Mock(spec=Project)
        mock_find_project.return_value = mock_project
        project = ensure_project()
        assert project == mock_project

    @patch("simpletask.core.project.find_project")
    def test_ensure_project_not_found(self, mock_find_project):
        """Test ensure_project raises when project not found."""
        mock_find_project.return_value = None
        with pytest.raises(ValueError, match="Not in a git repository"):
            ensure_project()


class TestGetTaskFilePath:
    """Tests for get_task_file_path() function."""

    @patch("simpletask.core.project.ensure_project")
    def test_get_task_file_explicit_branch(self, mock_ensure_project, tmp_project):
        """Test get_task_file_path with explicit branch."""
        mock_project = Mock(spec=Project)
        mock_project.get_task_file.return_value = tmp_project / ".tasks" / "test.yml"
        mock_ensure_project.return_value = mock_project

        result = get_task_file_path("test-branch")
        assert result == tmp_project / ".tasks" / "test.yml"
        mock_project.get_task_file.assert_called_once_with("test-branch")

    @patch("simpletask.core.project.current_branch")
    @patch("simpletask.core.project.ensure_project")
    def test_get_task_file_current_branch(
        self, mock_ensure_project, mock_current_branch, tmp_project
    ):
        """Test get_task_file_path uses current branch."""
        mock_project = Mock(spec=Project)
        mock_project.get_task_file.return_value = tmp_project / ".tasks" / "main.yml"
        mock_ensure_project.return_value = mock_project
        mock_current_branch.return_value = "main"

        result = get_task_file_path()
        assert result == tmp_project / ".tasks" / "main.yml"
        mock_current_branch.assert_called_once()
        mock_project.get_task_file.assert_called_once_with("main")

    @patch("simpletask.core.project.current_branch")
    @patch("simpletask.core.project.ensure_project")
    def test_get_task_file_detached_head(self, mock_ensure_project, mock_current_branch):
        """Test get_task_file_path raises on detached HEAD."""
        mock_ensure_project.return_value = Mock(spec=Project)
        mock_current_branch.return_value = None

        with pytest.raises(ValueError, match="Not on a git branch"):
            get_task_file_path()


class TestProjectListTasksByMtime:
    """Tests for Project.list_tasks_by_mtime() method."""

    def test_list_tasks_by_mtime_empty(self, tmp_path):
        """Test list_tasks_by_mtime returns empty list when no tasks exist."""
        # Create project without .tasks directory
        project_root = tmp_path / "empty-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        tasks = project.list_tasks_by_mtime()
        assert tasks == []

    def test_list_tasks_by_mtime_single(self, tmp_project_with_task):
        """Test list_tasks_by_mtime returns single task with mtime."""
        project_root, task_file = tmp_project_with_task
        project = Project(root=project_root)
        tasks = project.list_tasks_by_mtime()

        assert len(tasks) == 1
        branch, path, mtime = tasks[0]
        assert branch == "test-feature"
        assert path == task_file
        # Verify mtime is a datetime object
        from datetime import datetime

        assert isinstance(mtime, datetime)

    def test_list_tasks_by_mtime_multiple_oldest_first(self, tmp_project):
        """Test list_tasks_by_mtime returns multiple tasks sorted oldest to newest."""
        import time
        from datetime import datetime

        tasks_dir = tmp_project / ".tasks"

        # Create YAML files with different modification times
        yaml_a = """schema_version: '1.0'
branch: feature-a
title: Feature A
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        yaml_b = """schema_version: '1.0'
branch: feature-b
title: Feature B
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        yaml_c = """schema_version: '1.0'
branch: feature-c
title: Feature C
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""

        # Write files with delays to ensure different mtimes
        (tasks_dir / "feature-a.yml").write_text(yaml_a)
        time.sleep(0.01)  # Small delay to ensure different mtime
        (tasks_dir / "feature-b.yml").write_text(yaml_b)
        time.sleep(0.01)
        (tasks_dir / "feature-c.yml").write_text(yaml_c)

        project = Project(root=tmp_project)
        tasks = project.list_tasks_by_mtime()

        # Should have 3 tasks
        assert len(tasks) == 3

        # Extract branches and mtimes
        branches = [t[0] for t in tasks]
        mtimes = [t[2] for t in tasks]

        # Verify all items are tuples with 3 elements
        for task in tasks:
            assert len(task) == 3
            branch, path, mtime = task
            assert isinstance(branch, str)
            assert isinstance(mtime, datetime)

        # Verify oldest to newest ordering
        assert branches == ["feature-a", "feature-b", "feature-c"]

        # Verify mtimes are in ascending order
        for i in range(len(mtimes) - 1):
            assert mtimes[i] <= mtimes[i + 1], "Tasks should be sorted oldest to newest"

    def test_list_tasks_by_mtime_warns_on_invalid_files(self, tmp_project, capsys):
        """Test that list_tasks_by_mtime silently skips invalid task files for performance."""
        tasks_dir = tmp_project / ".tasks"

        # Create invalid YAML file
        (tasks_dir / "invalid.yml").write_text("this is: not: valid: yaml:::")

        # Create valid YAML file
        valid_yaml = """schema_version: '1.0'
branch: valid-task
title: Valid Task
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        (tasks_dir / "valid-task.yml").write_text(valid_yaml)

        project = Project(root=tmp_project)
        tasks = project.list_tasks_by_mtime()

        # Should only include the valid task (invalid file skipped silently)
        assert len(tasks) == 1
        assert tasks[0][0] == "valid-task"

        # Performance optimization: no warnings during lightweight listing
        # Full validation happens when files are actually loaded
        captured = capsys.readouterr()
        assert captured.out == ""  # No output during listing

    def test_list_tasks_by_mtime_ignores_directories(self, tmp_project):
        """Test list_tasks_by_mtime ignores directories."""
        tasks_dir = tmp_project / ".tasks"

        # Create YAML with branch matching expected name
        yaml_content = """schema_version: '1.0'
branch: feature
title: Feature
original_prompt: Test
created: '2024-01-01T00:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
"""
        (tasks_dir / "feature.yml").write_text(yaml_content)
        (tasks_dir / "subdir").mkdir()

        project = Project(root=tmp_project)
        tasks = project.list_tasks_by_mtime()

        assert len(tasks) == 1
        assert tasks[0][0] == "feature"

    def test_list_tasks_by_mtime_no_tasks_dir(self, tmp_path):
        """Test list_tasks_by_mtime returns empty when .tasks/ doesn't exist."""
        # Create project without tasks directory
        project_root = tmp_path / "no-tasks-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        tasks = project.list_tasks_by_mtime()
        assert tasks == []

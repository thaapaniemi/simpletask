"""Tests for project management utilities."""

from pathlib import Path
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
        assert project.tasks_dir == tmp_project / "tasks"

    def test_get_task_file(self, tmp_project):
        """Test get_task_file returns correct path."""
        project = Project(root=tmp_project)
        task_file = project.get_task_file("feature-branch")
        assert task_file == tmp_project / "tasks" / "feature-branch.yml"


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
        project_root, task_file = tmp_project_with_task
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
        # Create project without tasks directory
        project_root = tmp_path / "empty-project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project = Project(root=project_root)
        tasks = project.list_tasks()
        assert tasks == []

    def test_list_tasks_single(self, tmp_project_with_task):
        """Test list_tasks returns single task."""
        project_root, task_file = tmp_project_with_task
        project = Project(root=project_root)
        tasks = project.list_tasks()
        assert tasks == ["test-feature"]

    def test_list_tasks_multiple(self, tmp_project, sample_yaml_content):
        """Test list_tasks returns multiple tasks sorted."""
        tasks_dir = tmp_project / "tasks"
        (tasks_dir / "feature-a.yml").write_text(sample_yaml_content)
        (tasks_dir / "feature-b.yml").write_text(sample_yaml_content)
        (tasks_dir / "bugfix-x.yml").write_text(sample_yaml_content)

        project = Project(root=tmp_project)
        tasks = project.list_tasks()
        assert tasks == ["bugfix-x", "feature-a", "feature-b"]

    def test_list_tasks_ignores_non_yml(self, tmp_project, sample_yaml_content):
        """Test list_tasks ignores non-yml files."""
        tasks_dir = tmp_project / "tasks"
        (tasks_dir / "feature.yml").write_text(sample_yaml_content)
        (tasks_dir / "README.md").write_text("# Notes")
        (tasks_dir / "backup.txt").write_text("backup")

        project = Project(root=tmp_project)
        tasks = project.list_tasks()
        assert tasks == ["feature"]

    def test_list_tasks_ignores_directories(self, tmp_project, sample_yaml_content):
        """Test list_tasks ignores directories."""
        tasks_dir = tmp_project / "tasks"
        (tasks_dir / "feature.yml").write_text(sample_yaml_content)
        (tasks_dir / "subdir").mkdir()

        project = Project(root=tmp_project)
        tasks = project.list_tasks()
        assert tasks == ["feature"]

    def test_list_tasks_no_tasks_dir(self, tmp_path):
        """Test list_tasks returns empty when tasks/ doesn't exist."""
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
        mock_project.get_task_file.return_value = tmp_project / "tasks" / "test.yml"
        mock_ensure_project.return_value = mock_project

        result = get_task_file_path("test-branch")
        assert result == tmp_project / "tasks" / "test.yml"
        mock_project.get_task_file.assert_called_once_with("test-branch")

    @patch("simpletask.core.project.current_branch")
    @patch("simpletask.core.project.ensure_project")
    def test_get_task_file_current_branch(
        self, mock_ensure_project, mock_current_branch, tmp_project
    ):
        """Test get_task_file_path uses current branch."""
        mock_project = Mock(spec=Project)
        mock_project.get_task_file.return_value = tmp_project / "tasks" / "main.yml"
        mock_ensure_project.return_value = mock_project
        mock_current_branch.return_value = "main"

        result = get_task_file_path()
        assert result == tmp_project / "tasks" / "main.yml"
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

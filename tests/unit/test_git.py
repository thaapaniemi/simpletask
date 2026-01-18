"""Tests for git operations."""

from pathlib import Path
from unittest.mock import Mock, patch

from simpletask.core import git as git_module
from simpletask.core.git import (
    branch_exists,
    create_branch,
    current_branch,
    get_git_repo,
    is_git_repo,
    is_main_branch,
)


class TestIsGitRepo:
    """Tests for is_git_repo() function."""

    @patch("simpletask.core.git.GIT_AVAILABLE", True)
    @patch("simpletask.core.git.git.Repo")
    def test_is_git_repo_true(self, mock_repo_class):
        """Test is_git_repo returns True for git repo."""
        mock_repo_class.return_value = Mock()
        assert is_git_repo(Path("/fake/path"))
        mock_repo_class.assert_called_once_with(Path("/fake/path"), search_parent_directories=True)

    @patch("simpletask.core.git.GIT_AVAILABLE", True)
    @patch("simpletask.core.git.git.Repo")
    def test_is_git_repo_false(self, mock_repo_class):
        """Test is_git_repo returns False for non-git directory."""
        mock_repo_class.side_effect = git_module.InvalidGitRepositoryError
        assert not is_git_repo(Path("/fake/path"))

    @patch("simpletask.core.git.GIT_AVAILABLE", False)
    def test_is_git_repo_no_git_available(self):
        """Test is_git_repo returns False when git not available."""
        assert not is_git_repo(Path("/fake/path"))

    @patch("simpletask.core.git.GIT_AVAILABLE", True)
    @patch("simpletask.core.git.git.Repo")
    @patch("simpletask.core.git.Path.cwd")
    def test_is_git_repo_default_path(self, mock_cwd, mock_repo_class):
        """Test is_git_repo uses cwd when no path provided."""
        mock_cwd.return_value = Path("/current/dir")
        mock_repo_class.return_value = Mock()
        assert is_git_repo()
        mock_repo_class.assert_called_once_with(
            Path("/current/dir"), search_parent_directories=True
        )


class TestGetGitRepo:
    """Tests for get_git_repo() function."""

    @patch("simpletask.core.git.GIT_AVAILABLE", True)
    @patch("simpletask.core.git.git.Repo")
    def test_get_git_repo_success(self, mock_repo_class):
        """Test get_git_repo returns repo object."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        result = get_git_repo(Path("/fake/path"))
        assert result == mock_repo

    @patch("simpletask.core.git.GIT_AVAILABLE", True)
    @patch("simpletask.core.git.git.Repo")
    def test_get_git_repo_not_found(self, mock_repo_class):
        """Test get_git_repo returns None for non-git directory."""
        mock_repo_class.side_effect = git_module.InvalidGitRepositoryError
        result = get_git_repo(Path("/fake/path"))
        assert result is None

    @patch("simpletask.core.git.GIT_AVAILABLE", False)
    def test_get_git_repo_no_git_available(self):
        """Test get_git_repo returns None when git not available."""
        result = get_git_repo(Path("/fake/path"))
        assert result is None


class TestCurrentBranch:
    """Tests for current_branch() function."""

    @patch("simpletask.core.git.get_git_repo")
    def test_current_branch_success(self, mock_get_repo):
        """Test current_branch returns branch name."""
        mock_repo = Mock()
        mock_repo.head.is_detached = False
        mock_repo.active_branch.name = "feature-branch"
        mock_get_repo.return_value = mock_repo

        result = current_branch()
        assert result == "feature-branch"

    @patch("simpletask.core.git.get_git_repo")
    def test_current_branch_detached_head(self, mock_get_repo):
        """Test current_branch returns None for detached HEAD."""
        mock_repo = Mock()
        mock_repo.head.is_detached = True
        mock_get_repo.return_value = mock_repo

        result = current_branch()
        assert result is None

    @patch("simpletask.core.git.get_git_repo")
    def test_current_branch_no_repo(self, mock_get_repo):
        """Test current_branch returns None when not in repo."""
        mock_get_repo.return_value = None
        result = current_branch()
        assert result is None


class TestIsMainBranch:
    """Tests for is_main_branch() function."""

    def test_is_main_branch_main(self):
        """Test is_main_branch returns True for 'main'."""
        assert is_main_branch("main")

    def test_is_main_branch_master(self):
        """Test is_main_branch returns True for 'master'."""
        assert is_main_branch("master")

    def test_is_main_branch_feature(self):
        """Test is_main_branch returns False for feature branch."""
        assert not is_main_branch("feature-branch")

    @patch("simpletask.core.git.current_branch")
    def test_is_main_branch_current_main(self, mock_current_branch):
        """Test is_main_branch uses current branch when not specified."""
        mock_current_branch.return_value = "main"
        assert is_main_branch()

    @patch("simpletask.core.git.current_branch")
    def test_is_main_branch_current_none(self, mock_current_branch):
        """Test is_main_branch returns False when current branch is None."""
        mock_current_branch.return_value = None
        assert not is_main_branch()

    def test_is_main_branch_none_explicit(self):
        """Test is_main_branch returns False for None."""
        assert not is_main_branch(None)


class TestCreateBranch:
    """Tests for create_branch() function."""

    @patch("simpletask.core.git.get_git_repo")
    def test_create_branch_success(self, mock_get_repo):
        """Test create_branch creates and checks out new branch."""
        mock_repo = Mock()
        mock_repo.heads = []
        mock_branch = Mock()
        mock_repo.create_head.return_value = mock_branch
        mock_get_repo.return_value = mock_repo

        success, message = create_branch("new-feature")
        assert success
        assert "Created and checked out branch 'new-feature'" in message
        mock_repo.create_head.assert_called_once_with("new-feature")
        mock_branch.checkout.assert_called_once()

    @patch("simpletask.core.git.get_git_repo")
    def test_create_branch_already_exists(self, mock_get_repo):
        """Test create_branch fails when branch exists."""
        mock_repo = Mock()
        mock_repo.heads = ["new-feature"]
        mock_get_repo.return_value = mock_repo

        success, message = create_branch("new-feature")
        assert not success
        assert "already exists" in message

    @patch("simpletask.core.git.get_git_repo")
    def test_create_branch_no_repo(self, mock_get_repo):
        """Test create_branch fails when not in repo."""
        mock_get_repo.return_value = None

        success, message = create_branch("new-feature")
        assert not success
        assert "Not a git repository" in message

    @patch("simpletask.core.git.get_git_repo")
    def test_create_branch_git_error(self, mock_get_repo):
        """Test create_branch handles GitCommandError."""
        mock_repo = Mock()
        mock_repo.heads = []
        mock_repo.create_head.side_effect = git_module.GitCommandError("git error")
        mock_get_repo.return_value = mock_repo

        success, message = create_branch("new-feature")
        assert not success
        assert "Git error" in message

    @patch("simpletask.core.git.get_git_repo")
    def test_create_branch_generic_error(self, mock_get_repo):
        """Test create_branch handles generic exceptions."""
        mock_repo = Mock()
        mock_repo.heads = []
        mock_repo.create_head.side_effect = Exception("Unknown error")
        mock_get_repo.return_value = mock_repo

        success, message = create_branch("new-feature")
        assert not success
        assert "Error creating branch" in message


class TestBranchExists:
    """Tests for branch_exists() function."""

    @patch("simpletask.core.git.get_git_repo")
    def test_branch_exists_true(self, mock_get_repo):
        """Test branch_exists returns True for existing branch."""
        mock_repo = Mock()
        mock_repo.heads = ["main", "feature-branch", "bugfix"]
        mock_get_repo.return_value = mock_repo

        assert branch_exists("feature-branch")

    @patch("simpletask.core.git.get_git_repo")
    def test_branch_exists_false(self, mock_get_repo):
        """Test branch_exists returns False for non-existent branch."""
        mock_repo = Mock()
        mock_repo.heads = ["main", "feature-branch"]
        mock_get_repo.return_value = mock_repo

        assert not branch_exists("nonexistent")

    @patch("simpletask.core.git.get_git_repo")
    def test_branch_exists_no_repo(self, mock_get_repo):
        """Test branch_exists returns False when not in repo."""
        mock_get_repo.return_value = None
        assert not branch_exists("some-branch")

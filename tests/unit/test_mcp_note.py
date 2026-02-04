"""Unit tests for MCP note tool."""

import subprocess

import pytest
from simpletask.mcp.models import SimpleTaskNoteResponse, SimpleTaskWriteResponse
from simpletask.mcp.server import new, note, task


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """Create temporary git project for testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def task_project(temp_project):
    """Create project with existing task file and tasks."""
    new(branch="test", title="Test", prompt="Test")
    # Checkout the test branch so MCP tools can auto-detect it
    subprocess.run(["git", "checkout", "-b", "test"], cwd=temp_project, check=True)
    # Add some tasks for testing
    task(action="add", name="Task 1", goal="First task")
    task(action="add", name="Task 2", goal="Second task")
    return temp_project


class TestNoteAdd:
    """Tests for note add action."""

    def test_add_root_note(self, task_project):
        """Test adding a root-level note."""
        result = note(action="add", content="Root note")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "note_added"
        assert "root" in result.message

    def test_add_task_note(self, task_project):
        """Test adding a task-level note."""
        result = note(action="add", content="Task note", task_id="T001")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "note_added"
        assert "T001" in result.message

    def test_add_note_missing_content(self, task_project):
        """Test that missing content raises ValueError."""
        with pytest.raises(ValueError, match="'content' is required"):
            note(action="add")

    def test_add_note_invalid_task(self, task_project):
        """Test that invalid task ID raises ValueError."""
        with pytest.raises(ValueError, match="Task 'INVALID' not found"):
            note(action="add", content="Note", task_id="INVALID")


class TestNoteRemove:
    """Tests for note remove action."""

    def test_remove_root_note_by_index(self, task_project):
        """Test removing root-level note by index."""
        # Add notes first
        note(action="add", content="Note 1")
        note(action="add", content="Note 2")

        result = note(action="remove", index=0)
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "note_removed"
        assert "note 0" in result.message.lower()

    def test_remove_root_note_all(self, task_project):
        """Test removing all root-level notes."""
        note(action="add", content="Note 1")
        note(action="add", content="Note 2")

        result = note(action="remove", all=True)
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "note_removed"
        assert "all notes" in result.message.lower()

    def test_remove_task_note_by_index(self, task_project):
        """Test removing task-level note by index."""
        note(action="add", content="Task note 1", task_id="T001")
        note(action="add", content="Task note 2", task_id="T001")

        result = note(action="remove", index=0, task_id="T001")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert "T001" in result.message

    def test_remove_note_missing_params(self, task_project):
        """Test that missing index and all raises ValueError."""
        note(action="add", content="Note")

        with pytest.raises(ValueError, match="Either 'index' or 'all=True' is required"):
            note(action="remove")

    def test_remove_note_invalid_index(self, task_project):
        """Test that invalid index raises ValueError."""
        note(action="add", content="Note")

        with pytest.raises(ValueError, match="Invalid note index"):
            note(action="remove", index=99)


class TestNoteList:
    """Tests for note list action."""

    def test_list_empty_notes(self, task_project):
        """Test listing when no notes exist."""
        result = note(action="list")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.action == "note_list"
        assert result.root_notes is None
        assert result.task_notes == {}
        assert result.total_count == 0

    def test_list_root_notes_only(self, task_project):
        """Test listing root-level notes."""
        note(action="add", content="Root note 1")
        note(action="add", content="Root note 2")

        result = note(action="list")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.root_notes == ["Root note 1", "Root note 2"]
        assert result.total_count == 2

    def test_list_task_notes_only(self, task_project):
        """Test listing task-level notes."""
        note(action="add", content="Task note", task_id="T001")

        result = note(action="list")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.task_notes == {"T001": ["Task note"]}
        assert result.total_count == 1

    def test_list_mixed_notes(self, task_project):
        """Test listing both root and task notes."""
        note(action="add", content="Root note")
        note(action="add", content="Task 1 note", task_id="T001")
        note(action="add", content="Task 2 note", task_id="T002")

        result = note(action="list")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.root_notes == ["Root note"]
        assert result.task_notes == {
            "T001": ["Task 1 note"],
            "T002": ["Task 2 note"],
        }
        assert result.total_count == 3

    def test_list_specific_task(self, task_project):
        """Test listing notes for specific task."""
        note(action="add", content="Root note")
        note(action="add", content="Task 1 note", task_id="T001")
        note(action="add", content="Task 2 note", task_id="T002")

        result = note(action="list", task_id="T001")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.root_notes == ["Root note"]  # Still includes root notes
        assert result.task_notes == {"T001": ["Task 1 note"]}  # Only T001
        assert result.total_count == 2

    def test_list_root_only(self, task_project):
        """Test listing only root notes."""
        note(action="add", content="Root note")
        note(action="add", content="Task note", task_id="T001")

        result = note(action="list", root_only=True)
        assert isinstance(result, SimpleTaskNoteResponse)
        assert result.root_notes == ["Root note"]
        assert result.task_notes == {}
        assert result.total_count == 1

    def test_list_sparse_dict(self, task_project):
        """Test that task_notes dict is sparse (only tasks with notes)."""
        # Add note to T001 only, not T002
        note(action="add", content="Task 1 note", task_id="T001")

        result = note(action="list")
        assert isinstance(result, SimpleTaskNoteResponse)
        assert "T001" in result.task_notes
        assert "T002" not in result.task_notes


class TestNoteResponseModels:
    """Tests for note response model structure."""

    def test_list_response_structure(self, task_project):
        """Test that list response has all required fields."""
        note(action="add", content="Test note")
        result = note(action="list")

        assert hasattr(result, "action")
        assert hasattr(result, "root_notes")
        assert hasattr(result, "task_notes")
        assert hasattr(result, "total_count")
        assert hasattr(result, "file_path")
        assert hasattr(result, "summary")

    def test_write_response_structure(self, task_project):
        """Test that write response has all required fields."""
        result = note(action="add", content="Test note")

        assert hasattr(result, "success")
        assert hasattr(result, "action")
        assert hasattr(result, "message")
        assert hasattr(result, "file_path")
        assert hasattr(result, "summary")

"""Unit tests for note_ops module.

Tests cover:
- add_note() - Add notes to root and task-level
- remove_note() - Remove notes by index or all
- list_notes() - List notes with filters
"""

import pytest
from simpletask.core.models import SimpleTaskSpec
from simpletask.core.note_ops import add_note, list_notes, remove_note
from simpletask.core.yaml_parser import parse_task_file


class TestAddNote:
    """Test add_note function."""

    def test_add_root_note_to_empty(self, tmp_task_file):
        """Add root-level note when notes field is None."""
        spec = parse_task_file(tmp_task_file)
        assert spec.notes is None

        spec = add_note(spec, content="First note")
        assert spec.notes == ["First note"]

    def test_add_root_note_to_existing(self, tmp_task_file):
        """Add root-level note to existing notes."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Existing note"]

        spec = add_note(spec, content="Second note")
        assert spec.notes == ["Existing note", "Second note"]

    def test_add_task_note(self, tmp_task_file):
        """Add note to specific task."""
        spec = parse_task_file(tmp_task_file)
        assert spec.tasks is not None
        assert len(spec.tasks) > 0

        task_id = spec.tasks[0].id
        spec = add_note(spec, content="Task note", task_id=task_id)

        assert spec.tasks[0].notes == ["Task note"]

    def test_add_task_note_to_existing(self, tmp_task_file):
        """Add note to task with existing notes."""
        spec = parse_task_file(tmp_task_file)
        task_id = spec.tasks[0].id
        spec.tasks[0].notes = ["Existing task note"]

        spec = add_note(spec, content="Second task note", task_id=task_id)
        assert spec.tasks[0].notes == ["Existing task note", "Second task note"]

    def test_add_task_note_invalid_task(self, tmp_task_file):
        """Raise error for invalid task ID."""
        spec = parse_task_file(tmp_task_file)

        with pytest.raises(ValueError, match="Task 'INVALID' not found"):
            add_note(spec, content="Note", task_id="INVALID")

    def test_add_task_note_no_tasks(self):
        """Raise error when spec has no tasks."""
        from datetime import datetime

        from simpletask.core.models import AcceptanceCriterion

        spec = SimpleTaskSpec(
            branch="test",
            title="Test",
            original_prompt="Test",
            created=datetime.now(),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Test criterion")],
        )

        with pytest.raises(ValueError, match="No tasks defined in spec"):
            add_note(spec, content="Note", task_id="T001")


class TestRemoveNote:
    """Test remove_note function."""

    def test_remove_root_note_by_index(self, tmp_task_file):
        """Remove root-level note by index."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Note 1", "Note 2", "Note 3"]

        spec = remove_note(spec, index=1)
        assert spec.notes == ["Note 1", "Note 3"]

    def test_remove_root_note_all(self, tmp_task_file):
        """Remove all root-level notes."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Note 1", "Note 2"]

        spec = remove_note(spec, all=True)
        assert spec.notes is None

    def test_remove_root_note_last_one(self, tmp_task_file):
        """Set notes to None when removing last note."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Only note"]

        spec = remove_note(spec, index=0)
        assert spec.notes is None

    def test_remove_root_note_invalid_index(self, tmp_task_file):
        """Raise error for invalid index."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Note 1"]

        with pytest.raises(ValueError, match="Invalid note index: 5"):
            remove_note(spec, index=5)

    def test_remove_task_note_by_index(self, tmp_task_file):
        """Remove task-level note by index."""
        spec = parse_task_file(tmp_task_file)
        task_id = spec.tasks[0].id
        spec.tasks[0].notes = ["Task note 1", "Task note 2"]

        spec = remove_note(spec, index=0, task_id=task_id)
        assert spec.tasks[0].notes == ["Task note 2"]

    def test_remove_task_note_all(self, tmp_task_file):
        """Remove all task-level notes."""
        spec = parse_task_file(tmp_task_file)
        task_id = spec.tasks[0].id
        spec.tasks[0].notes = ["Task note 1", "Task note 2"]

        spec = remove_note(spec, all=True, task_id=task_id)
        assert spec.tasks[0].notes is None

    def test_remove_task_note_invalid_task(self, tmp_task_file):
        """Raise error for invalid task ID."""
        spec = parse_task_file(tmp_task_file)

        with pytest.raises(ValueError, match="Task 'INVALID' not found"):
            remove_note(spec, index=0, task_id="INVALID")

    def test_remove_note_no_index_no_all(self, tmp_task_file):
        """Raise error when neither index nor all is provided."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Note"]

        with pytest.raises(ValueError, match="Must provide either index or all=True"):
            remove_note(spec)


class TestListNotes:
    """Test list_notes function."""

    def test_list_all_notes_empty(self, tmp_task_file):
        """List notes when none exist."""
        spec = parse_task_file(tmp_task_file)
        root_notes, task_notes = list_notes(spec)

        assert root_notes is None
        assert task_notes == {}

    def test_list_root_notes_only(self, tmp_task_file):
        """List only root-level notes."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Root note 1", "Root note 2"]

        root_notes, task_notes = list_notes(spec, root_only=True)

        assert root_notes == ["Root note 1", "Root note 2"]
        assert task_notes == {}

    def test_list_all_notes(self, tmp_task_file):
        """List all notes (root + task)."""
        spec = parse_task_file(tmp_task_file)
        spec.notes = ["Root note"]
        spec.tasks[0].notes = ["Task 1 note"]

        root_notes, task_notes = list_notes(spec)

        assert root_notes == ["Root note"]
        assert task_notes == {spec.tasks[0].id: ["Task 1 note"]}

    def test_list_specific_task_notes(self, tmp_task_file):
        """List notes for specific task only."""
        spec = parse_task_file(tmp_task_file)
        spec.tasks[0].notes = ["Task 1 note"]
        if len(spec.tasks) > 1:
            spec.tasks[1].notes = ["Task 2 note"]

        task_id = spec.tasks[0].id
        root_notes, task_notes = list_notes(spec, task_id=task_id)

        assert root_notes == spec.notes
        assert task_notes == {task_id: ["Task 1 note"]}

    def test_list_specific_task_no_notes(self, tmp_task_file):
        """List notes for task with no notes."""
        spec = parse_task_file(tmp_task_file)
        task_id = spec.tasks[0].id

        root_notes, task_notes = list_notes(spec, task_id=task_id)

        assert root_notes == spec.notes
        assert task_notes == {}

    def test_list_specific_task_invalid(self, tmp_task_file):
        """Raise error for invalid task ID."""
        spec = parse_task_file(tmp_task_file)

        with pytest.raises(ValueError, match="Task 'INVALID' not found"):
            list_notes(spec, task_id="INVALID")

    def test_list_notes_sparse_dict(self, tmp_task_file):
        """Only include tasks with notes in result dict."""
        spec = parse_task_file(tmp_task_file)
        # Add notes to first task only
        spec.tasks[0].notes = ["Task 1 note"]

        _root_notes, task_notes = list_notes(spec)

        assert len(task_notes) == 1
        assert spec.tasks[0].id in task_notes

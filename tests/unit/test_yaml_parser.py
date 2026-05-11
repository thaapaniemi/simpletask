"""Unit tests for yaml_parser module.

Tests cover:
- parse_task_file() - Valid/invalid YAML parsing
- write_task_file() - Writing task files
- update_task_status() - Task status updates
- update_criterion_status() - Criterion status updates
- InvalidTaskFileError - Exception handling
"""

import pytest
import yaml
from simpletask.core.models import (
    TaskStatus,
    ToolName,
    WorkflowRunner,
)
from simpletask.core.yaml_parser import (
    InvalidTaskFileError,
    _bump_schema_version_if_canonical,
    parse_task_file,
    update_criterion_status,
    update_task_status,
    write_task_file,
)


class TestParseTaskFile:
    """Test parse_task_file function."""

    def test_parse_valid_file(self, tmp_task_file):
        """Parse valid task file successfully."""
        spec = parse_task_file(tmp_task_file)

        assert spec.branch == "test-feature"
        assert spec.title == "Test Feature"
        assert len(spec.acceptance_criteria) == 2
        assert len(spec.tasks) == 2

    def test_file_not_found(self, tmp_path):
        """Non-existent file raises FileNotFoundError."""
        non_existent = tmp_path / "missing.yml"

        with pytest.raises(FileNotFoundError) as exc_info:
            parse_task_file(non_existent)

        assert str(non_existent) in str(exc_info.value)

    def test_invalid_yaml_syntax(self, tmp_path):
        """Invalid YAML syntax raises InvalidTaskFileError."""
        task_file = tmp_path / "invalid.yml"
        content = """branch: test
title: Test"
  bad: indentation
"""
        task_file.write_text(content)

        with pytest.raises(InvalidTaskFileError) as exc_info:
            parse_task_file(task_file)

        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_yaml_not_dict(self, tmp_path):
        """YAML that doesn't parse to dict raises InvalidTaskFileError."""
        task_file = tmp_path / "list.yml"
        content = """- This is a list
- Not a dict
"""
        task_file.write_text(content)

        with pytest.raises(InvalidTaskFileError) as exc_info:
            parse_task_file(task_file)

        assert "Expected a dictionary" in str(exc_info.value)

    def test_schema_validation_error(self, tmp_path):
        """YAML that doesn't match schema raises InvalidTaskFileError."""
        task_file = tmp_path / "invalid_schema.yml"
        content = """branch: test
title: Test
# Missing required fields: original_prompt, created, updated, acceptance_criteria
"""
        task_file.write_text(content)

        with pytest.raises(InvalidTaskFileError) as exc_info:
            parse_task_file(task_file)

        assert "Invalid task file schema" in str(exc_info.value)


class TestWriteTaskFile:
    """Test write_task_file function."""

    def test_write_valid_file(self, tmp_path, sample_spec):
        """Write valid task file successfully."""
        task_file = tmp_path / "test.yml"
        write_task_file(task_file, sample_spec)

        assert task_file.exists()
        content = task_file.read_text()
        assert "branch: test-feature" in content
        assert "title: Test Feature" in content

    def test_write_creates_parent_directories(self, tmp_path, sample_spec):
        """write_task_file creates parent directories if needed."""
        nested_file = tmp_path / "nested" / "path" / "task.yml"
        write_task_file(nested_file, sample_spec)

        assert nested_file.exists()
        assert nested_file.parent.exists()

    def test_round_trip_parsing(self, tmp_path, sample_spec):
        """Parse → Write → Parse preserves data."""
        task_file = tmp_path / "test.yml"

        # Write
        write_task_file(task_file, sample_spec)

        # Parse
        parsed_spec = parse_task_file(task_file)

        # Verify metadata preserved
        assert parsed_spec.branch == sample_spec.branch
        assert parsed_spec.title == sample_spec.title
        assert len(parsed_spec.tasks) == len(sample_spec.tasks)
        assert len(parsed_spec.acceptance_criteria) == len(sample_spec.acceptance_criteria)


class TestBumpSchemaVersion:
    """Tests for _bump_schema_version_if_canonical — schema_version upgrade (AC3)."""

    def test_bumps_schema_version_to_1_1_when_canonical_execution_present(self):
        """schema_version is bumped to '1.1' when any section has canonical execution."""
        data = {
            "schema_version": "1.0",
            "quality_requirements": {
                "linting": {
                    "enabled": True,
                    "execution": {"kind": "tool", "tool": "ruff", "args": []},
                }
            },
        }
        result = _bump_schema_version_if_canonical(data)
        assert result["schema_version"] == "1.1"

    def test_does_not_bump_schema_version_when_no_execution(self):
        """schema_version stays unchanged when no section uses canonical execution."""
        data = {
            "schema_version": "1.0",
            "quality_requirements": {
                "linting": {"enabled": True, "tool": "ruff", "args": ["check", "."]}
            },
        }
        result = _bump_schema_version_if_canonical(data)
        assert result["schema_version"] == "1.0"

    def test_handles_missing_quality_requirements(self):
        """Data without quality_requirements is returned unchanged."""
        data = {"schema_version": "1.0", "branch": "test"}
        result = _bump_schema_version_if_canonical(data)
        assert result == {"schema_version": "1.0", "branch": "test"}

    def test_handles_non_dict_quality_requirements(self):
        """Non-dict quality_requirements value is returned unchanged."""
        data = {"schema_version": "1.0", "quality_requirements": None}
        result = _bump_schema_version_if_canonical(data)
        assert result["schema_version"] == "1.0"


class TestWriteTaskFileCanonicalOutput:
    """Integration tests: write_task_file emits canonical YAML (AC3)."""

    def test_write_strips_legacy_fields_and_bumps_schema_version(
        self, tmp_path, sample_spec_filterable
    ):
        """write_task_file removes legacy tool/args and sets schema_version:1.1 when execution present.

        sample_spec_filterable has quality_requirements built from legacy tool= kwargs, so after
        normalization the model holds both execution and tool. write_task_file must emit
        only canonical execution in the YAML.
        """
        task_file = tmp_path / "task.yml"
        write_task_file(task_file, sample_spec_filterable)

        data = yaml.safe_load(task_file.read_text())
        linting = data["quality_requirements"]["linting"]

        assert "execution" in linting, "canonical execution key must be present"
        assert "tool" not in linting, "legacy tool key must be stripped"
        assert "args" not in linting, "legacy args key must be stripped"
        assert data["schema_version"] == "1.1"

    def test_write_canonical_round_trip(self, tmp_path, sample_spec_filterable):
        """Spec written in canonical form can be read back and still has execution spec."""
        task_file = tmp_path / "task.yml"
        write_task_file(task_file, sample_spec_filterable)

        parsed = parse_task_file(task_file)
        assert parsed.quality_requirements is not None
        assert parsed.quality_requirements.linting.execution is not None
        assert parsed.quality_requirements.linting.execution.tool == ToolName.RUFF
        assert parsed.schema_version == "1.1"

    def test_write_workflow_execution_strips_legacy_and_bumps_version(
        self, tmp_path, sample_spec_filterable
    ):
        """Workflow execution spec also triggers legacy-field stripping and version bump."""
        from simpletask.core.quality_ops import update_quality_config

        updated = update_quality_config(
            sample_spec_filterable,
            "linting",
            workflow_runner=WorkflowRunner.EARTHLY,
            workflow_target="+lint",
        )
        task_file = tmp_path / "task.yml"
        write_task_file(task_file, updated)

        data = yaml.safe_load(task_file.read_text())
        linting = data["quality_requirements"]["linting"]

        assert "execution" in linting
        assert linting["execution"]["kind"] == "workflow"
        assert linting["execution"]["runner"] == "earthly"
        assert linting["execution"]["target"] == "+lint"
        assert "tool" not in linting
        assert "args" not in linting
        assert data["schema_version"] == "1.1"


class TestUpdateTaskStatus:
    """Test update_task_status function."""

    def test_update_to_completed(self, tmp_task_file):
        """Update task to completed status."""
        update_task_status(tmp_task_file, "T001", TaskStatus.COMPLETED)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].status == TaskStatus.COMPLETED

    def test_update_to_in_progress(self, tmp_task_file):
        """Update task to in_progress status."""
        update_task_status(tmp_task_file, "T001", TaskStatus.IN_PROGRESS)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_update_to_blocked(self, tmp_task_file):
        """Update task to blocked status."""
        update_task_status(tmp_task_file, "T001", TaskStatus.BLOCKED)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].status == TaskStatus.BLOCKED

    def test_update_nonexistent_task(self, tmp_task_file):
        """Updating non-existent task raises ValueError."""
        with pytest.raises(ValueError, match="Task 'T999' not found"):
            update_task_status(tmp_task_file, "T999", TaskStatus.COMPLETED)

    def test_update_no_tasks(self, tmp_path, sample_spec):
        """Raise ValueError when no tasks defined."""
        sample_spec.tasks = None
        task_file = tmp_path / "test.yml"
        write_task_file(task_file, sample_spec)

        with pytest.raises(ValueError, match="No tasks defined"):
            update_task_status(task_file, "T001", TaskStatus.COMPLETED)


class TestUpdateCriterionStatus:
    """Test update_criterion_status function."""

    def test_update_to_completed(self, tmp_task_file):
        """Update criterion to completed."""
        update_criterion_status(tmp_task_file, "AC1", completed=True)

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is True

    def test_update_to_incomplete(self, tmp_task_file):
        """Update criterion to incomplete."""
        update_criterion_status(tmp_task_file, "AC1", completed=False)

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is False

    def test_update_nonexistent_criterion(self, tmp_task_file):
        """Updating non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="Criterion 'AC999' not found"):
            update_criterion_status(tmp_task_file, "AC999", completed=True)

    def test_update_multiple_criteria(self, tmp_task_file):
        """Update multiple criteria independently."""
        update_criterion_status(tmp_task_file, "AC1", completed=True)
        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is True
        assert spec.acceptance_criteria[1].completed is False

        update_criterion_status(tmp_task_file, "AC2", completed=True)
        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is True
        assert spec.acceptance_criteria[1].completed is True

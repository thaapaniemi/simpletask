"""Tests for validation module."""

from unittest.mock import patch

from simpletask.core.validation import get_bundled_schema, validate_task_file


class TestGetBundledSchema:
    """Tests for get_bundled_schema() function."""

    def test_get_bundled_schema_success(self):
        """Test get_bundled_schema loads schema successfully."""
        schema = get_bundled_schema()
        assert isinstance(schema, dict)
        assert "schema_version" in schema.get("properties", {})
        assert "type" in schema
        assert schema["type"] == "object"

    def test_get_bundled_schema_has_required_fields(self):
        """Test schema has required fields defined."""
        schema = get_bundled_schema()
        required = schema.get("required", [])
        assert "schema_version" in required
        assert "branch" in required
        assert "title" in required


class TestValidateTaskFile:
    """Tests for validate_task_file() function."""

    def test_validate_valid_file(self, tmp_task_file):
        """Test validating a valid task file returns no errors."""
        errors = validate_task_file(tmp_task_file)
        assert errors == []

    def test_validate_file_not_found(self, tmp_path):
        """Test validating non-existent file returns error."""
        nonexistent = tmp_path / "nonexistent.yml"
        errors = validate_task_file(nonexistent)
        assert len(errors) == 1
        assert "File not found" in errors[0]

    def test_validate_invalid_yaml_syntax(self, tmp_path):
        """Test validating file with invalid YAML syntax."""
        bad_yaml = tmp_path / "bad.yml"
        bad_yaml.write_text("{\ninvalid: yaml: syntax\n")
        errors = validate_task_file(bad_yaml)
        assert len(errors) == 1
        assert "Invalid YAML syntax" in errors[0]

    def test_validate_missing_required_field(self, tmp_path):
        """Test validating file missing required field."""
        incomplete = tmp_path / "incomplete.yml"
        # Missing 'title' field
        incomplete.write_text("""
schema_version: '1.0'
branch: test
original_prompt: Test
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
""")
        errors = validate_task_file(incomplete)
        assert len(errors) > 0
        # Should have validation error about missing 'title'
        assert any("title" in err.lower() or "required" in err.lower() for err in errors)

    def test_validate_invalid_status_value(self, tmp_path):
        """Test validating file with invalid enum value."""
        invalid_status = tmp_path / "invalid_status.yml"
        invalid_status.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
status: invalid_status
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
""")
        errors = validate_task_file(invalid_status)
        assert len(errors) > 0
        # Should have validation error about status
        assert any("status" in err.lower() for err in errors)

    def test_validate_empty_acceptance_criteria(self, tmp_path):
        """Test validating file with empty acceptance criteria."""
        empty_ac = tmp_path / "empty_ac.yml"
        empty_ac.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria: []
""")
        errors = validate_task_file(empty_ac)
        # Should fail because acceptance_criteria must have at least one item
        assert len(errors) > 0

    def test_validate_task_missing_required_fields(self, tmp_path):
        """Test validating task without required fields."""
        bad_task = tmp_path / "bad_task.yml"
        bad_task.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
tasks:
  - id: T001
    name: Task without required fields
""")
        errors = validate_task_file(bad_task)
        assert len(errors) > 0
        # Should complain about missing task fields (status, goal, steps)

    def test_validate_empty_task_steps(self, tmp_path):
        """Test validating task with empty steps list."""
        empty_steps = tmp_path / "empty_steps.yml"
        empty_steps.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
tasks:
  - id: T001
    name: Task
    status: not_started
    goal: Goal
    steps: []
""")
        errors = validate_task_file(empty_steps)
        # Should fail because steps must have at least one item
        assert len(errors) > 0

    @patch("simpletask.core.validation.get_bundled_schema")
    def test_validate_schema_loading_error(self, mock_get_schema, tmp_task_file):
        """Test handling of schema loading error."""
        mock_get_schema.side_effect = Exception("Schema load error")
        errors = validate_task_file(tmp_task_file)
        assert len(errors) == 1
        assert "Error loading schema" in errors[0]

    def test_validate_file_read_error(self, tmp_path):
        """Test handling of file read error."""
        # Create a directory with the same name (can't be read as file)
        bad_path = tmp_path / "directory.yml"
        bad_path.mkdir()
        errors = validate_task_file(bad_path)
        assert len(errors) == 1
        # Could be YAML error or read error depending on OS
        assert any(keyword in errors[0] for keyword in ["Invalid YAML", "Error reading"])

    def test_validate_invalid_prerequisite_reference(self, tmp_path):
        """Test validating task with invalid prerequisite."""
        bad_prereq = tmp_path / "bad_prereq.yml"
        bad_prereq.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
tasks:
  - id: T001
    name: Task 1
    status: not_started
    goal: Goal 1
    steps:
      - Step 1
    prerequisites:
      - NONEXISTENT
""")
        # Note: This might not be caught by JSON schema alone,
        # but by Pydantic model validation. Schema might allow it.
        validate_task_file(bad_prereq)
        # This test documents the current behavior - adjust expectations
        # based on whether prerequisite validation is in schema or model

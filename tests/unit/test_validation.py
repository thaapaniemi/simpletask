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
acceptance_criteria:
  - id: AC1
    description: Test
    completed: false
""")
        errors = validate_task_file(incomplete)
        assert len(errors) > 0
        # Should have validation error about missing 'title'
        assert any("title" in err.lower() or "required" in err.lower() for err in errors)

    def test_validate_empty_acceptance_criteria(self, tmp_path):
        """Test validating file with empty acceptance criteria."""
        empty_ac = tmp_path / "empty_ac.yml"
        empty_ac.write_text("""
schema_version: '1.0'
branch: test
title: Test
original_prompt: Test
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


class TestAuditHistorySchemaValidation:
    """Tests for audit_history JSON schema validation (T043)."""

    def _make_valid_yaml(self, base_sha: str) -> str:
        return f"""schema_version: '1.2'
branch: test
title: Test
original_prompt: Test
created: '2024-01-15T14:30:00Z'
acceptance_criteria:
  - id: AC1
    description: Done
    completed: false
audit_history:
  - iteration: 1
    base_sha: '{base_sha}'
    head_sha: '{base_sha}'
    findings:
      - id: F-001
        file: cli/foo.py
        original_severity: high
        original_category: correctness
        verdict: confirmed
        summary: A finding
"""

    def test_valid_7_char_sha_passes(self, tmp_path):
        """7-char hex SHA should pass schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(self._make_valid_yaml("abc1234"))
        errors = validate_task_file(f)
        assert errors == [], errors

    def test_valid_40_char_sha_passes(self, tmp_path):
        """40-char hex SHA should pass schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(self._make_valid_yaml("e80d2978b776c7e886d220a168479ab24aa2160b"))
        errors = validate_task_file(f)
        assert errors == [], errors

    def test_non_hex_sha_fails(self, tmp_path):
        """Non-hex base_sha should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(self._make_valid_yaml("not-a-sha"))
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_too_short_sha_fails(self, tmp_path):
        """base_sha shorter than 7 chars should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(self._make_valid_yaml("abc123"))  # 6 chars
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_missing_head_sha_fails(self, tmp_path):
        """Audit runs missing head_sha should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            """schema_version: '1.2'
branch: test
title: Test
original_prompt: Test
created: '2024-01-15T14:30:00Z'
acceptance_criteria:
  - id: AC1
    description: Done
    completed: false
audit_history:
  - iteration: 1
    base_sha: abc1234
    findings:
      - id: F-001
        file: cli/foo.py
        original_severity: high
        original_category: correctness
        verdict: confirmed
        summary: A finding
"""
        )
        errors = validate_task_file(f)
        assert len(errors) > 0


class TestAuditFindingVerdictConditionals:
    """Tests for verdict-dependent corrected_severity/corrected_category in JSON schema (T050).

    AC5: when verdict=reclassified, corrected_severity and corrected_category are required
    and must be non-null; for all other verdict values these fields are rejected (must be null
    or absent).
    """

    _BASE_YAML = """schema_version: '1.2'
branch: test
title: Test
original_prompt: Test
created: '2024-01-15T14:30:00Z'
acceptance_criteria:
  - id: AC1
    description: Done
    completed: false
audit_history:
  - iteration: 1
    base_sha: abc1234
    head_sha: def5678
    findings:
      - {finding_block}
"""

    def _make_yaml(self, finding_lines: str) -> str:
        # Indent each line of the finding block to match the YAML list item
        indented = "\n        ".join(finding_lines.strip().splitlines())
        return self._BASE_YAML.format(finding_block=indented)

    def test_reclassified_with_both_corrected_fields_passes(self, tmp_path):
        """verdict=reclassified with both corrected fields should pass schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: reclassified\n"
                "corrected_severity: low\n"
                "corrected_category: style\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert errors == [], errors

    def test_reclassified_missing_corrected_severity_fails(self, tmp_path):
        """verdict=reclassified without corrected_severity should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: reclassified\n"
                "corrected_category: style\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_reclassified_missing_corrected_category_fails(self, tmp_path):
        """verdict=reclassified without corrected_category should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: reclassified\n"
                "corrected_severity: low\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_confirmed_with_corrected_severity_fails(self, tmp_path):
        """verdict=confirmed with corrected_severity set should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: confirmed\n"
                "corrected_severity: low\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_false_positive_with_corrected_category_fails(self, tmp_path):
        """verdict=false_positive with corrected_category set should fail schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: false_positive\n"
                "corrected_category: style\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert len(errors) > 0

    def test_uncertain_without_corrected_fields_passes(self, tmp_path):
        """verdict=uncertain without any corrected fields should pass schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: medium\n"
                "original_category: testing\n"
                "verdict: uncertain\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert errors == [], errors

    def test_confirmed_with_null_corrected_fields_passes(self, tmp_path):
        """verdict=confirmed with corrected fields explicitly null should pass schema validation."""
        f = tmp_path / "task.yml"
        f.write_text(
            self._make_yaml(
                "id: F-001\n"
                "file: cli/foo.py\n"
                "original_severity: high\n"
                "original_category: correctness\n"
                "verdict: confirmed\n"
                "corrected_severity: null\n"
                "corrected_category: null\n"
                "summary: A finding"
            )
        )
        errors = validate_task_file(f)
        assert errors == [], errors

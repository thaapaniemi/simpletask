"""Unit tests for MCP tools with target='defaults' parameter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from simpletask.mcp.server import constraint, context, design, quality

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def defaults_project(tmp_path: Path) -> tuple[Path, MagicMock]:
    """Create a temp .tasks/ dir and a mock Project pointing at it.

    Returns:
        Tuple of (tasks_dir, mock_project)
    """
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()

    mock_project = MagicMock()
    mock_project.tasks_dir = tasks_dir
    mock_project.ensure_tasks_dir.return_value = tasks_dir

    return tasks_dir, mock_project


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _patch_ensure_project(mock_project: MagicMock):
    """Return a context manager that patches ensure_project in server.py."""
    return patch("simpletask.mcp.server.ensure_project", return_value=mock_project)


# ---------------------------------------------------------------------------
# design() — target='defaults'
# ---------------------------------------------------------------------------


class TestDesignDefaultsTarget:
    """Tests for design() MCP tool with target='defaults'."""

    def test_get_returns_empty_when_no_defaults_file(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(action="get", target="defaults")

        assert response.action == "design_get"
        assert response.design is None
        assert "defaults" in response.file_path

    def test_set_pattern_creates_defaults_file(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(action="set", field="pattern", value="repository", target="defaults")

        assert response.success is True
        assert response.action == "design_set"
        defaults_file = tasks_dir / "defaults.yml"
        assert defaults_file.exists()

    def test_set_pattern_roundtrips_via_get(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            design(action="set", field="pattern", value="repository", target="defaults")
            response = design(action="get", target="defaults")

        assert response.design is not None
        assert response.design.patterns is not None
        assert any(p.value == "repository" for p in response.design.patterns)

    def test_set_constraint_writes_to_defaults(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(
                action="set",
                field="constraint",
                value="Use Pydantic models with extra='forbid'",
                target="defaults",
            )

        assert response.success is True
        defaults_file = tasks_dir / "defaults.yml"
        content = defaults_file.read_text()
        assert "Pydantic" in content

    def test_set_reference_requires_reason(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="reason"):
                design(
                    action="set",
                    field="reference",
                    value="cli/simpletask/mcp/server.py",
                    target="defaults",
                )

    def test_set_reference_with_reason(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(
                action="set",
                field="reference",
                value="cli/simpletask/mcp/server.py",
                reason="MCP tool pattern to follow",
                target="defaults",
            )

        assert response.success is True
        content = (tasks_dir / "defaults.yml").read_text()
        assert "server.py" in content

    def test_set_security_requires_category(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="category"):
                design(
                    action="set",
                    field="security",
                    value="Validate all inputs",
                    target="defaults",
                )

    def test_set_security_with_category(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(
                action="set",
                field="security",
                value="Validate all inputs",
                category="input_validation",
                target="defaults",
            )

        assert response.success is True
        content = (tasks_dir / "defaults.yml").read_text()
        assert "input_validation" in content

    def test_set_error_handling(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(
                action="set",
                field="error-handling",
                value="exceptions",
                target="defaults",
            )

        assert response.success is True
        content = (tasks_dir / "defaults.yml").read_text()
        assert "exceptions" in content

    def test_remove_pattern_by_index(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            design(action="set", field="pattern", value="repository", target="defaults")
            response = design(action="remove", field="pattern", index=0, target="defaults")

        assert response.success is True

    def test_remove_all_patterns(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            design(action="set", field="pattern", value="repository", target="defaults")
            response = design(action="remove", field="pattern", all=True, target="defaults")
            get_response = design(action="get", target="defaults")

        assert response.success is True
        assert get_response.design is None or get_response.design.patterns is None

    def test_summary_shows_defaults_branch(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = design(action="get", target="defaults")

        assert response.summary.branch == "defaults"
        assert response.summary.title == "Project Defaults"

    def test_set_invalid_field_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="field"):
                design(action="set", field="nonexistent", value="x", target="defaults")

    def test_set_invalid_pattern_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="pattern"):
                design(
                    action="set",
                    field="pattern",
                    value="nonexistent_pattern",
                    target="defaults",
                )


# ---------------------------------------------------------------------------
# quality() — target='defaults'
# ---------------------------------------------------------------------------


class TestQualityDefaultsTarget:
    """Tests for quality() MCP tool with target='defaults'."""

    def test_get_returns_none_when_no_defaults_file(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = quality(action="get", target="defaults")

        assert response.action == "quality_get"
        assert response.quality_requirements is None

    def test_set_linting_creates_defaults_file(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = quality(
                action="set",
                config_type="linting",
                tool="ruff",
                args="check,.",
                target="defaults",
            )

        assert response.success is True
        assert (tasks_dir / "defaults.yml").exists()

    def test_set_linting_roundtrips_via_get(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            quality(
                action="set",
                config_type="linting",
                tool="ruff",
                args="check,.",
                target="defaults",
            )
            response = quality(action="get", target="defaults")

        assert response.quality_requirements is not None
        assert response.quality_requirements.linting is not None
        assert response.quality_requirements.linting.execution is not None
        assert response.quality_requirements.linting.execution.tool.value == "ruff"

    def test_check_action_raises_for_defaults_target(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="branch task files"):
                quality(action="check", target="defaults")

    def test_preset_applies_to_defaults(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = quality(action="preset", preset_name="python", target="defaults")

        assert response.success is True
        assert (tasks_dir / "defaults.yml").exists()
        content = (tasks_dir / "defaults.yml").read_text()
        assert "ruff" in content

    def test_preset_fills_gaps_only(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            # Pre-set linting with a different tool
            quality(
                action="set",
                config_type="linting",
                tool="pylint",
                args=".",
                target="defaults",
            )
            # Apply preset — should not overwrite existing linting config
            quality(action="preset", preset_name="python", target="defaults")
            response = quality(action="get", target="defaults")

        assert response.quality_requirements is not None
        assert response.quality_requirements.linting is not None
        # Existing linting config (pylint) should be preserved
        assert response.quality_requirements.linting.execution is not None
        assert response.quality_requirements.linting.execution.tool.value == "pylint"

    def test_summary_shows_defaults_branch(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = quality(action="get", target="defaults")

        assert response.summary.branch == "defaults"

    def test_invalid_config_type_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="config_type"):
                quality(action="set", config_type="invalid", tool="ruff", target="defaults")

    def test_missing_preset_name_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="preset_name"):
                quality(action="preset", target="defaults")

    def test_set_type_checking_from_none_raises(self, defaults_project):
        """Setting type-checking on empty defaults raises ValueError to avoid phantom entries."""
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="preset"):
                quality(
                    action="set",
                    config_type="type-checking",
                    tool="mypy",
                    target="defaults",
                )

    def test_set_security_from_none_raises(self, defaults_project):
        """Setting security on empty defaults raises ValueError to avoid phantom entries."""
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="preset"):
                quality(
                    action="set",
                    config_type="security",
                    tool="bandit",
                    target="defaults",
                )

    def test_set_type_checking_after_preset_works(self, defaults_project):
        """After applying a preset, type-checking can be configured without phantom entries."""
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            quality(action="preset", preset_name="python", target="defaults")
            response = quality(
                action="set",
                config_type="type-checking",
                tool="mypy",
                args=".,--strict",
                target="defaults",
            )

        assert response.success is True
        # Verify linting was NOT silently added as a phantom — it came from the preset
        get_response = None
        with _patch_ensure_project(mock_project):
            get_response = quality(action="get", target="defaults")
        assert get_response is not None
        assert get_response.quality_requirements is not None
        assert get_response.quality_requirements.type_checking is not None
        assert get_response.quality_requirements.type_checking.execution is not None
        assert get_response.quality_requirements.type_checking.execution.tool.value == "mypy"


# ---------------------------------------------------------------------------
# constraint() — target='defaults'
# ---------------------------------------------------------------------------


class TestConstraintDefaultsTarget:
    """Tests for constraint() MCP tool with target='defaults'."""

    def test_list_returns_none_when_no_file(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = constraint(action="list", target="defaults")

        assert response.action == "constraint_list"
        assert response.constraints is None

    def test_add_creates_defaults_file(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = constraint(
                action="add",
                value="Use Pydantic models with extra='forbid'",
                target="defaults",
            )

        assert response.success is True
        assert (tasks_dir / "defaults.yml").exists()

    def test_add_then_list_roundtrips(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            constraint(action="add", value="Constraint A", target="defaults")
            constraint(action="add", value="Constraint B", target="defaults")
            response = constraint(action="list", target="defaults")

        assert response.constraints is not None
        assert "Constraint A" in response.constraints
        assert "Constraint B" in response.constraints

    def test_remove_by_index(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            constraint(action="add", value="Keep this", target="defaults")
            constraint(action="add", value="Remove this", target="defaults")
            response = constraint(action="remove", index=1, target="defaults")
            list_response = constraint(action="list", target="defaults")

        assert response.success is True
        assert list_response.constraints is not None
        assert "Remove this" not in list_response.constraints
        assert "Keep this" in list_response.constraints

    def test_remove_all(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            constraint(action="add", value="Some constraint", target="defaults")
            response = constraint(action="remove", all=True, target="defaults")
            list_response = constraint(action="list", target="defaults")

        assert response.success is True
        assert list_response.constraints is None

    def test_add_missing_value_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="value"):
                constraint(action="add", target="defaults")

    def test_remove_without_index_or_all_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            constraint(action="add", value="Something", target="defaults")
            with pytest.raises(ValueError):
                constraint(action="remove", target="defaults")

    def test_remove_invalid_index_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            constraint(action="add", value="Only one", target="defaults")
            with pytest.raises(ValueError):
                constraint(action="remove", index=99, target="defaults")

    def test_summary_shows_defaults_branch(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = constraint(action="list", target="defaults")

        assert response.summary.branch == "defaults"


# ---------------------------------------------------------------------------
# context() — target='defaults'
# ---------------------------------------------------------------------------


class TestContextDefaultsTarget:
    """Tests for context() MCP tool with target='defaults'."""

    def test_show_returns_none_when_no_file(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = context(action="show", target="defaults")

        assert response.action == "context_show"
        assert response.context is None

    def test_set_creates_defaults_file(self, defaults_project):
        tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = context(action="set", key="api_version", value="v2", target="defaults")

        assert response.success is True
        assert (tasks_dir / "defaults.yml").exists()

    def test_set_then_show_roundtrips(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            context(action="set", key="api_version", value="v2", target="defaults")
            context(action="set", key="db", value="postgres", target="defaults")
            response = context(action="show", target="defaults")

        assert response.context is not None
        assert response.context["api_version"] == "v2"
        assert response.context["db"] == "postgres"

    def test_remove_by_key(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            context(action="set", key="keep", value="yes", target="defaults")
            context(action="set", key="remove_me", value="no", target="defaults")
            response = context(action="remove", key="remove_me", target="defaults")
            show_response = context(action="show", target="defaults")

        assert response.success is True
        assert show_response.context is not None
        assert "remove_me" not in show_response.context
        assert show_response.context["keep"] == "yes"

    def test_remove_all(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            context(action="set", key="key1", value="val1", target="defaults")
            response = context(action="remove", all=True, target="defaults")
            show_response = context(action="show", target="defaults")

        assert response.success is True
        assert show_response.context is None

    def test_remove_nonexistent_key_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="not found"):
                context(action="remove", key="nonexistent", target="defaults")

    def test_set_missing_key_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="key"):
                context(action="set", value="v2", target="defaults")

    def test_set_missing_value_raises(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            with pytest.raises(ValueError, match="value"):
                context(action="set", key="k", target="defaults")

    def test_summary_shows_defaults_branch(self, defaults_project):
        _tasks_dir, mock_project = defaults_project

        with _patch_ensure_project(mock_project):
            response = context(action="show", target="defaults")

        assert response.summary.branch == "defaults"


# ---------------------------------------------------------------------------
# Verify target='branch' still works (no regression)
# ---------------------------------------------------------------------------


class TestBranchTargetNoRegression:
    """Verify that target='branch' (default) still works as before."""

    def test_design_get_branch_target(self, tmp_project_with_task):
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = design(action="get", target="branch")

        assert response.action == "design_get"
        # summary should NOT be the fake defaults summary
        assert response.summary.branch != "defaults"

    def test_constraint_list_branch_target(self, tmp_project_with_task):
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = constraint(action="list", target="branch")

        assert response.action == "constraint_list"
        assert response.summary.branch != "defaults"

    def test_context_show_branch_target(self, tmp_project_with_task):
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = context(action="show", target="branch")

        assert response.action == "context_show"
        assert response.summary.branch != "defaults"

    def test_quality_get_branch_target(self, tmp_project_with_task):
        _project_root, task_file = tmp_project_with_task

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = quality(action="get", target="branch")

        assert response.action == "quality_get"
        assert response.summary.branch != "defaults"

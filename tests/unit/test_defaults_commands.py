"""Unit tests for defaults CLI commands.

Tests cover:
- defaults show command: no file, with file, all sections
- defaults clear command: full file, specific field
- defaults design set command: all field types
- defaults quality set and preset commands
- defaults constraint add command
- defaults context set command
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import typer
import yaml
from simpletask.commands.defaults.commands import (
    clear_command,
    constraint_add_command,
    context_set_command,
    design_set_command,
    quality_preset_command,
    quality_set_command,
    show_command,
)
from simpletask.core.defaults import load_defaults
from simpletask.core.models import (
    ArchitecturalPattern,
    Design,
    ErrorHandlingStrategy,
    LintingConfig,
    ProjectDefaults,
    QualityRequirements,
    SecurityCategory,
    TestingConfig,
    ToolName,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_project(tmp_path: Path) -> MagicMock:
    """Return a mock Project whose tasks_dir points to a real temp directory."""
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    mock_project = MagicMock()
    mock_project.tasks_dir = tasks_dir
    mock_project.ensure_tasks_dir.return_value = tasks_dir
    return mock_project


def _write_defaults(tasks_dir: Path, defaults: ProjectDefaults) -> Path:
    """Serialise and write a ProjectDefaults to the tasks directory."""
    data: dict[str, Any] = defaults.model_dump(mode="json", exclude_none=True)
    path = tasks_dir / "defaults.yml"
    path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# TestShowCommand
# ---------------------------------------------------------------------------


class TestShowCommand:
    """Tests for 'simpletask defaults show'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_show_no_defaults_file(self, mock_ensure, tmp_path, capsys):
        """Show prints a 'no defaults' message when defaults.yml is absent."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        show_command()

        captured = capsys.readouterr()
        assert "No project defaults configured" in captured.out

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_show_with_all_sections(self, mock_ensure, tmp_path, capsys):
        """Show renders design, constraints, and context from a real file."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        defaults = ProjectDefaults(
            design=Design(
                patterns=[ArchitecturalPattern.REPOSITORY],
                architectural_constraints=["Use Pydantic"],
            ),
            constraints=["No shell=True", "Use pathlib"],
            context={"framework": "django", "db": "postgres"},
        )
        _write_defaults(tmp_path / ".tasks", defaults)

        show_command()

        captured = capsys.readouterr()
        assert "repository" in captured.out
        assert "Use Pydantic" in captured.out
        assert "No shell=True" in captured.out
        assert "Use pathlib" in captured.out
        assert "framework" in captured.out
        assert "django" in captured.out

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_show_empty_defaults_file(self, mock_ensure, tmp_path, capsys):
        """Show displays an 'empty' message when the file exists but has no sections."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        _write_defaults(tmp_path / ".tasks", ProjectDefaults())

        show_command()

        captured = capsys.readouterr()
        assert "empty" in captured.out


# ---------------------------------------------------------------------------
# TestClearCommand
# ---------------------------------------------------------------------------


class TestClearCommand:
    """Tests for 'simpletask defaults clear'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_all_removes_file(self, mock_ensure, tmp_path):
        """Clear without --field deletes the entire defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        # Create the file
        defaults_path = tmp_path / ".tasks" / "defaults.yml"
        defaults_path.write_text("constraints:\n- test\n", encoding="utf-8")

        clear_command(field=None)

        assert not defaults_path.exists()

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_all_no_file(self, mock_ensure, tmp_path, capsys):
        """Clear without --field prints 'nothing to remove' when file is absent."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        clear_command(field=None)

        captured = capsys.readouterr()
        assert "No defaults file" in captured.out

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_design_field(self, mock_ensure, tmp_path):
        """Clear --field design removes only the design section."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        defaults = ProjectDefaults(
            design=Design(patterns=[ArchitecturalPattern.REPOSITORY]),
            constraints=["Keep this"],
        )
        _write_defaults(tmp_path / ".tasks", defaults)

        clear_command(field="design")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is None
        assert result.constraints == ["Keep this"]

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_quality_field(self, mock_ensure, tmp_path):
        """Clear --field quality removes only the quality section."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        defaults = ProjectDefaults(
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                testing=TestingConfig(enabled=False, tool=ToolName.PYTEST, args=[]),
            ),
            constraints=["Keep this"],
        )
        _write_defaults(tmp_path / ".tasks", defaults)

        clear_command(field="quality")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.quality_requirements is None
        assert result.constraints == ["Keep this"]

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_constraints_field(self, mock_ensure, tmp_path):
        """Clear --field constraints removes only the constraints section."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        defaults = ProjectDefaults(
            constraints=["c1", "c2"],
            context={"k": "v"},
        )
        _write_defaults(tmp_path / ".tasks", defaults)

        clear_command(field="constraints")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.constraints is None
        assert result.context == {"k": "v"}

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_context_field(self, mock_ensure, tmp_path):
        """Clear --field context removes only the context section."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        defaults = ProjectDefaults(
            constraints=["keep"],
            context={"k": "v"},
        )
        _write_defaults(tmp_path / ".tasks", defaults)

        clear_command(field="context")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.context is None
        assert result.constraints == ["keep"]

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_clear_invalid_field(self, mock_ensure, tmp_path):
        """Clear with an invalid --field name raises typer.Exit."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        with pytest.raises(typer.Exit):
            clear_command(field="nonexistent")


# ---------------------------------------------------------------------------
# TestDesignSetCommand
# ---------------------------------------------------------------------------


class TestDesignSetCommand:
    """Tests for 'simpletask defaults design set'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_pattern(self, mock_ensure, tmp_path):
        """design set pattern writes pattern to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(field="pattern", value="repository")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        assert ArchitecturalPattern.REPOSITORY in result.design.patterns  # type: ignore[operator]

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_constraint(self, mock_ensure, tmp_path):
        """design set constraint writes constraint to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(field="constraint", value="Use Pydantic with extra='forbid'")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        assert "Use Pydantic with extra='forbid'" in result.design.architectural_constraints  # type: ignore[operator]

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_reference(self, mock_ensure, tmp_path):
        """design set reference writes reference to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(
            field="reference",
            value="cli/simpletask/mcp/server.py",
            reference_reason="MCP tool pattern",
        )

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        assert result.design.reference_implementations is not None
        ref = result.design.reference_implementations[0]
        assert ref.path == "cli/simpletask/mcp/server.py"
        assert ref.reason == "MCP tool pattern"

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_reference_missing_reason(self, mock_ensure, tmp_path):
        """design set reference without --reason raises typer.Exit."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        with pytest.raises(typer.Exit):
            design_set_command(field="reference", value="src/module.py", reference_reason=None)

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_security(self, mock_ensure, tmp_path):
        """design set security writes security requirement to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(
            field="security",
            value="Validate all inputs",
            security_category="input_validation",
        )

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        assert result.design.security is not None
        req = result.design.security[0]
        assert req.category == SecurityCategory.INPUT_VALIDATION
        assert req.description == "Validate all inputs"

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_error_handling(self, mock_ensure, tmp_path):
        """design set error-handling writes strategy to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(field="error-handling", value="exceptions")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        assert result.design.error_handling == ErrorHandlingStrategy.EXCEPTIONS

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_invalid_field(self, mock_ensure, tmp_path):
        """design set with unknown field raises typer.Exit."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        with pytest.raises(typer.Exit):
            design_set_command(field="nonexistent", value="anything")

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_invalid_pattern(self, mock_ensure, tmp_path):
        """design set pattern with invalid value raises typer.Exit."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        with pytest.raises(typer.Exit):
            design_set_command(field="pattern", value="not_a_valid_pattern")

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_appends_to_existing(self, mock_ensure, tmp_path):
        """design set appends to existing defaults instead of overwriting."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        design_set_command(field="pattern", value="repository")
        design_set_command(field="pattern", value="factory")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.design is not None
        patterns = result.design.patterns or []
        assert ArchitecturalPattern.REPOSITORY in patterns
        assert ArchitecturalPattern.FACTORY in patterns


# ---------------------------------------------------------------------------
# TestQualitySetCommand
# ---------------------------------------------------------------------------


class TestQualitySetCommand:
    """Tests for 'simpletask defaults quality set'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_linting(self, mock_ensure, tmp_path):
        """quality set linting writes linting config to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        quality_set_command(
            config_type="linting",  # type: ignore[arg-type]
            tool=ToolName.RUFF,
            args="check,.",
            enable=True,
            disable=False,
            min_coverage=None,
            timeout=None,
        )

        result = load_defaults(mock_project)
        assert result is not None
        assert result.quality_requirements is not None
        assert result.quality_requirements.linting is not None
        linting = result.quality_requirements.linting
        assert linting.enabled is True
        assert linting.execution is not None
        assert linting.execution.tool == ToolName.RUFF

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_testing_with_coverage(self, mock_ensure, tmp_path):
        """quality set testing with min-coverage writes correct config."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        quality_set_command(
            config_type="testing",  # type: ignore[arg-type]
            tool=ToolName.PYTEST,
            args=None,
            enable=True,
            disable=False,
            min_coverage=80,
            timeout=600,
        )

        result = load_defaults(mock_project)
        assert result is not None
        assert result.quality_requirements is not None
        assert result.quality_requirements.testing is not None
        testing = result.quality_requirements.testing
        assert testing.min_coverage == 80
        assert testing.timeout == 600
        assert testing.execution is not None
        assert testing.execution.tool == ToolName.PYTEST


# ---------------------------------------------------------------------------
# TestQualityPresetCommand
# ---------------------------------------------------------------------------


class TestQualityPresetCommand:
    """Tests for 'simpletask defaults quality preset'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_preset_python_applies(self, mock_ensure, tmp_path):
        """quality preset python populates defaults.yml quality section."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        quality_preset_command(preset_name="python", list_flag=False)

        result = load_defaults(mock_project)
        assert result is not None
        assert result.quality_requirements is not None
        # python preset should set linting (ruff) and type checking (mypy) at minimum
        assert result.quality_requirements.linting is not None

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_preset_missing_name_exits(self, mock_ensure, tmp_path):
        """quality preset without name raises typer.Exit."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        with pytest.raises(typer.Exit):
            quality_preset_command(preset_name=None, list_flag=False)

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_preset_list_flag(self, mock_ensure, tmp_path, capsys):
        """quality preset --list prints available presets and exits cleanly."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        quality_preset_command(preset_name=None, list_flag=True)

        captured = capsys.readouterr()
        assert "python" in captured.out

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_preset_fills_gaps_only(self, mock_ensure, tmp_path):
        """quality preset does not overwrite existing configuration."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        # Pre-populate linting config
        existing = ProjectDefaults(
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=False, tool=ToolName.RUFF, args=["check", "src/"]),
                testing=TestingConfig(enabled=False, tool=ToolName.PYTEST, args=[]),
            )
        )
        _write_defaults(tmp_path / ".tasks", existing)

        quality_preset_command(preset_name="python", list_flag=False)

        result = load_defaults(mock_project)
        assert result is not None
        assert result.quality_requirements is not None
        # Existing linting should be kept (args preserved in execution spec)
        linting = result.quality_requirements.linting
        assert linting is not None
        assert linting.execution is not None
        assert linting.execution.args == ["check", "src/"]


# ---------------------------------------------------------------------------
# TestConstraintAddCommand
# ---------------------------------------------------------------------------


class TestConstraintAddCommand:
    """Tests for 'simpletask defaults constraint add'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_add_constraint(self, mock_ensure, tmp_path):
        """constraint add writes constraint to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        constraint_add_command(value="Use Pydantic with extra='forbid'")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.constraints is not None
        assert "Use Pydantic with extra='forbid'" in result.constraints

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_add_multiple_constraints(self, mock_ensure, tmp_path):
        """constraint add accumulates multiple constraints."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        constraint_add_command(value="constraint one")
        constraint_add_command(value="constraint two")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.constraints is not None
        assert len(result.constraints) == 2


# ---------------------------------------------------------------------------
# TestContextSetCommand
# ---------------------------------------------------------------------------


class TestContextSetCommand:
    """Tests for 'simpletask defaults context set'."""

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_context(self, mock_ensure, tmp_path):
        """context set writes key-value to defaults.yml."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        context_set_command(key="framework", value="django")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.context is not None
        assert result.context["framework"] == "django"

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_set_multiple_context_keys(self, mock_ensure, tmp_path):
        """context set accumulates multiple keys."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        context_set_command(key="framework", value="django")
        context_set_command(key="database", value="postgres")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.context is not None
        assert result.context["framework"] == "django"
        assert result.context["database"] == "postgres"

    @patch("simpletask.commands.defaults.commands.ensure_project")
    def test_overwrite_existing_key(self, mock_ensure, tmp_path):
        """context set overwrites an existing key with new value."""
        mock_project = _make_project(tmp_path)
        mock_ensure.return_value = mock_project

        context_set_command(key="framework", value="flask")
        context_set_command(key="framework", value="django")

        result = load_defaults(mock_project)
        assert result is not None
        assert result.context is not None
        assert result.context["framework"] == "django"

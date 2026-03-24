"""Unit tests for ProjectDefaults model and defaults.py module.

Tests cover:
- ProjectDefaults model validation
- load_defaults() — file missing, valid, malformed, extra fields
- save_defaults() — round-trip, creates dir if needed
- merge_defaults_into_spec() — fill-gaps-only strategy, edge cases
- list_tasks / list_tasks_by_mtime exclusion of defaults.yml
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from simpletask.core.defaults import (
    get_defaults_path,
    load_defaults,
    merge_defaults_into_spec,
    save_defaults,
)
from simpletask.core.models import (
    AcceptanceCriterion,
    ArchitecturalPattern,
    Design,
    LintingConfig,
    ProjectDefaults,
    QualityRequirements,
    SimpleTaskSpec,
    TestingConfig,
    ToolName,
)
from simpletask.core.project import Project
from simpletask.core.yaml_parser import InvalidTaskFileError, write_task_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(root: Path) -> Project:
    return Project(root=root)


def _make_minimal_spec(branch: str = "test-branch") -> SimpleTaskSpec:
    return SimpleTaskSpec(
        schema_version="1.0",
        branch=branch,
        title="Test",
        original_prompt="Test",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Done", completed=False),
        ],
        constraints=None,
        context=None,
        tasks=None,
    )


def _make_design() -> Design:
    return Design(
        patterns=[ArchitecturalPattern.REPOSITORY],
        reference_implementations=None,
        architectural_constraints=["Use Pydantic"],
        security=None,
        error_handling=None,
    )


def _make_quality() -> QualityRequirements:
    return QualityRequirements(
        linting=LintingConfig(
            enabled=True,
            tool=ToolName.RUFF,
            args=["check", "."],
            timeout=300,
        ),
        type_checking=None,
        testing=TestingConfig(
            enabled=True,
            tool=ToolName.PYTEST,
            args=["--cov=cli/simpletask"],
            timeout=600,
        ),
        security_check=None,
    )


# ---------------------------------------------------------------------------
# ProjectDefaults model
# ---------------------------------------------------------------------------


class TestProjectDefaultsModel:
    """Tests for the ProjectDefaults Pydantic model."""

    def test_all_fields_set(self):
        """ProjectDefaults with all fields populated."""
        defaults = ProjectDefaults(
            design=_make_design(),
            quality_requirements=_make_quality(),
            constraints=["Be strict"],
            context={"env": "test"},
        )
        assert defaults.design is not None
        assert defaults.quality_requirements is not None
        assert defaults.constraints == ["Be strict"]
        assert defaults.context == {"env": "test"}

    def test_extra_fields_rejected(self):
        """extra='forbid' means unknown fields raise ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectDefaults.model_validate({"unknown_field": "value"})


# ---------------------------------------------------------------------------
# load_defaults
# ---------------------------------------------------------------------------


class TestLoadDefaults:
    """Tests for load_defaults()."""

    def test_returns_none_when_file_missing(self, tmp_project):
        """Returns None when .tasks/defaults.yml does not exist."""
        project = _make_project(tmp_project)
        result = load_defaults(project)
        assert result is None

    def test_returns_project_defaults_when_valid(self, tmp_project):
        """Returns ProjectDefaults when file is valid YAML."""
        project = _make_project(tmp_project)
        defaults = ProjectDefaults(constraints=["No magic numbers"])
        save_defaults(project, defaults)

        loaded = load_defaults(project)
        assert loaded is not None
        assert loaded.constraints == ["No magic numbers"]

    def test_returns_empty_defaults_for_empty_file(self, tmp_project):
        """Empty YAML file produces empty ProjectDefaults (not None)."""
        project = _make_project(tmp_project)
        project.ensure_tasks_dir()
        get_defaults_path(project).write_text("", encoding="utf-8")

        result = load_defaults(project)
        assert result is not None
        assert result.design is None
        assert result.constraints is None

    def test_raises_on_malformed_yaml(self, tmp_project):
        """InvalidTaskFileError raised on bad YAML syntax."""
        project = _make_project(tmp_project)
        project.ensure_tasks_dir()
        get_defaults_path(project).write_text("key: [unclosed", encoding="utf-8")

        with pytest.raises(InvalidTaskFileError, match="Invalid YAML syntax"):
            load_defaults(project)

    def test_raises_on_extra_fields(self, tmp_project):
        """InvalidTaskFileError raised when YAML has unknown fields."""
        project = _make_project(tmp_project)
        project.ensure_tasks_dir()
        content = yaml.dump({"constraints": ["ok"], "bogus_field": "oops"})
        get_defaults_path(project).write_text(content, encoding="utf-8")

        with pytest.raises(InvalidTaskFileError):
            load_defaults(project)

    def test_raises_when_root_is_not_dict(self, tmp_project):
        """InvalidTaskFileError raised when YAML root is not a dict."""
        project = _make_project(tmp_project)
        project.ensure_tasks_dir()
        get_defaults_path(project).write_text("- item1\n- item2\n", encoding="utf-8")

        with pytest.raises(InvalidTaskFileError, match="expected a dictionary"):
            load_defaults(project)

    def test_full_round_trip(self, tmp_project):
        """Defaults with all fields save and load correctly."""
        project = _make_project(tmp_project)
        original = ProjectDefaults(
            design=_make_design(),
            quality_requirements=_make_quality(),
            constraints=["Constraint A", "Constraint B"],
            context={"version": "1.0"},
        )
        save_defaults(project, original)
        loaded = load_defaults(project)

        assert loaded is not None
        assert loaded.constraints == ["Constraint A", "Constraint B"]
        assert loaded.context == {"version": "1.0"}
        assert loaded.design is not None
        assert ArchitecturalPattern.REPOSITORY in (loaded.design.patterns or [])


# ---------------------------------------------------------------------------
# save_defaults
# ---------------------------------------------------------------------------


class TestSaveDefaults:
    """Tests for save_defaults()."""

    def test_creates_tasks_dir_if_missing(self, tmp_path):
        """save_defaults creates the .tasks/ directory when it doesn't exist."""
        import git

        root = tmp_path / "new-project"
        root.mkdir()
        git.Repo.init(root)
        project = _make_project(root)

        # .tasks/ should not exist yet
        assert not project.tasks_dir.exists()

        defaults = ProjectDefaults(constraints=["Use Pydantic"])
        save_defaults(project, defaults)

        assert get_defaults_path(project).exists()

    def test_writes_valid_yaml(self, tmp_project):
        """Written file is valid YAML that can be parsed."""
        project = _make_project(tmp_project)
        defaults = ProjectDefaults(context={"key": "value"})
        path = save_defaults(project, defaults)

        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        assert isinstance(data, dict)
        assert data.get("context") == {"key": "value"}

    def test_overwrites_existing_file(self, tmp_project):
        """save_defaults overwrites an existing defaults.yml."""
        project = _make_project(tmp_project)
        save_defaults(project, ProjectDefaults(constraints=["Old constraint"]))
        save_defaults(project, ProjectDefaults(constraints=["New constraint"]))

        loaded = load_defaults(project)
        assert loaded is not None
        assert loaded.constraints == ["New constraint"]

    def test_exclude_none_fields_in_output(self, tmp_project):
        """Fields that are None are not written to the YAML file."""
        project = _make_project(tmp_project)
        defaults = ProjectDefaults(constraints=["A"])
        path = save_defaults(project, defaults)

        content = path.read_text(encoding="utf-8")
        assert "design" not in content
        assert "quality_requirements" not in content
        assert "context" not in content


# ---------------------------------------------------------------------------
# merge_defaults_into_spec
# ---------------------------------------------------------------------------


class TestMergeDefaultsIntoSpec:
    """Tests for merge_defaults_into_spec() — fill-gaps-only strategy."""

    def test_fills_none_constraints_from_defaults(self):
        """spec.constraints=None is populated from defaults."""
        spec = _make_minimal_spec()
        defaults = ProjectDefaults(constraints=["No shell=True"])
        result = merge_defaults_into_spec(spec, defaults)
        assert result.constraints == ["No shell=True"]

    def test_fills_none_context_from_defaults(self):
        """spec.context=None is populated from defaults."""
        spec = _make_minimal_spec()
        defaults = ProjectDefaults(context={"env": "ci"})
        result = merge_defaults_into_spec(spec, defaults)
        assert result.context == {"env": "ci"}

    def test_fills_none_design_from_defaults(self):
        """spec.design=None is populated from defaults."""
        spec = _make_minimal_spec()
        design = _make_design()
        defaults = ProjectDefaults(design=design)
        result = merge_defaults_into_spec(spec, defaults)
        assert result.design is not None
        assert ArchitecturalPattern.REPOSITORY in (result.design.patterns or [])

    def test_fills_none_quality_from_defaults(self):
        """spec.quality_requirements=None is populated from defaults."""
        spec = _make_minimal_spec()
        q = _make_quality()
        defaults = ProjectDefaults(quality_requirements=q)
        result = merge_defaults_into_spec(spec, defaults)
        assert result.quality_requirements is not None
        assert result.quality_requirements.linting is not None

    def test_does_not_overwrite_existing_constraints(self):
        """Existing spec.constraints is NOT replaced by defaults."""
        spec = _make_minimal_spec()
        spec.constraints = ["Existing constraint"]
        defaults = ProjectDefaults(constraints=["Default constraint"])
        result = merge_defaults_into_spec(spec, defaults)
        assert result.constraints == ["Existing constraint"]

    def test_does_not_overwrite_existing_context(self):
        """Existing spec.context is NOT replaced by defaults."""
        spec = _make_minimal_spec()
        spec.context = {"my_key": "my_value"}
        defaults = ProjectDefaults(context={"default_key": "default_value"})
        result = merge_defaults_into_spec(spec, defaults)
        assert result.context == {"my_key": "my_value"}

    def test_does_not_overwrite_existing_design(self):
        """Existing spec.design is NOT replaced by defaults."""
        spec = _make_minimal_spec()
        existing_design = Design(
            patterns=[ArchitecturalPattern.SERVICE_LAYER],
            reference_implementations=None,
            architectural_constraints=None,
            security=None,
            error_handling=None,
        )
        spec.design = existing_design
        defaults_design = _make_design()  # has REPOSITORY pattern
        defaults = ProjectDefaults(design=defaults_design)
        result = merge_defaults_into_spec(spec, defaults)
        assert result.design is existing_design
        assert ArchitecturalPattern.SERVICE_LAYER in (result.design.patterns or [])
        assert ArchitecturalPattern.REPOSITORY not in (result.design.patterns or [])

    def test_empty_defaults_is_noop(self):
        """All-None defaults produce no changes to the spec."""
        spec = _make_minimal_spec()
        spec.context = {"keep": "this"}
        defaults = ProjectDefaults()
        result = merge_defaults_into_spec(spec, defaults)
        assert result.constraints is None
        assert result.context == {"keep": "this"}
        assert result.design is None
        assert result.quality_requirements is None

    def test_partial_defaults_fills_only_missing(self):
        """Only unset spec fields are populated; present ones are untouched."""
        spec = _make_minimal_spec()
        spec.constraints = ["Keep me"]
        defaults = ProjectDefaults(
            constraints=["Should be ignored"],
            context={"fill": "this"},
        )
        result = merge_defaults_into_spec(spec, defaults)
        assert result.constraints == ["Keep me"]
        assert result.context == {"fill": "this"}


# ---------------------------------------------------------------------------
# Integration: create_task_file merges defaults
# ---------------------------------------------------------------------------


class TestCreateTaskFileWithDefaults:
    """Integration tests verifying create_task_file uses project defaults."""

    def test_new_task_gets_defaults_merged(self, tmp_project):
        """create_task_file merges defaults.yml into the new task file."""
        import git

        project = _make_project(tmp_project)
        # Set up a branch so task creation can proceed
        repo = git.Repo(tmp_project)
        branch = repo.create_head("feature/with-defaults")
        branch.checkout()

        # Write defaults
        defaults = ProjectDefaults(
            constraints=["Use Pydantic"],
            context={"team": "backend"},
        )
        save_defaults(project, defaults)

        # Create a task file
        from simpletask.core.task_file_ops import create_task_file

        spec = create_task_file(project, "feature/with-defaults", "Test Title", "Test prompt")
        assert spec.constraints == ["Use Pydantic"]
        assert spec.context == {"team": "backend"}

    def test_new_task_no_defaults_is_unchanged(self, tmp_project):
        """When no defaults.yml exists, task creation is unchanged."""
        import git

        project = _make_project(tmp_project)
        repo = git.Repo(tmp_project)
        branch = repo.create_head("feature/no-defaults")
        branch.checkout()

        # No defaults.yml exists
        from simpletask.core.task_file_ops import create_task_file

        spec = create_task_file(project, "feature/no-defaults", "T", "P")
        assert spec.constraints is None
        assert spec.context is None
        assert spec.design is None


# ---------------------------------------------------------------------------
# list_tasks exclusion of defaults.yml
# ---------------------------------------------------------------------------


class TestListTasksDefaultsExclusion:
    """Tests ensuring defaults.yml is excluded from task listings."""

    def _write_defaults(self, project: Project) -> None:
        defaults = ProjectDefaults(constraints=["Test"])
        save_defaults(project, defaults)

    def _write_task_file(self, project: Project, branch: str) -> None:
        spec = _make_minimal_spec(branch=branch)
        task_file = project.get_task_file(branch)
        write_task_file(task_file, spec)

    def test_list_tasks_excludes_defaults_yml(self, tmp_project):
        """list_tasks() does not include defaults.yml in results."""
        project = _make_project(tmp_project)
        self._write_defaults(project)
        self._write_task_file(project, "feature/my-task")

        tasks = project.list_tasks()
        assert "feature/my-task" in tasks
        # defaults.yml has no 'branch' field so it won't be parsed as a task anyway,
        # but our explicit check ensures it's skipped by filename before any parsing
        assert len(tasks) == 1

    def test_list_tasks_only_defaults_returns_empty(self, tmp_project):
        """When only defaults.yml exists, list_tasks() returns empty list."""
        project = _make_project(tmp_project)
        self._write_defaults(project)

        tasks = project.list_tasks()
        assert tasks == []

    def test_list_tasks_by_mtime_excludes_defaults_yml(self, tmp_project):
        """list_tasks_by_mtime() does not include defaults.yml in results."""
        project = _make_project(tmp_project)
        self._write_defaults(project)
        self._write_task_file(project, "feature/my-task")

        tasks = project.list_tasks_by_mtime()
        branches = [t[0] for t in tasks]
        assert "feature/my-task" in branches
        assert len(tasks) == 1

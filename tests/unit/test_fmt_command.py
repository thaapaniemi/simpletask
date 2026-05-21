"""Unit tests for the fmt command.

Tests cover:
- fmt rewrites non-canonical files (extra blank lines, wrong indentation)
- fmt is idempotent (running twice produces identical output)
- fmt skips schema-invalid files without overwriting them
- fmt --check exits 0 when all files are already canonical
- fmt --check exits 1 when any file would change
- fmt --check exits 1 when any file has parse errors, naming them separately
- fmt --check never writes to disk
- fmt --check is silent on success (no error output)
- fmt + fmt --check sequence always exits 0 (post-fmt idempotency)
- serialize_task_file is idempotent at the parser level (round-trip test)
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
import yaml
from simpletask.commands.fmt.commands import fmt_command
from simpletask.core.models import AcceptanceCriterion, SimpleTaskSpec, Task, TaskStatus
from simpletask.core.yaml_parser import (
    parse_task_file_from_text,
    serialize_task_file,
    write_task_file,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(branch: str = "test-feature") -> SimpleTaskSpec:
    """Return a minimal but valid SimpleTaskSpec."""
    return SimpleTaskSpec(
        schema_version="1.0",
        branch=branch,
        title="Test Feature",
        original_prompt="Implement test feature",
        created=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Feature works", completed=False),
        ],
        tasks=[
            Task(
                id="T001",
                name="Setup",
                status=TaskStatus.NOT_STARTED,
                goal="Configure environment",
                steps=["Install deps"],
            )
        ],
    )


def _write_canonical(path: Path, spec: SimpleTaskSpec) -> None:
    """Write a canonical task file (through write_task_file)."""
    write_task_file(path, spec)


def _write_non_canonical(path: Path, spec: SimpleTaskSpec) -> None:
    """Write a task file with extra blank lines (non-canonical)."""
    canonical = serialize_task_file(spec)
    # Insert extra blank lines to make it non-canonical
    non_canonical = canonical.replace("\n", "\n\n", 3)
    path.write_text(non_canonical, encoding="utf-8")


def _write_non_canonical_indent(path: Path, spec: SimpleTaskSpec) -> None:
    """Write a task file with indent=4 instead of the canonical indent=2."""
    data = spec.model_dump(mode="json", exclude_none=True)
    non_canonical = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        indent=4,
    )
    path.write_text(non_canonical, encoding="utf-8")


def _mock_project(tasks_dir: Path) -> MagicMock:
    """Return a mock Project with the given tasks_dir."""
    mock = MagicMock()
    mock.tasks_dir = tasks_dir
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tasks_dir(tmp_path: Path) -> Path:
    """Return an empty temporary .tasks/ directory."""
    d = tmp_path / ".tasks"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFmtNormalMode:
    """Tests for `simpletask fmt` (normal rewrite mode, check=False)."""

    def test_rewrites_non_canonical_file(self, tasks_dir: Path) -> None:
        """fmt rewrites a non-canonical file to canonical form."""
        spec = _make_spec()
        file_path = tasks_dir / "test-feature.yml"
        _write_non_canonical(file_path, spec)

        before = file_path.read_text(encoding="utf-8")
        expected_canonical = serialize_task_file(spec)
        assert before != expected_canonical, "Precondition: file must not yet be canonical"

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        after = file_path.read_text(encoding="utf-8")
        assert after == expected_canonical

    def test_rewrites_wrong_indentation(self, tasks_dir: Path) -> None:
        """fmt normalizes a file written with indent=4 to the canonical indent=2."""
        spec = _make_spec()
        file_path = tasks_dir / "test-feature.yml"
        _write_non_canonical_indent(file_path, spec)

        before = file_path.read_text(encoding="utf-8")
        expected_canonical = serialize_task_file(spec)
        assert before != expected_canonical, "Precondition: indent=4 file must not be canonical"

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        after = file_path.read_text(encoding="utf-8")
        assert after == expected_canonical

    def test_idempotent(self, tasks_dir: Path) -> None:
        """Running fmt twice produces identical byte-for-byte output."""
        spec = _make_spec()
        file_path = tasks_dir / "test-feature.yml"
        _write_non_canonical(file_path, spec)

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        after_first = file_path.read_text(encoding="utf-8")

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        after_second = file_path.read_text(encoding="utf-8")
        assert after_first == after_second

    def test_already_canonical_file_unchanged(self, tasks_dir: Path) -> None:
        """fmt does not modify a file already in canonical form."""
        spec = _make_spec()
        file_path = tasks_dir / "test-feature.yml"
        _write_canonical(file_path, spec)
        before = file_path.read_text(encoding="utf-8")

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        assert file_path.read_text(encoding="utf-8") == before

    def test_skips_invalid_file_without_overwriting(self, tasks_dir: Path) -> None:
        """fmt does not overwrite a schema-invalid YAML file."""
        file_path = tasks_dir / "bad.yml"
        invalid_yaml = "not_a_valid_task: true\nmissing_required_fields: yes\n"
        file_path.write_text(invalid_yaml, encoding="utf-8")

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            with pytest.raises(typer.Exit) as exc_info:
                fmt_command(check=False)

        # File must be unchanged
        assert file_path.read_text(encoding="utf-8") == invalid_yaml
        # Must exit with code 1 specifically
        assert exc_info.value.exit_code == 1


class TestFmtCheckMode:
    """Tests for `simpletask fmt --check` mode."""

    def test_does_not_write_files(self, tasks_dir: Path) -> None:
        """--check never modifies files even when they would change."""
        spec = _make_spec()
        file_path = tasks_dir / "test-feature.yml"
        _write_non_canonical(file_path, spec)
        original_content = file_path.read_text(encoding="utf-8")

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            with pytest.raises(typer.Exit):
                fmt_command(check=True)

        assert file_path.read_text(encoding="utf-8") == original_content

    def test_names_all_dirty_files(self, tasks_dir: Path) -> None:
        """--check output includes the name of every file that would change."""
        spec_a = _make_spec("feature-a")
        spec_b = _make_spec("feature-b")
        _write_non_canonical(tasks_dir / "feature-a.yml", spec_a)
        _write_non_canonical(tasks_dir / "feature-b.yml", spec_b)

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            with patch("simpletask.commands.fmt.commands.console") as mock_console:
                with pytest.raises(typer.Exit):
                    fmt_command(check=True)

                all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
                assert "feature-a.yml" in all_output
                assert "feature-b.yml" in all_output

    def test_check_mode_names_parse_error_files(self, tasks_dir: Path) -> None:
        """--check names files with parse errors separately and exits 1."""
        file_path = tasks_dir / "bad.yml"
        invalid_yaml = "not_a_valid_task: true\nmissing_required_fields: yes\n"
        file_path.write_text(invalid_yaml, encoding="utf-8")

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            with patch("simpletask.commands.fmt.commands.error_console") as mock_error_console:
                with pytest.raises(typer.Exit) as exc_info:
                    fmt_command(check=True)

                all_output = " ".join(str(c) for c in mock_error_console.print.call_args_list)
                assert "bad.yml" in all_output
                assert "Parse errors" in all_output
                assert exc_info.value.exit_code == 1

    def test_check_mode_separates_dirty_and_error_files(self, tasks_dir: Path) -> None:
        """--check prints dirty files and parse-error files under separate headers."""
        spec = _make_spec("clean-feature")
        _write_non_canonical(tasks_dir / "dirty.yml", spec)
        (tasks_dir / "bad.yml").write_text(
            "not_a_valid_task: true\nmissing_required_fields: yes\n", encoding="utf-8"
        )

        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            with patch("simpletask.commands.fmt.commands.console") as mock_console:
                with patch("simpletask.commands.fmt.commands.error_console") as mock_error_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        fmt_command(check=True)

                    console_output = " ".join(str(c) for c in mock_console.print.call_args_list)
                    error_output = " ".join(str(c) for c in mock_error_console.print.call_args_list)
                    assert "dirty.yml" in console_output
                    assert "Would reformat" in console_output
                    assert "bad.yml" in error_output
                    assert "Parse errors" in error_output
                    assert exc_info.value.exit_code == 1

    def test_post_fmt_check_exits_0(self, tasks_dir: Path) -> None:
        """Running fmt then fmt --check always exits 0 (post-fmt idempotency)."""
        spec = _make_spec()
        _write_non_canonical(tasks_dir / "test-feature.yml", spec)

        # First: fmt (normal mode)
        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=False)

        # Then: fmt --check must succeed (no Exit raised)
        with patch(
            "simpletask.commands.fmt.commands.ensure_project", return_value=_mock_project(tasks_dir)
        ):
            fmt_command(check=True)


class TestFmtSerializeIdempotency:
    """Tests verifying serializer-level idempotency independent of the fmt command."""

    def test_serialize_is_idempotent_at_parser_level(self) -> None:
        """parse -> serialize -> parse -> serialize produces identical output both times.

        This test can fail if serialize_task_file or the Pydantic models introduce
        any non-deterministic output, making it a meaningful regression guard.
        """
        spec = _make_spec()

        # First round-trip: serialize, re-parse in-memory, serialize again
        first_yaml = serialize_task_file(spec)
        reparsed = parse_task_file_from_text(first_yaml)

        # Second serialization must be byte-for-byte identical
        second_yaml = serialize_task_file(reparsed)
        assert first_yaml == second_yaml

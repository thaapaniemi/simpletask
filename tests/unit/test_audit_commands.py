"""Tests for audit CLI commands."""

from pathlib import Path

from simpletask.commands.audit import app
from simpletask.core.yaml_parser import write_task_file
from typer.testing import CliRunner

runner = CliRunner()


class TestAddRunCommand:
    """Tests for the audit add-run command."""

    def test_missing_findings_file_exits_one(self, monkeypatch, sample_spec, tmp_path: Path):
        """Report a missing findings file as a command failure, not a usage error."""
        task_file = tmp_path / "task.yml"
        write_task_file(task_file, sample_spec)
        monkeypatch.setattr(
            "simpletask.commands.audit.add_run.get_task_file_path", lambda _: task_file
        )

        result = runner.invoke(
            app,
            [
                "add-run",
                "--iteration",
                "1",
                "--base-sha",
                "abc1234",
                "--head-sha",
                "def5678",
                "--findings",
                str(tmp_path / "missing.json"),
            ],
        )

        assert result.exit_code == 1
        assert "No such file or directory" in result.output

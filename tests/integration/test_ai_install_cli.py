"""Integration tests for AI install CLI command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from simpletask import app

runner = CliRunner()


class TestAiInstallCLI:
    """Integration tests for 'simpletask ai install' command."""

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_default_installs_both_editors(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should install both OpenCode and Qwen templates by default."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout

        # Verify files were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (opencode_dir / "simpletask.implement.md").exists()
        assert (opencode_dir / "simpletask.review.md").exists()
        assert (qwen_dir / "simpletask.plan.toml").exists()
        assert (qwen_dir / "simpletask.implement.toml").exists()
        assert (qwen_dir / "simpletask.review.toml").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_opencode_flag_only(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should install only OpenCode templates with --opencode flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install", "--opencode"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" not in result.stdout

        # Verify only OpenCode files were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert not qwen_dir.exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_qwen_flag_only(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should install only Qwen templates with --qwen flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install", "--qwen"])

        assert result.exit_code == 0
        assert "Installing Qwen commands" in result.stdout
        assert "Installing OpenCode commands" not in result.stdout

        # Verify only Qwen files were created
        assert (qwen_dir / "simpletask.plan.toml").exists()
        assert not opencode_dir.exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_both_flags_explicit(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should install both when both flags are specified."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install", "--opencode", "--qwen"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout

        # Verify both were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.toml").exists()

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_qwen_commands_dir")
    def test_local_flag_with_both(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should install both to local directories with --local flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install", "--local"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout

        # Verify files were created in local directories
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.toml").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_no_overwrite_flag(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should respect --no-overwrite flag for both editors."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        opencode_dir.mkdir(parents=True)
        qwen_dir.mkdir(parents=True)

        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        # Create existing files
        (opencode_dir / "simpletask.plan.md").write_text("old opencode content")
        (qwen_dir / "simpletask.plan.toml").write_text("old qwen content")

        result = runner.invoke(app, ["ai", "install", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask.plan.md" in result.stdout
        assert "Skipped (already exists): simpletask.plan.toml" in result.stdout

        # Verify existing files were not overwritten
        assert (opencode_dir / "simpletask.plan.md").read_text() == "old opencode content"
        assert (qwen_dir / "simpletask.plan.toml").read_text() == "old qwen content"

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_qwen_commands_dir")
    def test_combined_flags(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should handle combination of --opencode, --qwen, and --local."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install", "--opencode", "--qwen", "--local"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout

        # Verify both were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.toml").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    def test_shows_summary(self, mock_qwen_dir, mock_opencode_dir, tmp_path: Path):
        """Should show summary information after installation."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        # Should show summary for each editor
        assert "Summary:" in result.stdout
        # Should show installed files
        assert "Installed: simpletask.plan.md" in result.stdout
        assert "Installed: simpletask.implement.md" in result.stdout
        assert "Installed: simpletask.review.md" in result.stdout
        assert "Installed: simpletask.plan.toml" in result.stdout
        assert "Installed: simpletask.implement.toml" in result.stdout
        assert "Installed: simpletask.review.toml" in result.stdout

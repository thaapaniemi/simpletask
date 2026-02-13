"""Integration tests for AI install CLI command."""

from pathlib import Path
from unittest.mock import patch

from simpletask import app
from typer.testing import CliRunner

runner = CliRunner()


class TestAiInstallCLI:
    """Integration tests for 'simpletask ai install' command."""

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_default_installs_all_three_editors(
        self, mock_agents_dir, mock_gemini_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should install all three editors (OpenCode, Qwen, Gemini) by default."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout
        assert "Installing Gemini CLI commands" in result.stdout

        # Verify all three sets of files were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (opencode_dir / "simpletask.implement.md").exists()
        assert (opencode_dir / "simpletask.review.md").exists()
        assert (qwen_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.implement.md").exists()
        assert (qwen_dir / "simpletask.review.md").exists()
        assert (gemini_dir / "simpletask.plan.toml").exists()
        assert (gemini_dir / "simpletask.implement.toml").exists()
        assert (gemini_dir / "simpletask.review.toml").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_opencode_flag_only(
        self, mock_agents_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should install only OpenCode templates with --opencode flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_agents_dir.return_value = agents_dir

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
        assert (qwen_dir / "simpletask.plan.md").exists()
        assert not opencode_dir.exists()

    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    def test_tip_shown_when_qwen_skips(self, mock_gemini_dir, mock_qwen_dir, tmp_path: Path):
        """Should show no-overwrite tip when Qwen files are skipped."""
        qwen_dir = tmp_path / "qwen"
        qwen_dir.mkdir(parents=True)
        gemini_dir = tmp_path / "gemini"
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir

        # Create existing file to force a skip
        (qwen_dir / "simpletask.plan.md").write_text("old content")

        result = runner.invoke(app, ["ai", "install", "--qwen", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask.plan.md" in result.stdout
        assert "Tip: Use --no-overwrite to preserve existing files" in result.stdout

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    def test_gemini_flag_only(
        self, mock_gemini_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should install only Gemini CLI templates with --gemini flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir

        result = runner.invoke(app, ["ai", "install", "--gemini"])

        assert result.exit_code == 0
        assert "Installing Gemini CLI commands" in result.stdout
        assert "Installing OpenCode commands" not in result.stdout
        assert "Installing Qwen commands" not in result.stdout

        # Verify only Gemini files were created
        assert (gemini_dir / "simpletask.plan.toml").exists()
        assert (gemini_dir / "simpletask.implement.toml").exists()
        assert (gemini_dir / "simpletask.review.toml").exists()
        assert not opencode_dir.exists()
        assert not qwen_dir.exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_all_three_flags_explicit(
        self, mock_agents_dir, mock_gemini_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should install all three editors when all flags are specified."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install", "--opencode", "--qwen", "--gemini"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout
        assert "Installing Gemini CLI commands" in result.stdout

        # Verify all three were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.md").exists()
        assert (gemini_dir / "simpletask.plan.toml").exists()

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_agents_dir")
    def test_local_flag_with_all_three(
        self, mock_agents_dir, mock_gemini_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should install all three editors to local directories with --local flag."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install", "--local"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout
        assert "Installing Gemini CLI commands" in result.stdout

        # Verify files were created in local directories
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.md").exists()
        assert (gemini_dir / "simpletask.plan.toml").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_no_overwrite_flag(
        self, mock_agents_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should respect --no-overwrite flag for both editors."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        agents_dir = tmp_path / "agents"
        opencode_dir.mkdir(parents=True)
        qwen_dir.mkdir(parents=True)

        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_agents_dir.return_value = agents_dir

        # Create existing files
        (opencode_dir / "simpletask.plan.md").write_text("old opencode content")
        (qwen_dir / "simpletask.plan.md").write_text("old qwen content")

        result = runner.invoke(app, ["ai", "install", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask.plan.md" in result.stdout

        # Verify existing files were not overwritten
        assert (opencode_dir / "simpletask.plan.md").read_text() == "old opencode content"
        assert (qwen_dir / "simpletask.plan.md").read_text() == "old qwen content"

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_agents_dir")
    def test_combined_flags(
        self, mock_agents_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should handle combination of --opencode, --qwen, and --local."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install", "--opencode", "--qwen", "--local"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout

        # Verify both were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.plan.md").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_shows_summary(
        self, mock_agents_dir, mock_gemini_dir, mock_qwen_dir, mock_opencode_dir, tmp_path: Path
    ):
        """Should show summary information after installation for all three editors."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        # Should show summary for each editor
        assert "Summary:" in result.stdout
        # Should show installed files for OpenCode
        assert "Installed: simpletask.plan.md" in result.stdout
        assert "Installed: simpletask.implement.md" in result.stdout
        assert "Installed: simpletask.review.md" in result.stdout
        # Should show installed files for Qwen (now using .md format)
        # Note: Multiple "Installed: simpletask.plan.md" from both OpenCode and Qwen
        assert "simpletask.plan.md" in result.stdout
        assert "simpletask.implement.md" in result.stdout
        assert "simpletask.review.md" in result.stdout


class TestAiInstallAgentsCLI:
    """Integration tests for agent installation via 'simpletask ai install' command."""

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_opencode_flag_installs_agents(
        self, mock_agents_dir, mock_commands_dir, tmp_path: Path
    ):
        """Should install OpenCode agents when --opencode flag is used."""
        commands_dir = tmp_path / "commands"
        agents_dir = tmp_path / "agents"
        mock_commands_dir.return_value = commands_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install", "--opencode"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing OpenCode agents" in result.stdout

        # Verify both commands and agents were installed
        assert (commands_dir / "simpletask.plan.md").exists()
        assert (agents_dir / "simpletask-plan.md").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_default_install_includes_agents(
        self, mock_agents_dir, mock_commands_dir, tmp_path: Path
    ):
        """Should install OpenCode agents by default when no flags specified."""
        commands_dir = tmp_path / "commands"
        agents_dir = tmp_path / "agents"
        mock_commands_dir.return_value = commands_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing OpenCode agents" in result.stdout

        # Verify agents were installed alongside commands
        assert (agents_dir / "simpletask-plan.md").exists()

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_agents_dir")
    def test_local_flag_installs_agents_locally(
        self, mock_local_agents_dir, mock_local_commands_dir, tmp_path: Path
    ):
        """Should install OpenCode agents to local directory with --local flag."""
        local_commands_dir = tmp_path / "local_commands"
        local_agents_dir = tmp_path / "local_agents"
        mock_local_commands_dir.return_value = local_commands_dir
        mock_local_agents_dir.return_value = local_agents_dir

        result = runner.invoke(app, ["ai", "install", "--local", "--opencode"])

        assert result.exit_code == 0
        assert "Installing OpenCode agents" in result.stdout
        assert str(local_agents_dir) in result.stdout

        # Verify agents were installed in local directory
        assert (local_agents_dir / "simpletask-plan.md").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_agent_no_overwrite_flag(self, mock_agents_dir, mock_commands_dir, tmp_path: Path):
        """Should respect --no-overwrite flag for agents."""
        commands_dir = tmp_path / "commands"
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        mock_commands_dir.return_value = commands_dir
        mock_agents_dir.return_value = agents_dir

        # Create existing agent file
        existing_agent = agents_dir / "simpletask-plan.md"
        existing_agent.write_text("old agent content")

        result = runner.invoke(app, ["ai", "install", "--opencode", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask-plan.md" in result.stdout

        # Verify existing agent was not overwritten
        assert existing_agent.read_text() == "old agent content"

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_agent_overwrite_default(self, mock_agents_dir, mock_commands_dir, tmp_path: Path):
        """Should overwrite existing agents by default."""
        commands_dir = tmp_path / "commands"
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        mock_commands_dir.return_value = commands_dir
        mock_agents_dir.return_value = agents_dir

        # Create existing agent file
        existing_agent = agents_dir / "simpletask-plan.md"
        old_content = "old agent content"
        existing_agent.write_text(old_content)

        result = runner.invoke(app, ["ai", "install", "--opencode"])

        assert result.exit_code == 0
        assert "Overwriting: simpletask-plan.md" in result.stdout

        # Verify existing agent was overwritten
        assert existing_agent.read_text() != old_content
        assert len(existing_agent.read_text()) > 0

"""Integration tests for AI install CLI command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from simpletask import app
from typer.testing import CliRunner

runner = CliRunner()


class TestAiInstallCLI:
    """Integration tests for 'simpletask ai install' command."""

    @pytest.fixture(autouse=True)
    def mock_editor_installed(self):
        """Assume all editors are installed for these behavioural tests."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=True):
            yield

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_default_installs_all_five_editors(
        self,
        mock_agents_dir,
        mock_vibe_dir,
        mock_pi_dir,
        mock_gemini_dir,
        mock_qwen_dir,
        mock_opencode_dir,
        tmp_path: Path,
    ):
        """Should install all five editors (OpenCode, Qwen, Gemini, Pi, Vibe) by default."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        pi_dir = tmp_path / "pi"
        vibe_dir = tmp_path / "vibe"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_pi_dir.return_value = pi_dir
        mock_vibe_dir.return_value = vibe_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout
        assert "Installing Gemini CLI commands" in result.stdout
        assert "Installing Pi prompts" in result.stdout
        assert "Installing Mistral Vibe skills" in result.stdout

        # Verify all five sets of files were created
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (opencode_dir / "simpletask.implement.md").exists()
        assert (opencode_dir / "simpletask.review.md").exists()
        assert (qwen_dir / "simpletask.plan.md").exists()
        assert (qwen_dir / "simpletask.implement.md").exists()
        assert (qwen_dir / "simpletask.review.md").exists()
        assert (gemini_dir / "simpletask.plan.toml").exists()
        assert (gemini_dir / "simpletask.implement.toml").exists()
        assert (gemini_dir / "simpletask.review.toml").exists()
        assert (pi_dir / "simpletask-implement.md").exists()
        assert (pi_dir / "simpletask-plan.md").exists()
        assert (pi_dir / "simpletask-split.md").exists()
        assert (pi_dir / "simpletask-review.md").exists()
        assert (vibe_dir / "simpletask-plan").is_dir()
        assert (vibe_dir / "simpletask-plan" / "SKILL.md").exists()

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

    @pytest.fixture(autouse=True)
    def mock_editor_installed(self):
        """Assume all editors are installed for these behavioural tests."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=True):
            yield

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
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_default_install_includes_agents(
        self, mock_agents_dir, mock_pi_dir, mock_commands_dir, tmp_path: Path
    ):
        """Should install OpenCode agents by default when no flags specified."""
        commands_dir = tmp_path / "commands"
        agents_dir = tmp_path / "agents"
        mock_commands_dir.return_value = commands_dir
        mock_pi_dir.return_value = tmp_path / "pi"
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


class TestAiInstallVibeCLI:
    """Integration tests for Vibe skill installation via 'simpletask ai install' command."""

    @pytest.fixture(autouse=True)
    def mock_editor_installed(self):
        """Assume all editors are installed for these behavioural tests."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=True):
            yield

    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    def test_vibe_flag_only(self, mock_vibe_dir, tmp_path: Path):
        """Should install only Vibe skills with --vibe flag."""
        vibe_dir = tmp_path / "vibe"
        mock_vibe_dir.return_value = vibe_dir

        result = runner.invoke(app, ["ai", "install", "--vibe"])

        assert result.exit_code == 0
        assert "Installing Mistral Vibe skills" in result.stdout
        assert "Installing OpenCode commands" not in result.stdout
        assert "Installing Qwen commands" not in result.stdout
        assert "Installing Gemini CLI commands" not in result.stdout

        # Verify skill directories were created with SKILL.md inside
        assert (vibe_dir / "simpletask-plan").is_dir()
        assert (vibe_dir / "simpletask-plan" / "SKILL.md").exists()
        assert (vibe_dir / "simpletask-split").is_dir()
        assert (vibe_dir / "simpletask-implement").is_dir()
        assert (vibe_dir / "simpletask-review").is_dir()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    def test_default_installs_all_five_editors(
        self,
        mock_agents_dir,
        mock_vibe_dir,
        mock_pi_dir,
        mock_gemini_dir,
        mock_qwen_dir,
        mock_opencode_dir,
        tmp_path: Path,
    ):
        """Should install all five editors (including Pi and Vibe) by default."""
        opencode_dir = tmp_path / "opencode"
        qwen_dir = tmp_path / "qwen"
        gemini_dir = tmp_path / "gemini"
        pi_dir = tmp_path / "pi"
        vibe_dir = tmp_path / "vibe"
        agents_dir = tmp_path / "agents"
        mock_opencode_dir.return_value = opencode_dir
        mock_qwen_dir.return_value = qwen_dir
        mock_gemini_dir.return_value = gemini_dir
        mock_pi_dir.return_value = pi_dir
        mock_vibe_dir.return_value = vibe_dir
        mock_agents_dir.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing Qwen commands" in result.stdout
        assert "Installing Gemini CLI commands" in result.stdout
        assert "Installing Pi prompts" in result.stdout
        assert "Installing Mistral Vibe skills" in result.stdout

        # Verify Pi and Vibe files were created
        assert (pi_dir / "simpletask-implement.md").exists()
        assert (pi_dir / "simpletask-plan.md").exists()
        assert (vibe_dir / "simpletask-plan").is_dir()
        assert (vibe_dir / "simpletask-plan" / "SKILL.md").exists()

    @patch("simpletask.commands.ai.install.get_local_vibe_commands_dir")
    def test_vibe_local_flag(self, mock_vibe_dir, tmp_path: Path):
        """Should install Vibe skills to local directory with --local flag."""
        vibe_dir = tmp_path / "vibe_local"
        mock_vibe_dir.return_value = vibe_dir

        result = runner.invoke(app, ["ai", "install", "--vibe", "--local"])

        assert result.exit_code == 0
        assert "Installing Mistral Vibe skills" in result.stdout
        assert str(vibe_dir) in result.stdout

        # Verify skills were installed in local directory
        assert (vibe_dir / "simpletask-plan").is_dir()
        assert (vibe_dir / "simpletask-plan" / "SKILL.md").exists()

    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    def test_vibe_no_overwrite_skips_existing(self, mock_vibe_dir, tmp_path: Path):
        """Should skip existing Vibe skill directories when --no-overwrite is used."""
        vibe_dir = tmp_path / "vibe"
        vibe_dir.mkdir(parents=True)
        mock_vibe_dir.return_value = vibe_dir

        # Create existing skill directory
        existing = vibe_dir / "simpletask-plan"
        existing.mkdir()
        (existing / "SKILL.md").write_text("old content")

        result = runner.invoke(app, ["ai", "install", "--vibe", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask-plan" in result.stdout

        # Verify existing skill was not overwritten
        assert (existing / "SKILL.md").read_text() == "old content"

    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    def test_vibe_overwrite_default(self, mock_vibe_dir, tmp_path: Path):
        """Should overwrite existing Vibe skill directories by default."""
        vibe_dir = tmp_path / "vibe"
        vibe_dir.mkdir(parents=True)
        mock_vibe_dir.return_value = vibe_dir

        # Create existing skill directory with old content
        existing = vibe_dir / "simpletask-plan"
        existing.mkdir()
        (existing / "SKILL.md").write_text("old content")

        result = runner.invoke(app, ["ai", "install", "--vibe"])

        assert result.exit_code == 0
        assert "Overwriting: simpletask-plan" in result.stdout

        # Verify existing skill was overwritten
        assert (existing / "SKILL.md").read_text() != "old content"

    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    def test_vibe_does_not_install_agents(self, mock_vibe_dir, tmp_path: Path):
        """Vibe-only install should NOT install OpenCode agents."""
        vibe_dir = tmp_path / "vibe"
        mock_vibe_dir.return_value = vibe_dir

        result = runner.invoke(app, ["ai", "install", "--vibe"])

        assert result.exit_code == 0
        assert "Installing OpenCode agents" not in result.stdout


class TestInstallEditorDetection:
    """Integration tests for editor detection behaviour in 'simpletask ai install'."""

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=False)
    def test_default_skips_missing_editors(
        self,
        mock_installed,
        mock_agents_dir,
        mock_pi_dir,
        mock_vibe_dir,
        mock_gemini_dir,
        mock_qwen_dir,
        mock_opencode_dir,
        tmp_path: Path,
    ):
        """Default install skips editors whose base directory does not exist."""
        for mock, name in [
            (mock_opencode_dir, "opencode"),
            (mock_qwen_dir, "qwen"),
            (mock_gemini_dir, "gemini"),
            (mock_vibe_dir, "vibe"),
            (mock_pi_dir, "pi"),
            (mock_agents_dir, "agents"),
        ]:
            mock.return_value = tmp_path / name

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "not detected" in result.stdout
        # No templates should be written
        assert not (tmp_path / "opencode").exists()
        assert not (tmp_path / "qwen").exists()
        assert not (tmp_path / "gemini").exists()
        assert not (tmp_path / "vibe").exists()
        assert not (tmp_path / "pi").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=False)
    def test_explicit_flag_prompts_when_editor_missing_and_user_declines(
        self,
        mock_installed,
        mock_agents_dir,
        mock_commands_dir,
        tmp_path: Path,
    ):
        """Explicit --opencode flag prompts when editor missing; no files written on decline."""
        mock_commands_dir.return_value = tmp_path / "opencode"
        mock_agents_dir.return_value = tmp_path / "agents"

        result = runner.invoke(app, ["ai", "install", "--opencode"], input="n\n")

        assert result.exit_code == 0
        assert "not found" in result.stdout
        assert not (tmp_path / "opencode").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=False)
    def test_explicit_flag_installs_when_editor_missing_and_user_confirms(
        self,
        mock_installed,
        mock_agents_dir,
        mock_commands_dir,
        tmp_path: Path,
    ):
        """Explicit --opencode flag installs when editor missing and user confirms."""
        mock_commands_dir.return_value = tmp_path / "opencode"
        mock_agents_dir.return_value = tmp_path / "agents"

        result = runner.invoke(app, ["ai", "install", "--opencode"], input="y\n")

        assert result.exit_code == 0
        assert (tmp_path / "opencode" / "simpletask.plan.md").exists()

    @patch("simpletask.commands.ai.install.get_local_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_vibe_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_local_agents_dir")
    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=False)
    def test_local_flag_bypasses_detection(
        self,
        mock_installed,
        mock_agents_dir,
        mock_pi_dir,
        mock_vibe_dir,
        mock_gemini_dir,
        mock_qwen_dir,
        mock_opencode_dir,
        tmp_path: Path,
    ):
        """--local flag bypasses editor detection; all editors install regardless."""
        for mock, name in [
            (mock_opencode_dir, "opencode"),
            (mock_qwen_dir, "qwen"),
            (mock_gemini_dir, "gemini"),
            (mock_vibe_dir, "vibe"),
            (mock_pi_dir, "pi"),
            (mock_agents_dir, "agents"),
        ]:
            mock.return_value = tmp_path / name

        result = runner.invoke(app, ["ai", "install", "--local"])

        assert result.exit_code == 0
        assert (tmp_path / "opencode" / "simpletask.plan.md").exists()
        assert (tmp_path / "qwen" / "simpletask.plan.md").exists()
        assert (tmp_path / "gemini" / "simpletask.plan.toml").exists()
        assert (tmp_path / "vibe" / "simpletask-plan").is_dir()
        assert (tmp_path / "pi" / "simpletask-plan.md").exists()

    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_qwen_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_gemini_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_vibe_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=True)
    def test_default_installs_all_detected_editors(
        self,
        mock_installed,
        mock_agents_dir,
        mock_pi_dir,
        mock_vibe_dir,
        mock_gemini_dir,
        mock_qwen_dir,
        mock_opencode_dir,
        tmp_path: Path,
    ):
        """Default install proceeds for all editors when all are detected."""
        for mock, name in [
            (mock_opencode_dir, "opencode"),
            (mock_qwen_dir, "qwen"),
            (mock_gemini_dir, "gemini"),
            (mock_vibe_dir, "vibe"),
            (mock_pi_dir, "pi"),
            (mock_agents_dir, "agents"),
        ]:
            mock.return_value = tmp_path / name

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert (tmp_path / "opencode" / "simpletask.plan.md").exists()
        assert (tmp_path / "qwen" / "simpletask.plan.md").exists()
        assert (tmp_path / "gemini" / "simpletask.plan.toml").exists()
        assert (tmp_path / "vibe" / "simpletask-plan").is_dir()
        assert (tmp_path / "pi" / "simpletask-plan.md").exists()


class TestAiInstallPiCLI:
    """Integration tests for Pi prompt installation via 'simpletask ai install'."""

    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    def test_pi_flag_only(self, mock_pi_dir, tmp_path: Path):
        """Should install only Pi prompt with --pi flag."""
        pi_dir = tmp_path / "pi"
        mock_pi_dir.return_value = pi_dir

        result = runner.invoke(app, ["ai", "install", "--pi"])

        assert result.exit_code == 0
        assert "Installing Pi prompts" in result.stdout
        assert "Installing OpenCode commands" not in result.stdout
        assert "Installing Qwen commands" not in result.stdout
        assert "Installing Gemini CLI commands" not in result.stdout
        assert "Installing Mistral Vibe skills" not in result.stdout
        assert "Installing OpenCode agents" not in result.stdout

        assert (pi_dir / "simpletask-implement.md").exists()
        assert (pi_dir / "simpletask-plan.md").exists()
        assert (pi_dir / "simpletask-split.md").exists()
        assert (pi_dir / "simpletask-review.md").exists()

    @patch("simpletask.commands.ai.install.get_local_pi_commands_dir")
    def test_pi_local_flag(self, mock_pi_dir, tmp_path: Path):
        """Should install Pi prompt to local directory with --local flag."""
        pi_dir = tmp_path / "pi_local"
        mock_pi_dir.return_value = pi_dir

        result = runner.invoke(app, ["ai", "install", "--pi", "--local"])

        assert result.exit_code == 0
        assert "Installing Pi prompts" in result.stdout
        assert str(pi_dir) in result.stdout
        assert (pi_dir / "simpletask-implement.md").exists()
        assert (pi_dir / "simpletask-plan.md").exists()
        assert (pi_dir / "simpletask-split.md").exists()
        assert (pi_dir / "simpletask-review.md").exists()

    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    def test_pi_no_overwrite_skips_existing(self, mock_pi_dir, tmp_path: Path):
        """Should skip existing Pi prompt when --no-overwrite is used."""
        pi_dir = tmp_path / "pi"
        pi_dir.mkdir(parents=True)
        mock_pi_dir.return_value = pi_dir

        existing = pi_dir / "simpletask-implement.md"
        existing.write_text("old content")

        result = runner.invoke(app, ["ai", "install", "--pi", "--no-overwrite"])

        assert result.exit_code == 0
        assert "Skipped (already exists): simpletask-implement.md" in result.stdout
        assert existing.read_text() == "old content"

    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    def test_pi_overwrite_default(self, mock_pi_dir, tmp_path: Path):
        """Should overwrite existing Pi prompt by default."""
        pi_dir = tmp_path / "pi"
        pi_dir.mkdir(parents=True)
        mock_pi_dir.return_value = pi_dir

        existing = pi_dir / "simpletask-implement.md"
        existing.write_text("old content")

        result = runner.invoke(app, ["ai", "install", "--pi"])

        assert result.exit_code == 0
        assert "Overwriting: simpletask-implement.md" in result.stdout
        assert existing.read_text() != "old content"

    @patch("simpletask.commands.ai.list.get_bundled_pi_templates")
    @patch("simpletask.commands.ai.list.get_pi_installed_status")
    @patch("simpletask.commands.ai.list.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.list.get_local_pi_commands_dir")
    def test_ai_list_shows_pi_section(
        self,
        mock_local_pi_dir,
        mock_global_pi_dir,
        mock_pi_status,
        mock_pi_templates,
        tmp_path: Path,
    ):
        """ai list should render Pi prompt status and locations."""
        pi_template = tmp_path / "simpletask-implement.md"
        pi_template.write_text("content")

        mock_pi_templates.return_value = [pi_template]
        mock_pi_status.return_value = {"simpletask-implement.md": {"global": True, "local": False}}
        mock_global_pi_dir.return_value = tmp_path / "global_pi"
        mock_local_pi_dir.return_value = tmp_path / "local_pi"

        result = runner.invoke(app, ["ai", "list"])

        assert result.exit_code == 0
        assert "Pi Prompts" in result.stdout
        assert "simpletask-implement" in result.stdout
        assert str(tmp_path / "global_pi") in result.stdout
        assert str(tmp_path / "local_pi") in result.stdout


class TestPiInstallBehavior:
    """Tests verifying Pi install behavior and path resolution."""

    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    def test_pi_flag_installs_pi_only(self, mock_pi_dir, tmp_path: Path):
        """--pi flag installs only Pi templates, not other editors."""
        pi_dir = tmp_path / "pi"
        mock_pi_dir.return_value = pi_dir

        result = runner.invoke(app, ["ai", "install", "--pi"])

        assert result.exit_code == 0
        assert "Installing Pi prompts" in result.stdout
        assert pi_dir.exists()
        assert (pi_dir / "simpletask-implement.md").exists()
        # No OpenCode/Qwen/Gemini dirs created
        assert not (tmp_path / "opencode").exists()
        assert not (tmp_path / "qwen").exists()

"""Integration tests for the supported AI install and list commands."""

from pathlib import Path
from unittest.mock import patch

import typer
from simpletask import app
from typer.testing import CliRunner

REPOSITORY_ROOT = Path(__file__).parents[2]

runner = CliRunner()


class TestAiInstallCLI:
    """Tests for ``simpletask ai install``."""

    def test_install_accepts_only_supported_editor_options(self):
        command = typer.main.get_command(app)
        install_command = command.commands["ai"].commands["install"]
        option_names = {option.name for option in install_command.params}

        assert {"opencode", "copilot", "pi"} <= option_names
        assert not {"qwen", "gemini", "vibe"} & option_names

    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=True)
    @patch("simpletask.commands.ai.install.get_global_agents_dir")
    @patch("simpletask.commands.ai.install.get_global_pi_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_copilot_commands_dir")
    @patch("simpletask.commands.ai.install.get_global_commands_dir")
    def test_default_installs_supported_editors(
        self,
        opencode_dir_mock,
        copilot_dir_mock,
        pi_dir_mock,
        agents_dir_mock,
        _installed_mock,
        tmp_path: Path,
    ):
        opencode_dir = tmp_path / "opencode"
        copilot_dir = tmp_path / "copilot"
        pi_dir = tmp_path / "pi"
        agents_dir = tmp_path / "agents"
        opencode_dir_mock.return_value = opencode_dir
        copilot_dir_mock.return_value = copilot_dir
        pi_dir_mock.return_value = pi_dir
        agents_dir_mock.return_value = agents_dir

        result = runner.invoke(app, ["ai", "install"])

        assert result.exit_code == 0
        assert "Installing OpenCode commands" in result.stdout
        assert "Installing GitHub Copilot prompts" in result.stdout
        assert "Installing Pi prompts" in result.stdout
        assert "Qwen" not in result.stdout
        assert "Gemini" not in result.stdout
        assert "Vibe" not in result.stdout
        assert (opencode_dir / "simpletask.plan.md").exists()
        assert (copilot_dir / "simpletask.plan.prompt.md").exists()
        assert (pi_dir / "simpletask-plan.md").exists()
        assert (agents_dir / "simpletask-plan.md").exists()

    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=True)
    @patch("simpletask.commands.ai.install.get_global_copilot_commands_dir")
    def test_copilot_flag_installs_only_copilot(
        self, copilot_dir_mock, _installed_mock, tmp_path: Path
    ):
        copilot_dir = tmp_path / "copilot"
        copilot_dir_mock.return_value = copilot_dir

        result = runner.invoke(app, ["ai", "install", "--copilot"])

        assert result.exit_code == 0
        assert "Installing GitHub Copilot prompts" in result.stdout
        assert "Installing OpenCode" not in result.stdout
        assert "Installing Pi" not in result.stdout
        assert (copilot_dir / "simpletask.review.prompt.md").exists()

    @patch("simpletask.commands.ai.install.is_editor_installed", return_value=False)
    @patch("simpletask.commands.ai.install.get_local_copilot_commands_dir")
    def test_local_copilot_install_bypasses_detection(
        self, copilot_dir_mock, _installed_mock, tmp_path: Path
    ):
        copilot_dir = tmp_path / "copilot"
        copilot_dir_mock.return_value = copilot_dir

        result = runner.invoke(app, ["ai", "install", "--copilot", "--local"])

        assert result.exit_code == 0
        assert (copilot_dir / "simpletask.split.prompt.md").exists()

    def test_removed_editor_flag_is_rejected(self):
        result = runner.invoke(app, ["ai", "install", "--qwen"])
        assert result.exit_code != 0

    @patch("simpletask.commands.ai.list.get_global_copilot_commands_dir")
    @patch("simpletask.commands.ai.list.get_local_copilot_commands_dir")
    def test_list_includes_copilot_paths(self, local_dir_mock, global_dir_mock, tmp_path: Path):
        global_dir_mock.return_value = tmp_path / "global"
        local_dir_mock.return_value = tmp_path / "local"

        result = runner.invoke(app, ["ai", "list"])

        assert result.exit_code == 0
        assert "GitHub Copilot Prompts" in result.stdout
        assert str(tmp_path / "global") in result.stdout
        assert str(tmp_path / "local") in result.stdout

    def test_copilot_resources_have_compatible_syntax_and_setup_docs(self):
        prompt_dir = REPOSITORY_ROOT / "cli/simpletask/templates/copilot"
        for prompt in prompt_dir.glob("*.prompt.md"):
            content = prompt.read_text()
            assert "${input:userInput}" in content
            assert "$ARGUMENTS" not in content
            assert "Task(" not in content
            assert "gilfoyle" not in content

        mcp_docs = (REPOSITORY_ROOT / "docs/MCP.md").read_text()
        assert ".vscode/mcp.json" in mcp_docs
        assert '"simpletask"' in mcp_docs
        assert '["serve"]' in mcp_docs

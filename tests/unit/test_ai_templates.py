"""Unit tests for supported AI template integrations."""

from pathlib import Path
from unittest.mock import patch

import pytest
from simpletask.commands.ai.install import _should_install
from simpletask.core.ai_templates import (
    EDITOR_CONFIGS,
    EditorType,
    get_editor_api,
    get_editor_base_dir,
    get_global_copilot_commands_dir,
    get_global_pi_commands_dir,
    get_local_copilot_commands_dir,
    get_local_pi_commands_dir,
    is_editor_installed,
)

SUPPORTED_EDITORS: list[EditorType] = ["opencode", "copilot", "pi"]


class TestEditorRegistry:
    """Tests for supported editor registration and paths."""

    def test_registry_contains_only_supported_editors(self):
        assert set(EDITOR_CONFIGS) == {"opencode", "copilot", "pi"}

    @pytest.mark.parametrize("editor", SUPPORTED_EDITORS)
    def test_base_directory_returns_path(self, editor: EditorType):
        assert isinstance(get_editor_base_dir(editor), Path)

    def test_copilot_configuration(self):
        config = EDITOR_CONFIGS["copilot"]
        assert config.file_extension == ".prompt.md"
        assert config.global_config_dir == (".github", "prompts")
        assert config.local_config_dir == (".github", "prompts")
        assert get_global_copilot_commands_dir() == Path.home() / ".github" / "prompts"
        assert get_local_copilot_commands_dir() == Path.cwd() / ".github" / "prompts"

    def test_pi_configuration(self):
        assert get_global_pi_commands_dir() == Path.home() / ".pi" / "agent" / "prompts"
        assert get_local_pi_commands_dir() == Path.cwd() / ".pi" / "prompts"

    def test_removed_editor_is_rejected(self):
        with pytest.raises((KeyError, ValueError)):
            get_editor_api("qwen")  # type: ignore[arg-type]


class TestIsEditorInstalled:
    """Tests for global editor detection."""

    @pytest.mark.parametrize("editor", SUPPORTED_EDITORS)
    def test_delegates_to_base_directory(self, editor: EditorType):
        with patch.object(Path, "exists", return_value=True) as mock_exists:
            assert is_editor_installed(editor) is True
        mock_exists.assert_called_once()


class TestShouldInstall:
    """Tests for install detection and confirmation behavior."""

    def test_local_bypasses_detection(self):
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            assert _should_install("copilot", "GitHub Copilot", False, True) is True

    def test_missing_implicit_editor_is_skipped(self):
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.info") as mock_info:
                assert _should_install("pi", "Pi", False, False) is False
        mock_info.assert_called_once()

    def test_missing_explicit_editor_can_be_confirmed(self):
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.typer.confirm", return_value=True):
                assert _should_install("opencode", "OpenCode", True, False) is True

"""Unit tests for ai_templates editor-detection helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest
from simpletask.commands.ai.install import _should_install
from simpletask.core.ai_templates import (
    EditorType,
    get_editor_base_dir,
    is_editor_installed,
)

ALL_EDITORS: list[EditorType] = ["opencode", "qwen", "gemini", "vibe"]


class TestGetEditorBaseDir:
    """Tests for get_editor_base_dir()."""

    @pytest.mark.parametrize("editor", ALL_EDITORS)
    def test_returns_path_for_all_editors(self, editor: EditorType):
        """Should return a Path for every supported editor without errors."""
        result = get_editor_base_dir(editor)
        assert isinstance(result, Path)

    def test_opencode_base_dir(self):
        """OpenCode base dir should be ~/.config/opencode."""
        result = get_editor_base_dir("opencode")
        assert result == Path.home() / ".config" / "opencode"

    def test_qwen_base_dir(self):
        """Qwen base dir should be ~/.qwen."""
        result = get_editor_base_dir("qwen")
        assert result == Path.home() / ".qwen"

    def test_gemini_base_dir(self):
        """Gemini base dir should be ~/.gemini."""
        result = get_editor_base_dir("gemini")
        assert result == Path.home() / ".gemini"

    def test_vibe_base_dir(self):
        """Vibe base dir should be ~/.vibe."""
        result = get_editor_base_dir("vibe")
        assert result == Path.home() / ".vibe"


class TestIsEditorInstalled:
    """Tests for is_editor_installed()."""

    def test_returns_true_when_base_dir_exists(self):
        """Should return True when the editor's base directory exists."""
        with patch.object(Path, "exists", return_value=True):
            assert is_editor_installed("opencode") is True

    def test_returns_false_when_base_dir_missing(self):
        """Should return False when the editor's base directory does not exist."""
        with patch.object(Path, "exists", return_value=False):
            assert is_editor_installed("opencode") is False

    @pytest.mark.parametrize("editor", ALL_EDITORS)
    def test_all_editors_delegate_to_exists(self, editor: EditorType):
        """Should call exists() on the base dir path for every editor."""
        with patch.object(Path, "exists", return_value=True) as mock_exists:
            result = is_editor_installed(editor)
            assert result is True
            mock_exists.assert_called_once()

    @pytest.mark.parametrize("editor", ALL_EDITORS)
    def test_not_affected_by_unrelated_path_exists(self, editor: EditorType, tmp_path: Path):
        """Detection is based solely on get_editor_base_dir, not on template dirs."""
        with patch(
            "simpletask.core.ai_templates.get_editor_base_dir",
            return_value=tmp_path / "nonexistent",
        ):
            assert is_editor_installed(editor) is False


class TestShouldInstall:
    """Tests for _should_install() — truth table verification."""

    def test_local_true_always_returns_true(self):
        """--local bypasses detection unconditionally."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            result = _should_install("opencode", "OpenCode", explicit=False, local=True)
        assert result is True

    def test_local_true_skips_confirm_even_when_explicit(self):
        """--local should not call typer.confirm even for explicit flags."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.typer.confirm") as mock_confirm:
                result = _should_install("opencode", "OpenCode", explicit=True, local=True)
        assert result is True
        mock_confirm.assert_not_called()

    def test_editor_detected_implicit_returns_true(self):
        """Row 1: editor detected, implicit → install without prompt."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=True):
            with patch("simpletask.commands.ai.install.typer.confirm") as mock_confirm:
                result = _should_install("opencode", "OpenCode", explicit=False, local=False)
        assert result is True
        mock_confirm.assert_not_called()

    def test_editor_detected_explicit_returns_true(self):
        """Row 3: editor detected, explicit flag → install without prompt."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=True):
            with patch("simpletask.commands.ai.install.typer.confirm") as mock_confirm:
                result = _should_install("qwen", "Qwen", explicit=True, local=False)
        assert result is True
        mock_confirm.assert_not_called()

    def test_editor_missing_implicit_returns_false_with_info(self):
        """Row 2: editor not detected, implicit → skip and print info message."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.info") as mock_info:
                result = _should_install("gemini", "Gemini CLI", explicit=False, local=False)
        assert result is False
        mock_info.assert_called_once()
        assert "Gemini CLI" in mock_info.call_args[0][0]

    def test_editor_missing_explicit_user_confirms(self):
        """Row 4: editor not detected, explicit flag, user confirms → install."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.typer.confirm", return_value=True):
                result = _should_install("vibe", "Mistral Vibe", explicit=True, local=False)
        assert result is True

    def test_editor_missing_explicit_user_declines(self):
        """Row 5: editor not detected, explicit flag, user declines → do not install."""
        with patch("simpletask.commands.ai.install.is_editor_installed", return_value=False):
            with patch("simpletask.commands.ai.install.typer.confirm", return_value=False):
                result = _should_install("vibe", "Mistral Vibe", explicit=True, local=False)
        assert result is False

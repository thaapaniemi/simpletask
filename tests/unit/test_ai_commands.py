"""Tests for AI integration commands."""

from pathlib import Path

from simpletask.core.ai_templates import (
    get_bundled_templates,
    get_global_commands_dir,
    get_installed_status,
    get_local_commands_dir,
    install_templates,
)


class TestGetBundledTemplates:
    """Tests for get_bundled_templates function."""

    def test_returns_list_of_paths(self):
        """Should return a list of Path objects."""
        templates = get_bundled_templates()
        assert isinstance(templates, list)
        for template in templates:
            assert isinstance(template, Path)

    def test_returns_only_markdown_files(self):
        """Should return only .md files."""
        templates = get_bundled_templates()
        for template in templates:
            assert template.suffix == ".md"

    def test_returns_expected_templates(self):
        """Should return the three bundled templates."""
        templates = get_bundled_templates()
        template_names = {t.name for t in templates}

        expected = {
            "simpletask.plan.md",
            "simpletask.implement.md",
            "simpletask.review.md",
        }

        assert template_names == expected


class TestGetGlobalCommandsDir:
    """Tests for get_global_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_global_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return ~/.config/opencode/commands/"""
        result = get_global_commands_dir()
        expected = Path.home() / ".config" / "opencode" / "commands"
        assert result == expected


class TestGetLocalCommandsDir:
    """Tests for get_local_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_local_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return .opencode/commands/ in current directory."""
        result = get_local_commands_dir()
        expected = Path.cwd() / ".opencode" / "commands"
        assert result == expected


class TestInstallTemplates:
    """Tests for install_templates function."""

    def test_install_to_empty_directory(self, tmp_path: Path):
        """Should successfully install all templates to empty directory."""
        target_dir = tmp_path / "commands"

        installed, skipped, overwritten = install_templates(target_dir, no_overwrite=False)

        # Should create target directory
        assert target_dir.exists()

        # Should install all three templates
        assert len(installed) == 3
        assert len(skipped) == 0
        assert len(overwritten) == 0

        # All templates should exist in target
        for name in installed:
            assert (target_dir / name).exists()

    def test_overwrite_existing_files(self, tmp_path: Path):
        """Should overwrite existing files when no_overwrite=False."""
        target_dir = tmp_path / "commands"
        target_dir.mkdir(parents=True)

        # Create existing file
        existing_file = target_dir / "simpletask.plan.md"
        existing_file.write_text("old content")

        installed, skipped, overwritten = install_templates(target_dir, no_overwrite=False)

        # Should report one overwrite
        assert "simpletask.plan.md" in overwritten
        assert len(overwritten) == 1

        # Should not report overwritten files as newly installed
        assert "simpletask.plan.md" not in installed

        # Should install the other two files
        assert len(installed) == 2

        # File should have new content (not "old content")
        assert existing_file.read_text() != "old content"
        assert len(existing_file.read_text()) > 0

    def test_no_overwrite_skips_existing(self, tmp_path: Path):
        """Should skip existing files when no_overwrite=True."""
        target_dir = tmp_path / "commands"
        target_dir.mkdir(parents=True)

        # Create existing file
        existing_file = target_dir / "simpletask.plan.md"
        old_content = "old content"
        existing_file.write_text(old_content)

        installed, skipped, overwritten = install_templates(target_dir, no_overwrite=True)

        # Should report one skip
        assert "simpletask.plan.md" in skipped
        assert len(skipped) == 1

        # Should not report as overwritten
        assert len(overwritten) == 0

        # Should install the other two
        assert len(installed) == 2

        # Original file should be unchanged
        assert existing_file.read_text() == old_content

    def test_creates_target_directory(self, tmp_path: Path):
        """Should create target directory if it doesn't exist."""
        target_dir = tmp_path / "nested" / "path" / "commands"

        assert not target_dir.exists()

        install_templates(target_dir, no_overwrite=False)

        assert target_dir.exists()
        assert target_dir.is_dir()


class TestGetInstalledStatus:
    """Tests for get_installed_status function."""

    def test_no_installations(self, tmp_path: Path, monkeypatch):
        """Should report nothing installed when directories don't exist."""
        # Mock the directory getters to use tmp_path
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"

        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_global_commands_dir", lambda: fake_global
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_local_commands_dir", lambda: fake_local
        )

        status = get_installed_status()

        # All templates should report not installed
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is False

    def test_global_only(self, tmp_path: Path, monkeypatch):
        """Should detect templates in global directory only."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"

        # Install to global
        install_templates(fake_global, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_global_commands_dir", lambda: fake_global
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_local_commands_dir", lambda: fake_local
        )

        status = get_installed_status()

        # All templates should be in global, none in local
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is False

    def test_local_only(self, tmp_path: Path, monkeypatch):
        """Should detect templates in local directory only."""
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to local
        install_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_global_commands_dir", lambda: fake_global
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_local_commands_dir", lambda: fake_local
        )

        status = get_installed_status()

        # All templates should be in local, none in global
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is True

    def test_both_locations(self, tmp_path: Path, monkeypatch):
        """Should detect templates in both directories."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to both
        install_templates(fake_global, no_overwrite=False)
        install_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_global_commands_dir", lambda: fake_global
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates.get_local_commands_dir", lambda: fake_local
        )

        status = get_installed_status()

        # All templates should be in both locations
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is True

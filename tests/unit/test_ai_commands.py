"""Tests for AI integration commands."""

from pathlib import Path

from simpletask.core.ai_templates import (
    get_bundled_gemini_templates,
    get_bundled_qwen_templates,
    get_bundled_templates,
    get_gemini_installed_status,
    get_gemini_templates_dir,
    get_global_commands_dir,
    get_global_gemini_commands_dir,
    get_global_qwen_commands_dir,
    get_installed_status,
    get_local_commands_dir,
    get_local_gemini_commands_dir,
    get_local_qwen_commands_dir,
    get_qwen_installed_status,
    install_gemini_templates,
    install_qwen_templates,
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
        """Should return the four bundled templates."""
        templates = get_bundled_templates()
        template_names = {t.name for t in templates}

        expected = {
            "simpletask.plan.md",
            "simpletask.split.md",
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

        # Should install all four templates
        assert len(installed) == 4
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

        installed, _skipped, overwritten = install_templates(target_dir, no_overwrite=False)

        # Should report one overwrite
        assert "simpletask.plan.md" in overwritten
        assert len(overwritten) == 1

        # Should not report overwritten files as newly installed
        assert "simpletask.plan.md" not in installed

        # Should install the other three files
        assert len(installed) == 3

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

        # Should install the other three
        assert len(installed) == 3

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
    """Tests for get_installed_status function.

    Note: These tests patch internal functions (_get_global_commands_dir,
    _get_local_commands_dir) rather than the public API. This is intentional
    as it provides fine-grained control over directory locations for both
    OpenCode and Qwen editors independently, which is necessary for testing
    the status checking logic. The trade-off is tighter coupling to the
    implementation, but this is acceptable for these specific tests.
    """

    def test_no_installations(self, tmp_path: Path, monkeypatch):
        """Should report nothing installed when directories don't exist."""
        # Mock the directory getters to use tmp_path
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
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
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
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
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
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
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_installed_status()

        # All templates should be in both locations
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is True


class TestGetBundledQwenTemplates:
    """Tests for get_bundled_qwen_templates function."""

    def test_returns_list_of_paths(self):
        """Should return a list of Path objects."""
        templates = get_bundled_qwen_templates()
        assert isinstance(templates, list)
        for template in templates:
            assert isinstance(template, Path)

    def test_returns_only_md_files(self):
        """Should return only .md files."""
        templates = get_bundled_qwen_templates()
        for template in templates:
            assert template.suffix == ".md"

    def test_returns_expected_templates(self):
        """Should return the four bundled Qwen templates."""
        templates = get_bundled_qwen_templates()
        template_names = {t.name for t in templates}

        expected = {
            "simpletask.plan.md",
            "simpletask.split.md",
            "simpletask.implement.md",
            "simpletask.review.md",
        }

        assert template_names == expected


class TestGetGlobalQwenCommandsDir:
    """Tests for get_global_qwen_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_global_qwen_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return ~/.qwen/commands/"""
        result = get_global_qwen_commands_dir()
        expected = Path.home() / ".qwen" / "commands"
        assert result == expected


class TestGetLocalQwenCommandsDir:
    """Tests for get_local_qwen_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_local_qwen_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return .qwen/commands/ in current directory."""
        result = get_local_qwen_commands_dir()
        expected = Path.cwd() / ".qwen" / "commands"
        assert result == expected


class TestInstallQwenTemplates:
    """Tests for install_qwen_templates function."""

    def test_install_to_empty_directory(self, tmp_path: Path):
        """Should successfully install all Qwen templates to empty directory."""
        target_dir = tmp_path / "commands"

        installed, skipped, overwritten = install_qwen_templates(target_dir, no_overwrite=False)

        # Should create target directory
        assert target_dir.exists()

        # Should install all four templates
        assert len(installed) == 4
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

        installed, _skipped, overwritten = install_qwen_templates(target_dir, no_overwrite=False)

        # Should report one overwrite
        assert "simpletask.plan.md" in overwritten
        assert len(overwritten) == 1

        # Should not report overwritten files as newly installed
        assert "simpletask.plan.md" not in installed

        # Should install the other three files
        assert len(installed) == 3

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

        installed, skipped, overwritten = install_qwen_templates(target_dir, no_overwrite=True)

        # Should report one skip
        assert "simpletask.plan.md" in skipped
        assert len(skipped) == 1

        # Should not report as overwritten
        assert len(overwritten) == 0

        # Should install the other three
        assert len(installed) == 3

        # Original file should be unchanged
        assert existing_file.read_text() == old_content

    def test_creates_target_directory(self, tmp_path: Path):
        """Should create target directory if it doesn't exist."""
        target_dir = tmp_path / "nested" / "path" / "commands"

        assert not target_dir.exists()

        install_qwen_templates(target_dir, no_overwrite=False)

        assert target_dir.exists()
        assert target_dir.is_dir()


class TestGetQwenInstalledStatus:
    """Tests for get_qwen_installed_status function."""

    def test_no_installations(self, tmp_path: Path, monkeypatch):
        """Should report nothing installed when directories don't exist."""
        # Mock the directory getters to use tmp_path
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_qwen_installed_status()

        # All templates should report not installed
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is False

    def test_global_only(self, tmp_path: Path, monkeypatch):
        """Should detect Qwen templates in global directory only."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"

        # Install to global
        install_qwen_templates(fake_global, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_qwen_installed_status()

        # All templates should be in global, none in local
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is False

    def test_local_only(self, tmp_path: Path, monkeypatch):
        """Should detect Qwen templates in local directory only."""
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to local
        install_qwen_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_qwen_installed_status()

        # All templates should be in local, none in global
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is True

    def test_both_locations(self, tmp_path: Path, monkeypatch):
        """Should detect Qwen templates in both directories."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to both
        install_qwen_templates(fake_global, no_overwrite=False)
        install_qwen_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_qwen_installed_status()

        # All templates should be in both locations
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is True


class TestGetBundledGeminiTemplates:
    """Tests for get_bundled_gemini_templates function."""

    def test_returns_list_of_paths(self):
        """Should return a list of Path objects."""
        templates = get_bundled_gemini_templates()
        assert isinstance(templates, list)
        for template in templates:
            assert isinstance(template, Path)

    def test_returns_only_toml_files(self):
        """Should return only .toml files."""
        templates = get_bundled_gemini_templates()
        for template in templates:
            assert template.suffix == ".toml"

    def test_returns_expected_templates(self):
        """Should return the four bundled Gemini templates."""
        templates = get_bundled_gemini_templates()
        template_names = {t.name for t in templates}

        expected = {
            "simpletask.plan.toml",
            "simpletask.split.toml",
            "simpletask.implement.toml",
            "simpletask.review.toml",
        }

        assert template_names == expected


class TestGetGlobalGeminiCommandsDir:
    """Tests for get_global_gemini_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_global_gemini_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return ~/.gemini/commands/"""
        result = get_global_gemini_commands_dir()
        expected = Path.home() / ".gemini" / "commands"
        assert result == expected


class TestGetLocalGeminiCommandsDir:
    """Tests for get_local_gemini_commands_dir function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_local_gemini_commands_dir()
        assert isinstance(result, Path)

    def test_returns_expected_location(self):
        """Should return .gemini/commands/ in current directory."""
        result = get_local_gemini_commands_dir()
        expected = Path.cwd() / ".gemini" / "commands"
        assert result == expected


class TestInstallGeminiTemplates:
    """Tests for install_gemini_templates function."""

    def test_install_to_empty_directory(self, tmp_path: Path):
        """Should successfully install all Gemini templates to empty directory."""
        target_dir = tmp_path / "commands"

        installed, skipped, overwritten = install_gemini_templates(target_dir, no_overwrite=False)

        # Should create target directory
        assert target_dir.exists()

        # Should install all four templates
        assert len(installed) == 4
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
        existing_file = target_dir / "simpletask.plan.toml"
        existing_file.write_text("old content")

        installed, _skipped, overwritten = install_gemini_templates(target_dir, no_overwrite=False)

        # Should report one overwrite
        assert "simpletask.plan.toml" in overwritten
        assert len(overwritten) == 1

        # Should not report overwritten files as newly installed
        assert "simpletask.plan.toml" not in installed

        # Should install the other three files
        assert len(installed) == 3

        # File should have new content (not "old content")
        assert existing_file.read_text() != "old content"
        assert len(existing_file.read_text()) > 0

    def test_no_overwrite_skips_existing(self, tmp_path: Path):
        """Should skip existing files when no_overwrite=True."""
        target_dir = tmp_path / "commands"
        target_dir.mkdir(parents=True)

        # Create existing file
        existing_file = target_dir / "simpletask.plan.toml"
        old_content = "old content"
        existing_file.write_text(old_content)

        installed, skipped, overwritten = install_gemini_templates(target_dir, no_overwrite=True)

        # Should report one skip
        assert "simpletask.plan.toml" in skipped
        assert len(skipped) == 1

        # Should not report as overwritten
        assert len(overwritten) == 0

        # Should install the other three
        assert len(installed) == 3

        # Original file should be unchanged
        assert existing_file.read_text() == old_content

    def test_creates_target_directory(self, tmp_path: Path):
        """Should create target directory if it doesn't exist."""
        target_dir = tmp_path / "nested" / "path" / "commands"

        assert not target_dir.exists()

        install_gemini_templates(target_dir, no_overwrite=False)

        assert target_dir.exists()
        assert target_dir.is_dir()


class TestGetGeminiInstalledStatus:
    """Tests for get_gemini_installed_status function."""

    def test_no_installations(self, tmp_path: Path, monkeypatch):
        """Should report nothing installed when directories don't exist."""
        # Mock the directory getters to use tmp_path
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_gemini_installed_status()

        # All templates should report not installed
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is False

    def test_global_only(self, tmp_path: Path, monkeypatch):
        """Should detect Gemini templates in global directory only."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"

        # Install to global
        install_gemini_templates(fake_global, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_gemini_installed_status()

        # All templates should be in global, none in local
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is False

    def test_local_only(self, tmp_path: Path, monkeypatch):
        """Should detect Gemini templates in local directory only."""
        fake_global = tmp_path / "global"
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to local
        install_gemini_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_gemini_installed_status()

        # All templates should be in local, none in global
        for _template_name, locations in status.items():
            assert locations["global"] is False
            assert locations["local"] is True

    def test_both_locations(self, tmp_path: Path, monkeypatch):
        """Should detect Gemini templates in both directories."""
        fake_global = tmp_path / "global"
        fake_global.mkdir(parents=True)
        fake_local = tmp_path / "local"
        fake_local.mkdir(parents=True)

        # Install to both
        install_gemini_templates(fake_global, no_overwrite=False)
        install_gemini_templates(fake_local, no_overwrite=False)

        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_global_commands_dir",
            lambda editor: fake_global,
        )
        monkeypatch.setattr(
            "simpletask.core.ai_templates._get_local_commands_dir",
            lambda editor: fake_local,
        )

        status = get_gemini_installed_status()

        # All templates should be in both locations
        for _template_name, locations in status.items():
            assert locations["global"] is True
            assert locations["local"] is True


class TestGeminiAndQwenTemplateDifferences:
    """Verify Gemini (TOML) and Qwen (Markdown) templates are no longer identical."""

    def test_gemini_and_qwen_have_same_count(self):
        """Gemini and Qwen should have the same number of templates."""
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        # Same number of templates
        assert len(qwen_templates) == len(gemini_templates)

    def test_gemini_uses_toml_qwen_uses_markdown(self):
        """Gemini should use TOML format while Qwen uses Markdown format."""
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        # Qwen uses .md extension
        for template in qwen_templates:
            assert template.suffix == ".md", f"Qwen template {template.name} should be .md"

        # Gemini uses .toml extension
        for template in gemini_templates:
            assert template.suffix == ".toml", f"Gemini template {template.name} should be .toml"

    def test_gemini_and_qwen_have_matching_base_names(self):
        """Gemini and Qwen should have the same template base names (without extensions)."""
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        # Extract base names (without extensions)
        qwen_bases = sorted([t.stem for t in qwen_templates])
        gemini_bases = sorted([t.stem for t in gemini_templates])

        assert (
            qwen_bases == gemini_bases
        ), "Qwen and Gemini should have the same template names (ignoring extensions)"


class TestSplitTemplateContent:
    """Validate split template content structure and completeness."""

    def test_opencode_split_template_has_essential_sections(self):
        """OpenCode split template should contain all essential sections."""
        templates = get_bundled_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None, "simpletask.split.md not found"

        content = split_template.read_text()

        # Essential sections that must be present
        essential_sections = [
            "## Step 1: Load Task File",
            "## Step 1.5: Codebase Analysis & Design (Conditional)",
            "## Step 2: Identify Tasks to Split",
            "## Step 3: Analyze and Generate Subtasks",
            "## Step 4: Apply Changes Atomically with Batch Operations",
            "## Step 5: Renumber Task IDs Sequentially",
            "## Step 6: Validate and Report",
            "## Edge Cases",
            "## Important Reminders",
        ]

        for section in essential_sections:
            assert section in content, f"Missing essential section: {section}"

    def test_opencode_split_template_has_splitting_criteria(self):
        """OpenCode split template should define splitting criteria."""
        templates = get_bundled_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()

        # Splitting criteria markers
        splitting_criteria = [
            ">2 steps",
            ">1 file",
            ">3 conditions",
            ">100 characters",
        ]

        for criterion in splitting_criteria:
            assert criterion in content, f"Missing splitting criterion: {criterion}"

    def test_opencode_split_template_has_mcp_instructions(self):
        """OpenCode split template should include MCP tool usage."""
        templates = get_bundled_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()

        # MCP tool references
        mcp_tools = [
            "simpletask_get",
            "simpletask_task",
        ]

        for tool in mcp_tools:
            assert tool in content, f"Missing MCP tool reference: {tool}"

    def test_opencode_split_template_has_no_cli_fallback(self):
        """OpenCode split template should not include CLI fallback commands (MCP-first approach)."""
        templates = get_bundled_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()

        # CLI fallback patterns that should NOT be present
        cli_fallback_patterns = [
            "**Fallback: Use CLI**",
            "**Preferred: Use MCP tool**",
        ]

        for pattern in cli_fallback_patterns:
            assert pattern not in content, f"Found unexpected CLI fallback pattern: {pattern}"

    def test_opencode_split_template_size_under_500_lines(self):
        """OpenCode split template should be under 500 lines for token efficiency."""
        templates = get_bundled_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()
        line_count = len(content.splitlines())

        assert (
            line_count < 500
        ), f"Split template is {line_count} lines, should be <500 for token efficiency"

    def test_qwen_split_template_has_markdown_structure(self):
        """Qwen split template should have valid Markdown with YAML frontmatter structure."""
        templates = get_bundled_qwen_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None, "simpletask.split.md not found"

        content = split_template.read_text()

        # Markdown with YAML frontmatter structure markers
        assert content.startswith("---\n"), "Missing YAML frontmatter opening"
        assert "description:" in content, "Missing YAML description field"
        assert "\n---\n" in content, "Missing YAML frontmatter closing"

    def test_qwen_split_template_has_essential_content(self):
        """Qwen split template should contain essential content."""
        templates = get_bundled_qwen_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()

        # Essential content
        essential_content = [
            "Step 1: Load Task File",
            "Step 2: Identify Tasks to Split",
            "simpletask_get",
            "simpletask_task",
        ]

        for item in essential_content:
            assert item in content, f"Missing essential content: {item}"

    def test_qwen_split_template_size_under_500_lines(self):
        """Qwen split template should be under 500 lines for token efficiency."""
        templates = get_bundled_qwen_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.md"), None)
        assert split_template is not None

        content = split_template.read_text()
        line_count = len(content.splitlines())

        assert (
            line_count < 500
        ), f"Qwen split template is {line_count} lines, should be <500 for token efficiency"

    def test_gemini_split_template_exists(self):
        """Gemini split template should exist (uses TOML format, while Qwen uses Markdown)."""
        gemini_dir = get_gemini_templates_dir()
        gemini_split = gemini_dir / "simpletask.split.toml"
        assert gemini_split.exists(), "Gemini simpletask.split.toml not found"

        # Note: Qwen now uses Markdown (.md) while Gemini uses TOML (.toml)
        # They are no longer byte-identical but serve the same purpose

    def test_gemini_split_template_has_toml_structure(self):
        """Gemini split template should have valid TOML structure."""
        templates = get_bundled_gemini_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.toml"), None)
        assert split_template is not None, "simpletask.split.toml not found"

        content = split_template.read_text()

        # TOML structure markers
        assert "description = " in content, "Missing TOML description field"
        assert 'prompt = """' in content, "Missing TOML prompt field"

    def test_gemini_split_template_has_essential_content(self):
        """Gemini split template should contain essential content."""
        templates = get_bundled_gemini_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.toml"), None)
        assert split_template is not None

        content = split_template.read_text()

        # Essential content
        essential_content = [
            "Step 1: Load Task File",
            "Step 2: Identify Tasks to Split",
            "simpletask_get",
            "simpletask_task",
        ]

        for item in essential_content:
            assert item in content, f"Missing essential content: {item}"

    def test_gemini_split_template_size_under_500_lines(self):
        """Gemini split template should be under 500 lines for token efficiency."""
        templates = get_bundled_gemini_templates()
        split_template = next((t for t in templates if t.name == "simpletask.split.toml"), None)
        assert split_template is not None

        content = split_template.read_text()
        line_count = len(content.splitlines())

        assert (
            line_count < 500
        ), f"Gemini split template is {line_count} lines, should be <500 for token efficiency"


class TestCrossEditorConsistency:
    """Verify consistency across OpenCode, Qwen, and Gemini templates."""

    def test_all_editors_have_same_template_names(self):
        """All editors should have templates with the same base names."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        # Extract base names (stems) without extensions
        opencode_bases = sorted([t.stem for t in opencode_templates])
        qwen_bases = sorted([t.stem for t in qwen_templates])
        gemini_bases = sorted([t.stem for t in gemini_templates])

        assert (
            opencode_bases == qwen_bases == gemini_bases
        ), "All editors should have the same template base names"

    def test_all_split_templates_have_splitting_criteria(self):
        """All split templates should define the same splitting criteria."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_split = next((t for t in opencode_templates if t.stem == "simpletask.split"), None)
        qwen_split = next((t for t in qwen_templates if t.stem == "simpletask.split"), None)
        gemini_split = next((t for t in gemini_templates if t.stem == "simpletask.split"), None)

        assert opencode_split is not None
        assert qwen_split is not None
        assert gemini_split is not None

        # Read files once outside the loop for efficiency
        opencode_content = opencode_split.read_text()
        qwen_content = qwen_split.read_text()
        gemini_content = gemini_split.read_text()

        # Splitting criteria markers that should be in all templates
        splitting_criteria = [
            ">2 steps",
            ">1 file",
            ">3 conditions",
            ">100 characters",
        ]

        for criterion in splitting_criteria:
            assert criterion in opencode_content, f"OpenCode missing: {criterion}"
            assert criterion in qwen_content, f"Qwen missing: {criterion}"
            assert criterion in gemini_content, f"Gemini missing: {criterion}"

    def test_all_implement_templates_reference_same_mcp_tools(self):
        """All implement templates should reference the same core MCP tools."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_impl = next(
            (t for t in opencode_templates if t.stem == "simpletask.implement"), None
        )
        qwen_impl = next((t for t in qwen_templates if t.stem == "simpletask.implement"), None)
        gemini_impl = next((t for t in gemini_templates if t.stem == "simpletask.implement"), None)

        assert opencode_impl is not None
        assert qwen_impl is not None
        assert gemini_impl is not None

        # Core MCP tools that should be in all implement templates
        core_mcp_tools = [
            "simpletask_get",
            "simpletask_task",
            "simpletask_criteria",
            "simpletask_note",
            "simpletask_quality",
        ]

        # Read files once before the loop
        opencode_content = opencode_impl.read_text()
        qwen_content = qwen_impl.read_text()
        gemini_content = gemini_impl.read_text()

        for tool in core_mcp_tools:
            assert tool in opencode_content, f"OpenCode missing MCP tool: {tool}"
            assert tool in qwen_content, f"Qwen missing MCP tool: {tool}"
            assert tool in gemini_content, f"Gemini missing MCP tool: {tool}"

    def test_no_branch_parameter_in_any_implement_template(self):
        """No implement template should reference branch=None (removed in v0.18.0)."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_impl = next(
            (t for t in opencode_templates if t.stem == "simpletask.implement"), None
        )
        qwen_impl = next((t for t in qwen_templates if t.stem == "simpletask.implement"), None)
        gemini_impl = next((t for t in gemini_templates if t.stem == "simpletask.implement"), None)

        assert opencode_impl is not None
        assert qwen_impl is not None
        assert gemini_impl is not None

        opencode_content = opencode_impl.read_text()
        qwen_content = qwen_impl.read_text()
        gemini_content = gemini_impl.read_text()

        # Should not contain branch=None (removed in v0.18.0)
        assert "branch=None" not in opencode_content, "OpenCode has branch=None"
        assert "branch=None" not in qwen_content, "Qwen has branch=None"
        assert "branch=None" not in gemini_content, "Gemini has branch=None"

    def test_all_split_templates_reference_same_mcp_tools(self):
        """All split templates should reference the same core MCP tools."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_split = next((t for t in opencode_templates if t.stem == "simpletask.split"), None)
        qwen_split = next((t for t in qwen_templates if t.stem == "simpletask.split"), None)
        gemini_split = next((t for t in gemini_templates if t.stem == "simpletask.split"), None)

        assert opencode_split is not None
        assert qwen_split is not None
        assert gemini_split is not None

        # Core MCP tools that should be in all split templates
        core_mcp_tools = [
            "simpletask_get",
            "simpletask_task",
        ]

        opencode_content = opencode_split.read_text()
        qwen_content = qwen_split.read_text()
        gemini_content = gemini_split.read_text()

        for tool in core_mcp_tools:
            assert tool in opencode_content, f"OpenCode missing MCP tool: {tool}"
            assert tool in qwen_content, f"Qwen missing MCP tool: {tool}"
            assert tool in gemini_content, f"Gemini missing MCP tool: {tool}"

    def test_all_review_templates_reference_same_mcp_tools(self):
        """All review templates should reference the same core MCP tools."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_review = next(
            (t for t in opencode_templates if t.stem == "simpletask.review"), None
        )
        qwen_review = next((t for t in qwen_templates if t.stem == "simpletask.review"), None)
        gemini_review = next((t for t in gemini_templates if t.stem == "simpletask.review"), None)

        assert opencode_review is not None
        assert qwen_review is not None
        assert gemini_review is not None

        # Core MCP tools that should be in all review templates
        # Note: Review templates use simpletask_get() for read-only access and
        # simpletask_task() for adding fix tasks to the task file
        core_mcp_tools = [
            "simpletask_get",
            "simpletask_task",
        ]

        opencode_content = opencode_review.read_text()
        qwen_content = qwen_review.read_text()
        gemini_content = gemini_review.read_text()

        for tool in core_mcp_tools:
            assert tool in opencode_content, f"OpenCode missing MCP tool: {tool}"
            assert tool in qwen_content, f"Qwen missing MCP tool: {tool}"
            assert tool in gemini_content, f"Gemini missing MCP tool: {tool}"

    def test_no_branch_parameter_in_any_template(self):
        """All 12 templates should not contain deprecated branch=None.

        The branch parameter is still valid for simpletask_new() but was removed
        from other MCP tools (get, task, criteria, quality, design, etc.) which
        now auto-detect the current git branch.
        """
        import re

        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        # Pattern to match MCP tool calls with branch parameter (excluding simpletask_new)
        # Matches: simpletask_get(branch=...), simpletask_task(action="...", branch=...)
        # But NOT: simpletask_new(branch=...)
        deprecated_branch_pattern = re.compile(
            r"simpletask_(?!new\()"  # Negative lookahead: not followed by "new("
            r"[a-z_]+\([^)]*branch="  # Any simpletask tool with branch= param
        )

        # Check all 4 OpenCode templates
        for template in opencode_templates:
            content = template.read_text()
            assert "branch=None" not in content, f"{template.name} has branch=None"
            match = deprecated_branch_pattern.search(content)
            assert match is None, (
                f"{template.name} has deprecated branch parameter in non-new tool: "
                f"{match.group(0) if match else ''}"
            )

        # Check all 4 Qwen templates
        for template in qwen_templates:
            content = template.read_text()
            assert "branch=None" not in content, f"{template.name} has branch=None"
            match = deprecated_branch_pattern.search(content)
            assert match is None, (
                f"{template.name} has deprecated branch parameter in non-new tool: "
                f"{match.group(0) if match else ''}"
            )

        # Check all 4 Gemini templates
        for template in gemini_templates:
            content = template.read_text()
            assert "branch=None" not in content, f"{template.name} has branch=None"
            match = deprecated_branch_pattern.search(content)
            assert match is None, (
                f"{template.name} has deprecated branch parameter in non-new tool: "
                f"{match.group(0) if match else ''}"
            )

    def test_all_implement_templates_list_all_statuses(self):
        """All implement templates should list all 5 valid statuses (in_progress, completed, blocked, paused, not_started) in their reference sections."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_impl = next(
            (t for t in opencode_templates if t.stem == "simpletask.implement"), None
        )
        qwen_impl = next((t for t in qwen_templates if t.stem == "simpletask.implement"), None)
        gemini_impl = next((t for t in gemini_templates if t.stem == "simpletask.implement"), None)

        assert opencode_impl is not None
        assert qwen_impl is not None
        assert gemini_impl is not None

        # All 5 valid task statuses
        required_statuses = ["in_progress", "completed", "blocked", "paused", "not_started"]

        opencode_content = opencode_impl.read_text()
        qwen_content = qwen_impl.read_text()
        gemini_content = gemini_impl.read_text()

        for status in required_statuses:
            assert status in opencode_content, f"OpenCode implement missing status: {status}"
            assert status in qwen_content, f"Qwen implement missing status: {status}"
            assert status in gemini_content, f"Gemini implement missing status: {status}"

    def test_implement_return_type_descriptions_consistent(self):
        """All implement templates should use consistent SimpleTaskWriteResponse description text."""
        opencode_templates = get_bundled_templates()
        qwen_templates = get_bundled_qwen_templates()
        gemini_templates = get_bundled_gemini_templates()

        opencode_impl = next(
            (t for t in opencode_templates if t.stem == "simpletask.implement"), None
        )
        qwen_impl = next((t for t in qwen_templates if t.stem == "simpletask.implement"), None)
        gemini_impl = next((t for t in gemini_templates if t.stem == "simpletask.implement"), None)

        assert opencode_impl is not None
        assert qwen_impl is not None
        assert gemini_impl is not None

        opencode_content = opencode_impl.read_text()
        qwen_content = qwen_impl.read_text()
        gemini_content = gemini_impl.read_text()

        # All templates should use the same description for SimpleTaskWriteResponse
        expected_description = "Returns SimpleTaskWriteResponse with success confirmation"

        assert (
            expected_description in opencode_content
        ), "OpenCode implement has inconsistent SimpleTaskWriteResponse description"
        assert (
            expected_description in qwen_content
        ), "Qwen implement has inconsistent SimpleTaskWriteResponse description"
        assert (
            expected_description in gemini_content
        ), "Gemini implement has inconsistent SimpleTaskWriteResponse description"

        # Also verify absence of known divergent phrasings
        divergent_description = "Returns SimpleTaskWriteResponse with updated criteria state"

        assert (
            divergent_description not in opencode_content
        ), "OpenCode implement contains divergent description: 'updated criteria state'"
        assert (
            divergent_description not in qwen_content
        ), "Qwen implement contains divergent description: 'updated criteria state'"
        assert (
            divergent_description not in gemini_content
        ), "Gemini implement contains divergent description: 'updated criteria state'"

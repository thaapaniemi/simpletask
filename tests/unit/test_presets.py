"""Unit tests for quality presets in core/presets.py.

Tests cover:
- get_preset() function with valid and invalid preset names
- list_presets() function
- apply_preset() fill-gaps-only strategy
- build_command() helper function
- load_presets_from_file() and load_all_presets() functions
- Preset configurations for: python, typescript, node, go, rust, java-maven, java-gradle
"""

import pytest
from simpletask.core.models import (
    LintingConfig,
    QualityRequirements,
    SecurityCheckConfig,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
)
from simpletask.core.presets import (
    QUALITY_PRESETS,
    apply_preset,
    build_command,
    get_preset,
    list_presets,
    load_all_presets,
    load_presets_from_file,
)


class TestQualityPresets:
    """Test QUALITY_PRESETS dictionary."""

    def test_all_presets_exist(self):
        """All expected presets are defined."""
        expected = ["python", "typescript", "node", "go", "rust", "java-maven", "java-gradle"]
        for preset_name in expected:
            assert preset_name in QUALITY_PRESETS

    def test_python_preset(self):
        """Python preset has correct configuration."""
        preset = QUALITY_PRESETS["python"]
        assert preset.linting.enabled is True
        assert preset.linting.tool == ToolName.RUFF
        assert preset.linting.args == ["check", "."]
        assert preset.type_checking is not None
        assert preset.type_checking.tool == ToolName.MYPY
        assert preset.testing.enabled is True
        assert preset.testing.tool == ToolName.PYTEST
        assert preset.testing.min_coverage == 80
        assert preset.security_check.enabled is False

    def test_typescript_preset(self):
        """TypeScript preset has correct configuration."""
        preset = QUALITY_PRESETS["typescript"]
        assert preset.linting.tool == ToolName.ESLINT
        assert preset.type_checking is not None
        assert preset.type_checking.tool == ToolName.TSC
        assert preset.testing.tool == ToolName.NPM
        assert preset.testing.args == ["test"]

    def test_node_preset(self):
        """Node preset has correct configuration."""
        preset = QUALITY_PRESETS["node"]
        assert preset.linting.tool == ToolName.ESLINT
        assert preset.type_checking is None  # No type checking for plain Node
        assert preset.testing.tool == ToolName.NPM
        assert preset.security_check.enabled is True
        assert preset.security_check.tool == ToolName.NPM
        assert preset.security_check.args == ["audit"]

    def test_go_preset(self):
        """Go preset has correct configuration."""
        preset = QUALITY_PRESETS["go"]
        assert preset.linting.tool == ToolName.GOLANGCI_LINT
        assert preset.type_checking is None  # Built-in at compile time
        assert preset.testing.tool == ToolName.GO
        assert preset.security_check.enabled is True
        assert preset.security_check.tool == ToolName.GOSEC

    def test_rust_preset(self):
        """Rust preset has correct configuration."""
        preset = QUALITY_PRESETS["rust"]
        assert preset.linting.tool == ToolName.CARGO
        assert "clippy" in preset.linting.args
        assert preset.type_checking is None  # Built-in at compile time
        assert preset.testing.tool == ToolName.CARGO
        assert preset.security_check.enabled is True
        assert preset.security_check.tool == ToolName.CARGO

    def test_java_maven_preset(self):
        """Java Maven preset has correct configuration."""
        preset = QUALITY_PRESETS["java-maven"]
        assert preset.linting.tool == ToolName.MVN
        assert "checkstyle:check" in preset.linting.args
        assert preset.type_checking is None  # Built-in at compile time
        assert preset.testing.tool == ToolName.MVN
        assert preset.security_check.enabled is True

    def test_java_gradle_preset(self):
        """Java Gradle preset has correct configuration."""
        preset = QUALITY_PRESETS["java-gradle"]
        assert preset.linting.tool == ToolName.GRADLE
        assert preset.testing.tool == ToolName.GRADLE
        assert preset.security_check.enabled is True


class TestGetPreset:
    """Test get_preset() function."""

    def test_get_valid_preset(self):
        """Getting a valid preset returns QualityRequirements."""
        preset = get_preset("python")
        assert isinstance(preset, QualityRequirements)
        assert preset.linting.tool == ToolName.RUFF

    def test_get_invalid_preset(self):
        """Getting an invalid preset raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_preset("nonexistent")
        error_msg = str(exc_info.value).lower()
        assert "unknown preset" in error_msg
        assert "nonexistent" in error_msg
        assert "available presets" in error_msg

    def test_get_preset_case_sensitive(self):
        """Preset names are case-sensitive."""
        with pytest.raises(ValueError):
            get_preset("Python")  # Should be "python"


class TestListPresets:
    """Test list_presets() function."""

    def test_list_presets_returns_all(self):
        """list_presets() returns all preset names."""
        presets = list_presets()
        assert isinstance(presets, list)
        assert len(presets) >= 7  # At least the 7 we defined
        assert "python" in presets
        assert "typescript" in presets
        assert "java-maven" in presets

    def test_list_presets_sorted(self):
        """list_presets() returns sorted list."""
        presets = list_presets()
        assert presets == sorted(presets)


class TestApplyPreset:
    """Test apply_preset() function with fill-gaps-only strategy."""

    def test_apply_to_none(self):
        """Applying preset to None uses preset directly."""
        merged, applied = apply_preset(None, "python")
        assert merged.linting.tool == ToolName.RUFF
        assert merged.type_checking is not None
        assert merged.type_checking.tool == ToolName.MYPY
        assert merged.testing.tool == ToolName.PYTEST
        assert applied["linting"] is True
        assert applied["type_checking"] is True
        assert applied["testing"] is True
        assert applied["security_check"] is True

    def test_apply_fills_gaps_only(self):
        """Applying preset fills only missing fields."""
        # Existing config with type_checking missing
        existing = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.PYLINT, args=["."]),
            type_checking=None,  # Missing
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            security_check=SecurityCheckConfig(enabled=False),
        )

        merged, applied = apply_preset(existing, "python")

        # Linting should NOT be replaced (user's PYLINT preserved)
        assert merged.linting.tool == ToolName.PYLINT
        assert applied["linting"] is False

        # Type checking should be filled from preset (MYPY)
        assert merged.type_checking is not None
        assert merged.type_checking.tool == ToolName.MYPY
        assert applied["type_checking"] is True

        # Testing should NOT be replaced (user's config preserved)
        assert merged.testing.tool == ToolName.PYTEST
        assert applied["testing"] is False

        # Security check should NOT be replaced (user's config preserved)
        assert applied["security_check"] is False

    def test_apply_preserves_existing_config(self):
        """Applying preset preserves all existing non-None configs."""
        existing = QualityRequirements(
            linting=LintingConfig(enabled=False, tool=ToolName.RUFF, args=["check", "src/"]),
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["src/"]),
            testing=TestingConfig(
                enabled=True, tool=ToolName.PYTEST, args=["tests/"], min_coverage=90
            ),
            security_check=SecurityCheckConfig(
                enabled=True, tool=ToolName.BANDIT, args=["-r", "."]
            ),
        )

        merged, applied = apply_preset(existing, "python")

        # All fields should be preserved
        assert merged.linting.tool == ToolName.RUFF
        assert merged.linting.args == ["check", "src/"]
        assert merged.type_checking.args == ["src/"]
        assert merged.testing.min_coverage == 90
        assert merged.security_check.tool == ToolName.BANDIT
        assert applied["linting"] is False
        assert applied["type_checking"] is False
        assert applied["testing"] is False
        assert applied["security_check"] is False

    def test_apply_fills_only_type_checking(self):
        """Applying preset fills only type_checking when it's None."""
        existing = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=None,
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            security_check=SecurityCheckConfig(enabled=False),
        )

        merged, applied = apply_preset(existing, "python")

        assert merged.type_checking is not None
        assert merged.type_checking.tool == ToolName.MYPY
        assert applied["type_checking"] is True
        assert applied["linting"] is False
        assert applied["testing"] is False
        assert applied["security_check"] is False

    def test_apply_fills_only_security_check(self):
        """Applying preset fills only security_check when it's None."""
        existing = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            security_check=None,
        )

        merged, applied = apply_preset(existing, "python")

        # Python preset has security_check disabled, so it should be applied
        assert merged.security_check is not None
        assert merged.security_check.enabled is False
        assert applied["security_check"] is True

    def test_apply_invalid_preset(self):
        """Applying invalid preset raises ValueError."""
        existing = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
        )

        with pytest.raises(ValueError) as exc_info:
            apply_preset(existing, "invalid-preset")
        assert "unknown preset" in str(exc_info.value).lower()


class TestBuildCommand:
    """Test build_command() helper function."""

    def test_build_command_with_args(self):
        """build_command() builds correct command list with args."""
        cmd = build_command(ToolName.RUFF, ["check", "."])
        assert cmd == ["ruff", "check", "."]

    def test_build_command_no_args(self):
        """build_command() builds correct command list without args."""
        cmd = build_command(ToolName.MYPY, [])
        assert cmd == ["mypy"]

    def test_build_command_multiple_args(self):
        """build_command() builds correct command list with multiple args."""
        cmd = build_command(ToolName.PYTEST, ["--cov", "--cov-report=term"])
        assert cmd == ["pytest", "--cov", "--cov-report=term"]

    def test_build_command_preserves_order(self):
        """build_command() preserves argument order."""
        cmd = build_command(ToolName.ESLINT, [".", "--ext", ".ts,.tsx", "--fix"])
        assert cmd == ["eslint", ".", "--ext", ".ts,.tsx", "--fix"]


class TestLoadPresetsFromFile:
    """Test load_presets_from_file() function."""

    def test_load_valid_yaml(self, tmp_path):
        """Load valid YAML preset file."""
        preset_file = tmp_path / "presets.yaml"
        preset_file.write_text("""
custom-python:
  linting:
    enabled: true
    tool: ruff
    args: ["check", "src/"]
  type_checking:
    enabled: true
    tool: mypy
    args: ["src/"]
  testing:
    enabled: true
    tool: pytest
    args: ["tests/"]
    min_coverage: 90
  security_check:
    enabled: false
    tool: null
    args: []
""")

        presets = load_presets_from_file(preset_file)

        assert "custom-python" in presets
        preset = presets["custom-python"]
        assert preset.linting.enabled is True
        assert preset.linting.tool == ToolName.RUFF
        assert preset.linting.args == ["check", "src/"]
        assert preset.testing.min_coverage == 90

    def test_load_file_not_found(self, tmp_path):
        """Loading non-existent file raises FileNotFoundError."""
        preset_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_presets_from_file(preset_file)

    def test_load_invalid_yaml(self, tmp_path):
        """Loading invalid YAML raises ValueError."""
        preset_file = tmp_path / "presets.yaml"
        preset_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError) as exc_info:
            load_presets_from_file(preset_file)
        assert "failed to parse yaml" in str(exc_info.value).lower()

    def test_load_non_dict_yaml(self, tmp_path):
        """Loading non-dict YAML raises ValueError."""
        preset_file = tmp_path / "presets.yaml"
        preset_file.write_text("- item1\n- item2\n")

        with pytest.raises(TypeError) as exc_info:
            load_presets_from_file(preset_file)
        assert "must contain a yaml dictionary" in str(exc_info.value).lower()

    def test_load_invalid_preset_config(self, tmp_path):
        """Loading preset with invalid config raises ValueError."""
        preset_file = tmp_path / "presets.yaml"
        preset_file.write_text("""
bad-preset:
  linting:
    enabled: true
    tool: invalid_tool
    args: ["check"]
""")

        with pytest.raises(ValueError) as exc_info:
            load_presets_from_file(preset_file)
        assert "invalid preset 'bad-preset'" in str(exc_info.value).lower()

    def test_load_multiple_presets(self, tmp_path):
        """Load file with multiple presets."""
        preset_file = tmp_path / "presets.yaml"
        preset_file.write_text("""
preset1:
  linting:
    enabled: true
    tool: ruff
    args: []
  testing:
    enabled: true
    tool: pytest
    args: []
    min_coverage: 80
preset2:
  linting:
    enabled: true
    tool: eslint
    args: ["."]
  testing:
    enabled: true
    tool: npm
    args: ["test"]
    min_coverage: 75
""")

        presets = load_presets_from_file(preset_file)

        assert len(presets) == 2
        assert "preset1" in presets
        assert "preset2" in presets
        assert presets["preset1"].linting.tool == ToolName.RUFF
        assert presets["preset2"].linting.tool == ToolName.ESLINT


class TestLoadAllPresets:
    """Test load_all_presets() function."""

    def test_load_all_returns_builtin_presets(self):
        """load_all_presets() returns at least built-in presets."""
        all_presets = load_all_presets()

        # Should contain all built-in presets
        for name in QUALITY_PRESETS:
            assert name in all_presets

    def test_custom_presets_override_builtin(self, tmp_path, monkeypatch):
        """Custom presets override built-in presets with same name."""
        # Create custom preset file that overrides 'python' preset
        preset_file = tmp_path / ".simpletask" / "presets.yaml"
        preset_file.parent.mkdir(parents=True)
        preset_file.write_text("""
python:
  linting:
    enabled: true
    tool: ruff
    args: ["check", "custom/"]
  testing:
    enabled: true
    tool: pytest
    args: ["custom_tests/"]
    min_coverage: 95
""")

        # Mock the preset search paths to include our test file
        def mock_search_paths():
            return [preset_file]

        monkeypatch.setattr("simpletask.core.presets.get_preset_search_paths", mock_search_paths)

        all_presets = load_all_presets()

        # Custom 'python' preset should override built-in
        assert "python" in all_presets
        assert all_presets["python"].linting.args == ["check", "custom/"]
        assert all_presets["python"].testing.min_coverage == 95

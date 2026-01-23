"""Unit tests for quality and design Pydantic models in core/models.py.

Tests cover:
- ToolName enum validation
- LintingConfig, TypeCheckConfig, TestingConfig, SecurityCheckConfig validation
- Shell metacharacter rejection in args
- QualityRequirements model validation
- Design and DesignReference model validation
- SimpleTaskSpec with quality_requirements and design fields
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from simpletask.core.models import (
    AcceptanceCriterion,
    ArchitecturalPattern,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    LintingConfig,
    QualityRequirements,
    SecurityCategory,
    SecurityCheckConfig,
    SecurityRequirement,
    SimpleTaskSpec,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
)


class TestToolName:
    """Test ToolName enum."""

    def test_enum_values(self):
        """ToolName enum has correct values for common tools."""
        assert ToolName.RUFF.value == "ruff"
        assert ToolName.MYPY.value == "mypy"
        assert ToolName.PYTEST.value == "pytest"
        assert ToolName.ESLINT.value == "eslint"
        assert ToolName.TSC.value == "tsc"
        assert ToolName.GO.value == "go"
        assert ToolName.CARGO.value == "cargo"
        assert ToolName.MVN.value == "mvn"
        assert ToolName.GRADLE.value == "gradle"


class TestLintingConfig:
    """Test LintingConfig model."""

    def test_valid_config(self):
        """Valid linting config validates correctly."""
        config = LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."])
        assert config.enabled is True
        assert config.tool == ToolName.RUFF
        assert config.args == ["check", "."]

    def test_empty_args(self):
        """Empty args list is valid."""
        config = LintingConfig(enabled=True, tool=ToolName.RUFF, args=[])
        assert config.args == []

    def test_shell_metacharacters_rejected(self):
        """Dangerous shell metacharacters are rejected."""
        # Only these are actually dangerous and should be rejected
        dangerous_chars = [";", "&", "|", "`", "$", ">", "<"]
        for char in dangerous_chars:
            with pytest.raises(ValidationError) as exc_info:
                LintingConfig(enabled=True, tool=ToolName.RUFF, args=[f"check{char}"])
            assert "shell metacharacters" in str(exc_info.value).lower()

    def test_legitimate_special_chars_allowed(self):
        """Legitimate special chars like parentheses are allowed."""
        # These are legitimate in many tool arguments (e.g., pytest -k "(test_a or test_b)")
        # and should NOT be rejected
        legitimate_chars = ["(", ")", "{", "}", "[", "]", "*", "?"]
        for char in legitimate_chars:
            # Should not raise ValidationError
            config = LintingConfig(enabled=True, tool=ToolName.RUFF, args=[f"check{char}"])
            assert config.args == [f"check{char}"]

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            LintingConfig(tool=ToolName.RUFF, args=["check"])  # Missing enabled

        with pytest.raises(ValidationError):
            LintingConfig(enabled=True, args=["check"])  # Missing tool

    def test_extra_fields_forbidden(self):
        """Extra fields are rejected due to extra='forbid'."""
        with pytest.raises(ValidationError):
            LintingConfig(enabled=True, tool=ToolName.RUFF, args=[], extra_field="invalid")


class TestTypeCheckConfig:
    """Test TypeCheckConfig model."""

    def test_valid_config(self):
        """Valid type check config validates correctly."""
        config = TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"])
        assert config.enabled is True
        assert config.tool == ToolName.MYPY
        assert config.args == ["cli/"]

    def test_shell_metacharacters_rejected(self):
        """Args containing shell metacharacters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/", "&&", "echo"])
        assert "shell metacharacters" in str(exc_info.value).lower()


class TestTestingConfig:
    """Test TestingConfig model."""

    def test_valid_config_with_coverage(self):
        """Valid test config with coverage validates correctly."""
        config = TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80)
        assert config.enabled is True
        assert config.tool == ToolName.PYTEST
        assert config.min_coverage == 80

    def test_valid_config_without_coverage(self):
        """Valid test config without coverage validates correctly."""
        config = TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[])
        assert config.min_coverage is None

    def test_coverage_range_validation(self):
        """Coverage must be between 0 and 100."""
        # Valid range
        TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=0)
        TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=100)

        # Invalid range
        with pytest.raises(ValidationError):
            TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=-1)

        with pytest.raises(ValidationError):
            TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=101)

    def test_shell_metacharacters_rejected(self):
        """Args containing shell metacharacters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TestingConfig(enabled=True, tool=ToolName.PYTEST, args=["--cov", "|", "grep"])
        assert "shell metacharacters" in str(exc_info.value).lower()


class TestSecurityCheckConfig:
    """Test SecurityCheckConfig model."""

    def test_valid_config_enabled(self):
        """Valid enabled security config validates correctly."""
        config = SecurityCheckConfig(enabled=True, tool=ToolName.BANDIT, args=["-r", "."])
        assert config.enabled is True
        assert config.tool == ToolName.BANDIT
        assert config.args == ["-r", "."]

    def test_valid_config_disabled(self):
        """Valid disabled security config validates correctly."""
        config = SecurityCheckConfig(enabled=False, tool=None, args=[])
        assert config.enabled is False
        assert config.tool is None
        assert config.args == []

    def test_default_values(self):
        """Default values are set correctly."""
        config = SecurityCheckConfig()
        assert config.enabled is False
        assert config.tool is None
        assert config.args == []

    def test_shell_metacharacters_rejected(self):
        """Args containing shell metacharacters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityCheckConfig(enabled=True, tool=ToolName.BANDIT, args=["-r", ";", "rm"])
        assert "shell metacharacters" in str(exc_info.value).lower()


class TestQualityRequirements:
    """Test QualityRequirements model."""

    def test_valid_full_config(self):
        """Valid complete quality requirements validates correctly."""
        qr = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
            security_check=SecurityCheckConfig(
                enabled=True, tool=ToolName.BANDIT, args=["-r", "."]
            ),
        )
        assert qr.linting.enabled is True
        assert qr.type_checking.enabled is True
        assert qr.testing.enabled is True
        assert qr.security_check.enabled is True

    def test_valid_minimal_config(self):
        """Valid minimal quality requirements validates correctly."""
        qr = QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=None,
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            security_check=None,
        )
        assert qr.linting is not None
        assert qr.type_checking is None
        assert qr.testing is not None
        assert qr.security_check is None

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        # Missing linting
        with pytest.raises(ValidationError):
            QualityRequirements(
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            )

        # Missing testing
        with pytest.raises(ValidationError):
            QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            )

    def test_extra_fields_forbidden(self):
        """Extra fields are rejected due to extra='forbid'."""
        with pytest.raises(ValidationError):
            QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
                extra_field="invalid",
            )


class TestDesignReference:
    """Test DesignReference model."""

    def test_valid_reference(self):
        """Valid design reference validates correctly."""
        ref = DesignReference(
            path="cli/simpletask/core/models.py",
            reason="Follow existing Pydantic model patterns",
        )
        assert ref.path == "cli/simpletask/core/models.py"
        assert ref.reason == "Follow existing Pydantic model patterns"

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            DesignReference(path="file.py")  # Missing reason

        with pytest.raises(ValidationError):
            DesignReference(reason="Some reason")  # Missing path

    def test_extra_fields_forbidden(self):
        """Extra fields are rejected due to extra='forbid'."""
        with pytest.raises(ValidationError):
            DesignReference(path="file.py", reason="reason", extra_field="invalid")

    def test_path_traversal_rejected(self):
        """Path containing '..' is rejected to prevent path traversal attacks."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="../../../etc/passwd", reason="test")
        assert ".." in str(exc_info.value)
        assert "path traversal" in str(exc_info.value).lower()

    def test_path_traversal_in_middle_rejected(self):
        """Path with '..' in the middle is also rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="cli/../../../etc/passwd", reason="test")
        assert ".." in str(exc_info.value)

    def test_sensitive_env_file_rejected(self):
        """Paths containing .env are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path=".env", reason="test")
        assert ".env" in str(exc_info.value).lower()

    def test_sensitive_key_file_rejected(self):
        """Paths containing .key are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="config/secrets.key", reason="test")
        assert ".key" in str(exc_info.value).lower()

    def test_sensitive_credentials_file_rejected(self):
        """Paths containing 'credentials' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="config/credentials.json", reason="test")
        assert "credentials" in str(exc_info.value).lower()

    def test_sensitive_secrets_file_rejected(self):
        """Paths containing 'secrets' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="config/secrets.yaml", reason="test")
        assert "secrets" in str(exc_info.value).lower()

    def test_sensitive_password_file_rejected(self):
        """Paths containing 'password' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="config/password.txt", reason="test")
        assert "password" in str(exc_info.value).lower()

    def test_sensitive_pem_file_rejected(self):
        """Paths containing .pem are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="certs/private.pem", reason="test")
        assert ".pem" in str(exc_info.value).lower()

    def test_sensitive_crt_file_rejected(self):
        """Paths containing .crt are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="certs/certificate.crt", reason="test")
        assert ".crt" in str(exc_info.value).lower()

    def test_absolute_path_unix_rejected(self):
        """Absolute Unix paths (starting with /) are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="/etc/passwd", reason="test")
        assert "absolute" in str(exc_info.value).lower()

    def test_absolute_path_windows_rejected(self):
        r"""Absolute Windows paths (C:\ style) are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignReference(path="C:\\Windows\\System32\\config.sys", reason="test")
        assert "absolute" in str(exc_info.value).lower()

    def test_windows_path_normalized(self):
        """Windows backslashes should work but are normalized."""
        # This should succeed because backslashes are normalized to forward slashes
        ref = DesignReference(path="src\\module\\file.py", reason="test")
        # The path should be stored as-is (validation normalizes internally but doesn't modify)
        assert ref.path == "src\\module\\file.py"

    def test_case_insensitive_sensitive_pattern_detection(self):
        """Sensitive patterns are detected case-insensitively."""
        with pytest.raises(ValidationError):
            DesignReference(path="CONFIG/.ENV", reason="test")
        with pytest.raises(ValidationError):
            DesignReference(path="config/CREDENTIALS.json", reason="test")
        with pytest.raises(ValidationError):
            DesignReference(path="config/Secrets.yaml", reason="test")

    def test_legitimate_paths_allowed(self):
        """Legitimate source code paths are allowed."""
        valid_paths = [
            "src/module/file.py",
            "cli/simpletask/core/models.py",
            "tests/unit/test_models.py",
            "docs/api/reference.md",
            "config/settings.py",  # 'config' directory is OK
            "lib/auth/token_manager.py",  # auth code is OK
            "cli/simpletask/utils/validators.py",  # utility code
        ]
        for path in valid_paths:
            ref = DesignReference(path=path, reason="test")
            assert ref.path == path


class TestDesign:
    """Test Design model."""

    def test_valid_complete_design(self):
        """Valid complete design validates correctly."""
        design = Design(
            patterns=[ArchitecturalPattern.REPOSITORY, ArchitecturalPattern.FACTORY],
            reference_implementations=[
                DesignReference(path="cli/simpletask/core/models.py", reason="Model pattern")
            ],
            architectural_constraints=["Must be stateless", "No global state"],
            security=[
                SecurityRequirement(
                    category=SecurityCategory.INPUT_VALIDATION, description="Validate all inputs"
                ),
                SecurityRequirement(
                    category=SecurityCategory.DATA_PROTECTION, description="No shell injection"
                ),
            ],
            error_handling=ErrorHandlingStrategy.EXCEPTIONS,
        )
        assert len(design.patterns) == 2
        assert len(design.reference_implementations) == 1
        assert len(design.architectural_constraints) == 2
        assert len(design.security) == 2
        assert design.error_handling == ErrorHandlingStrategy.EXCEPTIONS

    def test_valid_minimal_design(self):
        """Valid minimal design with all None validates correctly."""
        design = Design(
            patterns=None,
            reference_implementations=None,
            architectural_constraints=None,
            security=None,
            error_handling=None,
        )
        assert design.patterns is None
        assert design.reference_implementations is None
        assert design.architectural_constraints is None
        assert design.security is None
        assert design.error_handling is None

    def test_empty_lists_allowed(self):
        """Empty lists are allowed for most list fields (except architectural_constraints)."""
        design = Design(
            patterns=[],
            reference_implementations=[],
            architectural_constraints=None,  # Must have at least 1 item or be None
            security=[],
            error_handling=None,
        )
        assert design.patterns == []
        assert design.architectural_constraints is None

    def test_extra_fields_forbidden(self):
        """Extra fields are rejected due to extra='forbid'."""
        with pytest.raises(ValidationError):
            Design(patterns_to_follow=["Pattern"], extra_field="invalid")


class TestSimpleTaskSpecWithQualityAndDesign:
    """Test SimpleTaskSpec with quality_requirements and design fields."""

    def test_spec_with_quality_requirements(self):
        """Spec with quality_requirements validates correctly."""
        spec = SimpleTaskSpec(
            schema_version="1.3",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works correctly")],
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
                security_check=None,
            ),
        )
        assert spec.quality_requirements is not None
        assert spec.quality_requirements.linting.tool == ToolName.RUFF
        assert spec.quality_requirements.testing.min_coverage == 80

    def test_spec_with_design(self):
        """Spec with design field validates correctly."""
        spec = SimpleTaskSpec(
            schema_version="1.3",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works correctly")],
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            ),
            design=Design(
                patterns=[ArchitecturalPattern.REPOSITORY],
                architectural_constraints=["Must be stateless"],
            ),
        )
        assert spec.design is not None
        assert spec.design.patterns == [ArchitecturalPattern.REPOSITORY]
        assert spec.design.architectural_constraints == ["Must be stateless"]

    def test_spec_with_quality_and_design(self):
        """Spec with both quality and design validates correctly."""
        spec = SimpleTaskSpec(
            schema_version="1.3",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works correctly")],
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            ),
            design=Design(patterns=[ArchitecturalPattern.REPOSITORY]),
        )
        assert spec.quality_requirements is not None
        assert spec.design is not None

    def test_spec_without_design(self):
        """Spec without design field validates correctly (design is optional)."""
        spec = SimpleTaskSpec(
            schema_version="1.3",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works correctly")],
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
            ),
        )
        assert spec.design is None

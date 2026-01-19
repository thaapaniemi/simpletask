"""Tests for branch name normalization."""

import pytest

from simpletask.core.project import normalize_branch_name


class TestNormalizeBranchName:
    """Tests for normalize_branch_name function."""

    def test_simple_name_unchanged(self):
        """Test that simple lowercase names pass through."""
        assert normalize_branch_name("main") == "main"
        assert normalize_branch_name("feature") == "feature"

    def test_forward_slash_to_dash(self):
        """Test forward slash conversion."""
        assert normalize_branch_name("feature/auth") == "feature-auth"
        assert normalize_branch_name("bugfix/api-timeout") == "bugfix-api-timeout"

    def test_backslash_to_dash(self):
        """Test backslash conversion."""
        assert normalize_branch_name("feature\\auth") == "feature-auth"

    def test_multiple_slashes_collapsed(self):
        """Test multiple slashes collapse to single dash."""
        assert normalize_branch_name("test///multiple//slashes") == "test-multiple-slashes"

    def test_uppercase_to_lowercase(self):
        """Test case conversion."""
        assert normalize_branch_name("Feature/Auth") == "feature-auth"
        assert normalize_branch_name("URGENT-FIX") == "urgent-fix"

    def test_special_characters_replaced(self):
        """Test special character replacement."""
        assert normalize_branch_name("feat: add feature") == "feat-add-feature"
        assert normalize_branch_name('fix "bug" in <module>') == "fix-bug-in-module"
        assert normalize_branch_name("test*?file") == "test-file"
        assert normalize_branch_name("path|separator") == "path-separator"

    def test_whitespace_to_dash(self):
        """Test whitespace conversion."""
        assert normalize_branch_name("my task") == "my-task"
        assert normalize_branch_name("test  spaces") == "test-spaces"
        assert normalize_branch_name("tab\ttab") == "tab-tab"

    def test_double_dot_to_double_dash(self):
        """Test parent traversal security."""
        assert normalize_branch_name("test..file") == "test--file"
        assert normalize_branch_name("../../../etc/passwd") == "etc-passwd"

    def test_unicode_to_ascii(self):
        """Test unicode normalization."""
        assert normalize_branch_name("café") == "cafe"
        assert normalize_branch_name("über-cool") == "uber-cool"
        assert normalize_branch_name("naïve") == "naive"

    def test_leading_trailing_dashes_trimmed(self):
        """Test dash trimming."""
        assert normalize_branch_name("-test-") == "test"
        assert normalize_branch_name("---feature---") == "feature"

    def test_leading_trailing_whitespace(self):
        """Test whitespace trimming."""
        assert normalize_branch_name("  test  ") == "test"

    def test_max_length_truncation(self):
        """Test length limiting."""
        long_name = "a" * 250
        result = normalize_branch_name(long_name)
        assert len(result) == 200

    def test_max_length_custom(self):
        """Test custom max length."""
        long_name = "a" * 150
        result = normalize_branch_name(long_name, max_length=100)
        assert len(result) == 100

    def test_max_length_with_trailing_dash(self):
        """Test that trailing dash is removed after truncation."""
        # Create a string that would end in dash after truncation
        long_name = "a" * 199 + "-" + "b" * 50
        result = normalize_branch_name(long_name, max_length=200)
        # Length might be less than max_length after trimming trailing dash
        assert len(result) <= 200
        assert not result.endswith("-")

    def test_empty_after_normalization_raises(self):
        """Test that names normalizing to empty raise error."""
        with pytest.raises(ValueError, match="normalizes to empty string"):
            normalize_branch_name("///")

        with pytest.raises(ValueError, match="normalizes to empty string"):
            normalize_branch_name("---")

        with pytest.raises(ValueError, match="normalizes to empty string"):
            normalize_branch_name("   ")

        with pytest.raises(ValueError, match="normalizes to empty string"):
            normalize_branch_name(":::")

        # These should NOT raise (they produce valid filenames)
        assert normalize_branch_name("...") == "."  # Triple dot becomes single dot
        assert normalize_branch_name("a") == "a"

    def test_real_world_examples(self):
        """Test real-world branch naming patterns."""
        cases = [
            ("refactor/dry-violations-cleanup", "refactor-dry-violations-cleanup"),
            ("feature/user-authentication", "feature-user-authentication"),
            ("bugfix/login-oauth-issue", "bugfix-login-oauth-issue"),
            ("hotfix/security-CVE-2024", "hotfix-security-cve-2024"),
            ("chore/update-dependencies", "chore-update-dependencies"),
        ]

        for input_name, expected in cases:
            assert normalize_branch_name(input_name) == expected

    def test_github_flow_patterns(self):
        """Test common GitHub flow branch naming patterns."""
        assert normalize_branch_name("feature/PROJ-123-add-login") == "feature-proj-123-add-login"
        assert normalize_branch_name("fix/bug-in-parser") == "fix-bug-in-parser"
        assert normalize_branch_name("docs/update-readme") == "docs-update-readme"

    def test_git_flow_patterns(self):
        """Test common Git flow branch naming patterns."""
        assert normalize_branch_name("release/1.2.0") == "release-1.2.0"
        assert normalize_branch_name("hotfix/1.2.1") == "hotfix-1.2.1"
        assert normalize_branch_name("develop") == "develop"

    def test_jira_style_patterns(self):
        """Test JIRA-style branch names."""
        assert normalize_branch_name("PROJ-123/add-feature") == "proj-123-add-feature"
        assert normalize_branch_name("BUG-456/fix-login") == "bug-456-fix-login"

    def test_mixed_special_characters(self):
        """Test combinations of special characters."""
        assert normalize_branch_name("feat(api): add endpoint") == "feat-api-add-endpoint"
        assert normalize_branch_name("fix[parser]<urgent>") == "fix-parser-urgent"

    def test_consecutive_special_chars(self):
        """Test multiple consecutive special characters collapse."""
        assert normalize_branch_name("test///***???") == "test"
        assert normalize_branch_name("feature::api//v2") == "feature-api-v2"

    def test_dots_preserved_except_double(self):
        """Test that single dots are preserved but double dots become double dash."""
        assert normalize_branch_name("v1.2.3") == "v1.2.3"
        assert normalize_branch_name("file.name") == "file.name"
        assert normalize_branch_name("test..danger") == "test--danger"

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        assert normalize_branch_name("feature-123") == "feature-123"
        assert normalize_branch_name("2024-01-19-update") == "2024-01-19-update"

    def test_underscores_preserved(self):
        """Test that underscores are preserved."""
        assert normalize_branch_name("feature_with_underscores") == "feature_with_underscores"
        assert normalize_branch_name("test_api_v2") == "test_api_v2"

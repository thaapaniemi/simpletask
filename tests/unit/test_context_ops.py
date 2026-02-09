"""Unit tests for context_ops module.

Tests cover:
- set_context() - Set context key-value pairs
- remove_context() - Remove context entries by key or all
- show_context() - Show all context entries
"""

import pytest
from simpletask.core.context_ops import remove_context, set_context, show_context
from simpletask.core.yaml_parser import parse_task_file


class TestSetContext:
    """Test set_context function."""

    def test_set_context_to_empty(self, tmp_task_file):
        """Set context when context field is None."""
        spec = parse_task_file(tmp_task_file)
        spec.context = None  # Ensure empty for this test

        spec = set_context(spec, key="framework", value="django")
        assert spec.context == {"framework": "django"}

    def test_set_context_to_existing(self, tmp_task_file):
        """Set context to existing context dict."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"existing": "value"}

        spec = set_context(spec, key="framework", value="django")
        assert spec.context == {"existing": "value", "framework": "django"}

    def test_set_context_update_existing_key(self, tmp_task_file):
        """Update existing context key."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"framework": "flask"}

        spec = set_context(spec, key="framework", value="django")
        assert spec.context == {"framework": "django"}

    def test_set_multiple_context_keys(self, tmp_task_file):
        """Set multiple context keys sequentially."""
        spec = parse_task_file(tmp_task_file)
        spec.context = None  # Ensure empty for this test

        spec = set_context(spec, key="framework", value="django")
        spec = set_context(spec, key="database", value="postgresql")
        spec = set_context(spec, key="cache", value="redis")

        assert spec.context == {
            "framework": "django",
            "database": "postgresql",
            "cache": "redis",
        }


class TestRemoveContext:
    """Test remove_context function."""

    def test_remove_context_by_key(self, tmp_task_file):
        """Remove context entry by key."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"framework": "django", "database": "postgresql", "cache": "redis"}

        spec = remove_context(spec, key="database")
        assert spec.context == {"framework": "django", "cache": "redis"}

    def test_remove_context_all(self, tmp_task_file):
        """Remove all context entries."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"framework": "django", "database": "postgresql"}

        spec = remove_context(spec, all=True)
        assert spec.context is None

    def test_remove_context_last_one(self, tmp_task_file):
        """Set context to None when removing last key."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"only_key": "value"}

        spec = remove_context(spec, key="only_key")
        assert spec.context is None

    def test_remove_context_invalid_key(self, tmp_task_file):
        """Raise error for invalid key."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"framework": "django"}

        with pytest.raises(ValueError, match="Context key 'invalid' not found"):
            remove_context(spec, key="invalid")

    def test_remove_context_none_dict(self, tmp_task_file):
        """Raise error when context is None."""
        spec = parse_task_file(tmp_task_file)
        spec.context = None

        with pytest.raises(ValueError, match=r"Context key 'key' not found.*No context exists"):
            remove_context(spec, key="key")

    def test_remove_context_requires_key_or_all(self, tmp_task_file):
        """Raise error when neither key nor all is provided."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"framework": "django"}

        with pytest.raises(ValueError, match="Must provide either key or all=True"):
            remove_context(spec)


class TestShowContext:
    """Test show_context function."""

    def test_show_context_empty(self, tmp_task_file):
        """Show context when None."""
        spec = parse_task_file(tmp_task_file)
        spec.context = None

        context = show_context(spec)
        assert context is None

    def test_show_context_with_entries(self, tmp_task_file):
        """Show context with existing entries."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {
            "framework": "django",
            "database": "postgresql",
            "cache": "redis",
        }

        context = show_context(spec)
        assert context == {
            "framework": "django",
            "database": "postgresql",
            "cache": "redis",
        }

    def test_show_context_single(self, tmp_task_file):
        """Show single context entry."""
        spec = parse_task_file(tmp_task_file)
        spec.context = {"only_key": "value"}

        context = show_context(spec)
        assert context == {"only_key": "value"}
